#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012
#    All rights reserved
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston,
#    MA 02111-1307  USA
#
"""
Plot module data about usage from the BOINC stats
"""
import glob
import os
import gzip
import xml.etree.ElementTree as ET
import logging
import math
import numpy
import time

from datetime import date
from matplotlib import pyplot
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import LogNorm
from matplotlib.dates import date2num, num2date
from mpl_toolkits.axes_grid1 import make_axes_locatable
from sqlalchemy import create_engine, select
from plots.database_plot import PLOT_METADATA, USAGE, INDIVIDUAL, HDF5_SIZE
from utils.name_builder import get_archive_bucket, get_files_bucket
from utils.s3_helper import S3Helper


LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

COBBLESTONE_FACTOR = 150.0
BINS_INDIVIDUAL = 8
START_BIN_INDIVIDUAL = 0.001
BINS_FILE_SIZE = 7

# If the database doesn't exist create it
PLOT_DB = '/tmp/pogs/plot.db'
SQLITE_DB = 'sqlite:///%s' % PLOT_DB

sqlite = create_engine(SQLITE_DB)
connection = sqlite.connect()
PLOT_METADATA.create_all(sqlite)


def get_done_dates():
    """
    Are there stats record in the data base?

    :param date:
    :return:
    """
    done_dates = set()
    for entry in connection.execute(select([USAGE])):
        done_dates.add(entry[USAGE.c.date])
    return done_dates


def get_data(output_directory):
    """
    Get the stats from the S3 archive and build the csv files
    :param output_directory: where to store the files
    :param max_id: the maximum user id
    :return:
    """
    done_dates = get_done_dates()

    # Now get ready to load the files
    keys_being_restored = []
    s3helper = S3Helper()
    bucket = s3helper.get_bucket(get_archive_bucket())
    set_filenames = set()
    for prefix in bucket.list(prefix='stats/', delimiter='/'):
        elements = prefix.name.split('/')
        elements = elements[1].split('_')
        date_file = date(int(elements[1]), int(elements[2]), int(elements[3]))
        if date_file not in done_dates:
            stats_file = '{0}_{1}_{2}_user.gz'.format(elements[1], elements[2], elements[3])
            full_filename = os.path.join(output_directory, stats_file)
            if full_filename in set_filenames:
                # Ignore
                pass
            elif not os.path.exists(full_filename) or os.path.getsize(full_filename) == 9:
                set_filenames.add(full_filename)
                key = bucket.get_key(os.path.join(prefix.name, 'user.gz'))
                if key is not None:
                    if key.ongoing_restore or key.storage_class == 'GLACIER':
                        LOG.info('Restoring {0}'.format(key.name))
                        # We need retrieve it
                        if not key.ongoing_restore:
                            key.restore(days=5)
                        keys_being_restored.append([key.name, full_filename])

                        # Put an empty file in the directory
                        if not os.path.exists(full_filename):
                            output_file = open(full_filename, "wb")
                            output_file.write('Restoring')
                            output_file.close()
                    else:
                        # Put the file in the storage area
                        LOG.info('Fetching {0}'.format(key.name))
                        key.get_contents_to_filename(full_filename)

    # Now we have to wait for all the files we need to be restored
    for key_pair in keys_being_restored:
        key = bucket.get_key(key_pair[0])
        if key.ongoing_restore:
            time.sleep(300)
        else:
            # The file has been restored so copy it
            LOG.info('Fetching {0}'.format(key_pair[0]))
            key.get_contents_to_filename(key_pair[1])

    # Build the prepared statements
    insert_usage = USAGE.insert()
    insert_individual = INDIVIDUAL.insert()

    # Now build up the list of filenames
    for file_name in glob.glob(os.path.join(output_directory, '*_user.gz')):
        (head, tail) = os.path.split(file_name)
        elements = tail.split('_')
        date_file = date(int(elements[0]), int(elements[1]), int(elements[2]))

        if date_file not in done_dates:
            # Read the contents
            LOG.info('Processing {0}'.format(file_name))
            gzip_file = gzip.open(file_name, 'rb')
            contents = gzip_file.read()
            gzip_file.close()

            # Extract the XML data
            root = ET.fromstring(contents)

            # Initialise
            gflops = 0.0
            active_users = 0
            registered_users = 0
            transaction = connection.begin()

            # The users are in a random order
            for user in root:
                user_id = user.find('id').text
                user_id = int(user_id)

                expavg_credit = user.find('expavg_credit').text
                expavg_credit = float(expavg_credit)

                connection.execute(insert_individual, date=date_file, user_id=user_id, expavg_credit=expavg_credit)

                registered_users += 1

                if expavg_credit > 1:
                    active_users += 1

                gflops += expavg_credit

            connection.execute(insert_usage, date=date_file, gflops=gflops / COBBLESTONE_FACTOR, active_users=active_users, registered_users=registered_users)
            transaction.commit()


def plot_individual_data_stack(file_name):
    """
    Plot the individual data
    :param file_name: the filename
    :return:
    """
    dates = []
    dates_map = {}
    user_ids_map = {}
    count = 0
    for entry in connection.execute(select([INDIVIDUAL.c.date]).distinct().order_by(INDIVIDUAL.c.date)):
        dates_map[entry[0]] = count
        dates.append(entry[0])
        count += 1
    count = 0
    for entry in connection.execute(select([INDIVIDUAL.c.user_id]).distinct().order_by(INDIVIDUAL.c.user_id)):
        user_ids_map[entry[0]] = count
        count += 1

    columns = len(user_ids_map.keys())
    rows = len(dates_map.keys())
    shape = (rows, columns)
    my_data = numpy.zeros(shape)

    LOG.info('Loading data ')
    for entry in connection.execute(select([INDIVIDUAL]).order_by(INDIVIDUAL.c.date, INDIVIDUAL.c.user_id)):
        my_data[dates_map[entry[INDIVIDUAL.c.date]],user_ids_map[entry[INDIVIDUAL.c.user_id]]] = entry[INDIVIDUAL.c.expavg_credit]

    # Now bin the data into bins
    LOG.info('Binning data')
    shape = (BINS_INDIVIDUAL, rows)
    bins = numpy.zeros(shape)

    edges = [START_BIN_INDIVIDUAL / 1000.0]
    for i in range(BINS_INDIVIDUAL - 1):
        value = START_BIN_INDIVIDUAL * math.pow(10, i)
        edges.append(value)
    edges.append(START_BIN_INDIVIDUAL * math.pow(10, BINS_INDIVIDUAL * 2))

    for row in range(rows):
        histogram = numpy.histogram(my_data[row, :] / COBBLESTONE_FACTOR, bins=edges)
        bins[:, row] = histogram[0]

    # Now plot it
    LOG.info('Printing')
    pdf_pages = PdfPages('{0}.pdf'.format(file_name))
    pyplot.xlabel('Date')
    pyplot.ylabel('Users')
    pyplot.xticks(rotation=30)

    x = [date2num(date) for date in dates]
    ax = pyplot.axes()
    ax.locator_params(axis='x', nbins=20)
    plots = ax.stackplot(x, bins)

    # Cause the labels to be generated
    pyplot.xlim(x[0], x[-1])
    pyplot.tight_layout()

    # Correct the dates on the x axis
    labels = []
    for location in ax.xaxis.get_ticklocs():
        if location < 0 or location > x[-1]:
            labels.append('')
        else:
            date = num2date(location)
            labels.append(date.strftime("%d-%m-%y"))

    ax.xaxis.set_ticklabels(labels)

    # Add the legend
    plot_count = 0
    labels = []
    proxy = []
    # Ignore the last one
    for plot in plots[:-1]:
        fc = plot.get_facecolor()
        proxy.append(pyplot.Rectangle((0, 0), 1, 1, fc=fc[0]))
        if plot_count == 0:
            labels.append('<= {0} Gflops'.format(edges[1]))
        elif plot_count == BINS_INDIVIDUAL - 2:
            labels.append('> {0} Gflops'.format(edges[BINS_INDIVIDUAL - 2]))
        else:
            labels.append('{0} to {1} Gflops'.format(edges[plot_count], edges[plot_count + 1]))
        plot_count += 1
    pyplot.legend(proxy, labels, loc=2, prop={'size': 10})

    # make sure everything fits
    pyplot.tight_layout()
    pdf_pages.savefig()
    pdf_pages.close()


def plot_individual_data(file_name):
    """
    Plot the individual data
    :param file_name:
    :return:
    """
    input_file = open(file_name, 'r')
    lines = input_file.readlines()
    input_file.close()

    y_dim = len(lines[0].split(',')) - 1
    x_dim = len(lines)
    shape = (x_dim, y_dim)
    my_data = numpy.zeros(shape)
    dates = []

    LOG.info('Loading data')
    line_count = 0
    for line in lines:
        data = line.split(',')
        my_data[line_count, :] = data[1:]
        dates.append(data[0])
        line_count += 1

    # Remove blank columns
    LOG.info('Removing blank columns')
    for column in reversed(range(y_dim)):
        if not numpy.any(my_data[:, column]):
            my_data = numpy.delete(my_data, column, 1)

    # Now plot it
    LOG.info('Printing')
    pdf_pages = PdfPages('{0}.pdf'.format(file_name))
    ax = pyplot.axes()
    divider = make_axes_locatable(ax)
    ax_cb = divider.new_horizontal(size="5%", pad=0.05)
    figure = ax.get_figure()
    figure.add_axes(ax_cb)
    image = ax.imshow(my_data / COBBLESTONE_FACTOR, norm=LogNorm(), origin='lower')
    ax.set_xlabel('Users')
    ax.set_ylabel('Date')
    colour_bar = pyplot.colorbar(image, cax=ax_cb)
    colour_bar.set_label('GFlops')
    ax_cb.yaxis.tick_right()

    # Cause the labels to be generated
    pyplot.tight_layout()

    # Correct the dates on the y axis
    labels = []
    for location in ax.yaxis.get_ticklocs():
        if location < 0 or location > len(dates):
            labels.append('')
        else:
            date = dates[int(location)]
            labels.append(date[:7])

    ax.yaxis.set_ticklabels(labels)

    # make sure everything fits
    pyplot.tight_layout()
    pdf_pages.savefig()
    pdf_pages.close()


def plot_usage_data(file_name):
    """
    Plot the data
    :param file_name:
    :return:
    """
    date = []
    gflops = []
    active_users = []
    registered_users = []
    for entry in connection.execute(select([USAGE]).order_by(USAGE.c.date)):
        date.append(entry[USAGE.c.date])
        gflops.append(entry[USAGE.c.gflops])
        active_users.append(entry[USAGE.c.active_users])
        registered_users.append(entry[USAGE.c.registered_users])

    pdf_pages = PdfPages(file_name)
    pyplot.subplot(211)
    pyplot.plot(date, active_users, 'b-', label='Active')
    pyplot.plot(date, registered_users, 'g-', label='Registered')
    pyplot.ylabel('Users')
    pyplot.xticks(rotation=30)
    pyplot.grid(True)
    pyplot.legend(loc=0)

    pyplot.subplot(212)
    pyplot.plot(date, gflops, 'r-')
    pyplot.xlabel('Date')
    pyplot.ylabel('GFlops')
    pyplot.xticks(rotation=30)
    pyplot.grid(True)
    pyplot.tight_layout()
    pdf_pages.savefig()
    pdf_pages.close()


def print_stats(data):
    for key, values in data.items():
        min_value = None
        max_value = None
        for value in values:
            if min_value is None:
                min_value = value
            else:
                min_value = min(value, min_value)

            if max_value is None:
                max_value = value
            else:
                max_value = max(value, max_value)

        LOG.info('key: {0}, min: {1}, max:{2}'.format(key, min_value, max_value))


def plot_file_size_histogram(file_name):
    """
    Plot the file size histogram

    :param file_name:
    :return:
    """
    data = get_hdf5_size_data()
    print_stats(data)

    LOG.info('Binning data')
    shape = (BINS_FILE_SIZE, 3)
    bins = numpy.zeros(shape)
    edges = [0.0000001, 1.0, 5.0, 10.0, 50.0, 100.0, 500.0, 1000.0]

    row = 0
    for key in [2, 1, 0]:
        values = data[key]
        histogram = numpy.histogram(values, bins=edges)
        LOG.info('key: {0}, bins: {1}'.format(key, histogram[0]))
        bins[:, row] = histogram[0]
        row += 1

    LOG.info('Printing')
    indexes = numpy.arange(BINS_FILE_SIZE)
    # Bar graphs expect a total width of "1.0" per group
    # Thus, you should make the sum of the two margins
    # plus the sum of the width for each entry equal 1.0.
    margin = 0.05
    width = (1. - 2. * margin) / 3
    pdf_pages = PdfPages('{0}'.format(file_name))
    rects = [0,0,0]
    colours = ['r', 'b', 'g']
    for row in range(0, 3):
        xdata = indexes + margin + (row * width)
        rects[row] = pyplot.bar(xdata, height=bins[:, row], width=width, log=True, color=colours[row])
    pyplot.xlabel('Size (MByte)')
    pyplot.ylabel('Frequency')
    pyplot.ylim(ymin=0.1, ymax=10000)
    pyplot.legend((rects[0], rects[1], rects[2]), ('5 Filters', '6 Filters', '11 Filters'))

    ax = pyplot.axes()
    ax.yaxis.grid(True)
    labels = []
    for location in ax.yaxis.get_ticklocs():
        if location < 0:
            labels.append('')
        else:
            labels.append("{0}".format(int(location)))

    ax.yaxis.set_ticklabels(labels)
    ax.set_xticks(indexes + 0.5)
    ax.set_xticklabels(('0-1', '1-5', '5-10', '10-50', '50-100', '100-500', '500-1000'))

    pyplot.tight_layout()
    pdf_pages.savefig()
    pdf_pages.close()


def get_hdf5_size_data():
    """
    Get the HDF5 data we need
    :return:
    """
    # Get the list of files
    LOG.info('Getting the hdf5 files from the database')
    data = {}
    set_names = set()

    for entry in connection.execute(select([HDF5_SIZE])):
        key_size_mb = entry[HDF5_SIZE.c.size] / 1000000.0
        LOG.info('Processing {0} {1} {2}'.format(entry[HDF5_SIZE.c.name], entry[HDF5_SIZE.c.size], key_size_mb))
        run_id = entry[HDF5_SIZE.c.run_id]

        # Get the array
        row_data = data.get(run_id)
        if row_data is None:
            row_data = []
            data[run_id] = row_data

        row_data.append(key_size_mb)
        set_names.add(entry[HDF5_SIZE.c.name])

    LOG.info('Getting the hdf5 files from S3')
    s3helper = S3Helper()
    bucket = s3helper.get_bucket(get_files_bucket())
    insert_hdf5 = HDF5_SIZE.insert()
    for prefix in bucket.list(prefix='', delimiter='/'):
        prefix_name = prefix.name[:-1]
        if prefix_name not in set_names:
            key = bucket.get_key('{0}/{0}.hdf5'.format(prefix_name))
            if key is not None:
                key_size_mb = key.size / 1000000.0
                LOG.info('Processing {0} {1} {2}'.format(key.name, key.size, key_size_mb))
                elements = prefix.name.split('__')
                run_id = int(elements[1])

                connection.execute(insert_hdf5, name=prefix_name, size=key.size, run_id=run_id)

                # Get the array
                row_data = data.get(run_id)
                if row_data is None:
                    row_data = []
                    data[run_id] = row_data

                row_data.append(key_size_mb)

    return data


def plot_file_size_line(pdf_file_name):
    """
    Plot the file size histogram

    :param pdf_file_name:
    :return:
    """
    data = get_hdf5_size_data()

    LOG.info('Printing')
    pdf_pages = PdfPages('{0}'.format(pdf_file_name))
    # Print the data
    markers = {11: 'o', 5: 'D', 6: '+'}
    colours = {11: 'r', 5: 'g', 6: 'b'}
    for key, value in data.iteritems():
        x = []
        y = []
        for values in value:
            x.append(values[2] / 1000.0)
            y.append(values[1])
        pyplot.scatter(x, y, marker=markers[key], c=colours[key], label='{0} filters'.format(key))

    pyplot.xlabel('Pixels (K)')
    pyplot.ylabel('Size (MB)')
    pyplot.xlim(0,)
    pyplot.ylim(0,)
    pyplot.grid(True)
    pyplot.legend(loc=2)
    pyplot.tight_layout()
    pdf_pages.savefig()
    pdf_pages.close()
