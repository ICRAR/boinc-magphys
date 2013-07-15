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
import StringIO
import collections
import glob
import os
import gzip
import urllib2
import xml.etree.ElementTree as ET
import logging
import csv
import math
import numpy

from datetime import datetime
from matplotlib import pyplot
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import LogNorm
from matplotlib.dates import date2num, num2date
from mpl_toolkits.axes_grid1 import make_axes_locatable
from sqlalchemy import create_engine, select
from config import DB_LOGIN
from database.database_support_core import GALAXY

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

COBBLESTONE_FACTOR = 150.0
BINS = 8
START_BIN = 0.001


def add_usage_data(contents):
    """
    Parse the XML and return the data to be added

    :param contents: the XML to be parsed
    :return:
    """
    root = ET.fromstring(contents)

    gflops = 0.0
    active_users = 0
    registered_users = 0
    for user in root:
        registered_users += 1
        expavg_credit = user.find('expavg_credit').text
        expavg_credit = float(expavg_credit)

        if expavg_credit > 1:
            active_users += 1

        gflops += expavg_credit

    return gflops / COBBLESTONE_FACTOR, active_users, registered_users


def get_usage_data(dir_name, file_name):
    """
    Get the data we want to plot

    :param dir_name: where the data files live
    :param file_name: the output file to store the data in
    :return:
    """
    files = os.path.join(dir_name, '*')

    file_list = {}
    for directory in glob.glob(files):
        if os.path.isdir(directory):
            file_user = os.path.join(directory, 'user.gz')
            if os.path.isfile(file_user):
                base_name = os.path.basename(directory)
                elements = base_name.split('_')
                time = datetime(int(elements[1]), int(elements[2]), int(elements[3]), int(elements[4]), int(elements[5]))
                file_list[time] = file_user

    # Now sort the list
    file_list_sorted = collections.OrderedDict(sorted(file_list.items()))

    output_file = open(file_name, 'w')
    output_file.write('Date, gflops, active_users, registered_users\n')

    for time, file_user in file_list_sorted.iteritems():
        LOG.info('Processing %s', file_user)
        gzip_file = gzip.open(file_user, 'rb')
        contents = gzip_file.read()
        gzip_file.close()

        # Extract the data
        d1, d2, d3 = add_usage_data(contents)

        # Write the aggregated data
        output_file.write('{0}, {1}, {2}, {3}\n'.format(time, d1, d2, d3))

    output_file.close()


def get_individual_data(dir_name, file_name, max_id):
    """
    Get the data we want to plot

    :param dir_name: where the data files live
    :param file_name: the output file to store the data in
    :return:
    """
    files = os.path.join(dir_name, '*')

    file_list = {}
    for directory in glob.glob(files):
        if os.path.isdir(directory):
            file_user = os.path.join(directory, 'user.gz')
            if os.path.isfile(file_user):
                base_name = os.path.basename(directory)
                elements = base_name.split('_')
                time = datetime(int(elements[1]), int(elements[2]), int(elements[3]), int(elements[4]), int(elements[5]))
                file_list[time] = file_user

    # Now sort the list
    file_list_sorted = collections.OrderedDict(sorted(file_list.items()))
    with open(file_name, 'wb') as output_file:
        writer = csv.writer(output_file)
        for time, file_user in file_list_sorted.iteritems():
            LOG.info('Processing %s', file_user)
            gzip_file = gzip.open(file_user, 'rb')
            contents = gzip_file.read()
            gzip_file.close()

            # Extract the data
            root = ET.fromstring(contents)
            data = [0.0] * (max_id + 1)
            data[0] = time

            # The users are in a random order
            for user in root:
                user_id = user.find('id').text
                user_id = int(user_id)

                expavg_credit = user.find('expavg_credit').text
                expavg_credit = float(expavg_credit)

                data[user_id] = expavg_credit

            writer.writerow(data)


def plot_individual_data_stack(file_name):
    """
    Plot the individual data
    :param file_name: the filename
    :return:
    """
    input_file = open(file_name, 'r')
    lines = input_file.readlines()
    input_file.close()

    csv_columns = len(lines[0].split(',')) - 1
    csv_rows = len(lines)
    shape = (csv_rows, csv_columns)
    my_data = numpy.zeros(shape)
    dates = []

    LOG.info('Loading data ')
    line_count = 0
    for line in lines:
        data = line.split(',')
        my_data[line_count, :] = data[1:]
        dates.append(datetime.strptime(data[0], '%Y-%m-%d %H:%M:%S'))
        line_count += 1

    # Remove blank columns
    LOG.info('Removing blank columns from CSV data')
    for column in reversed(range(csv_columns)):
        if not numpy.any(my_data[:, column]):
            my_data = numpy.delete(my_data, column, 1)

    # Now bin the data into bins
    LOG.info('Binning data')
    shape = (BINS, csv_rows)
    bins = numpy.zeros(shape)

    edges = [START_BIN / 1000.0]
    for i in range(BINS - 1):
        value = START_BIN * math.pow(10, i)
        edges.append(value)
    edges.append(START_BIN * math.pow(10, BINS * 2))

    for row in range(csv_rows):
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

    # Correct the dates on the y axis
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
        elif plot_count == BINS - 2:
            labels.append('> {0} Gflops'.format(edges[BINS - 2]))
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
    col_headers = ['date','gflops','active_users','registered_users']
    convert_func = lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S')
    my_data = numpy.genfromtxt(file_name, delimiter=',', names=col_headers, skip_header=1, converters={'date':convert_func}, dtype=None)

    pdf_pages = PdfPages('{0}.pdf'.format(file_name))
    pyplot.subplot(211)
    pyplot.plot(my_data['date'], my_data['active_users'], 'b-', label='Active')
    pyplot.plot(my_data['date'], my_data['registered_users'], 'g-', label='Registered')
    pyplot.ylabel('Users')
    pyplot.xticks(rotation=30)
    pyplot.grid(True)
    pyplot.legend(loc=0)

    pyplot.subplot(212)
    pyplot.plot(my_data['date'], my_data['gflops'], 'r-')
    pyplot.xlabel('Date')
    pyplot.ylabel('GFlops')
    pyplot.xticks(rotation=30)
    pyplot.grid(True)
    pyplot.tight_layout()
    pdf_pages.savefig()
    pdf_pages.close()


def plot_file_size_histogram(file_name):
    """
    Plot the file size histogram

    :param file_name:
    :return:
    """
    data = get_hdf5_size_data()
    hist_data = []
    for key in [5, 6, 11]:
        value = data[key]
        sizes = []
        for values in value:
            sizes.append(values[1])
        hist_data.append(sizes)

    LOG.info('Printing')
    pdf_pages = PdfPages('{0}'.format(file_name))
    pyplot.hist(hist_data, bins=20, log=True, color=['crimson', 'burlywood', 'chartreuse'], label=['5 Filters', '6 Filters', '11 Filters'])
    pyplot.xlabel('Size (MByte)')
    pyplot.ylabel('Frequency')
    pyplot.grid(True)
    pyplot.legend()

    ax = pyplot.axes()
    labels = []
    for location in ax.yaxis.get_ticklocs():
        if location < 0:
            labels.append('')
        else:
            labels.append("{0}".format(int(location)))

    ax.yaxis.set_ticklabels(labels)

    pyplot.tight_layout()
    pdf_pages.savefig()
    pdf_pages.close()


def get_hdf5_size_data():
    """
    Get the HDF5 data we need
    :return:
    """
    # Get the list of files
    LOG.info('Getting the galaxies list from the database')
    engine_aws = create_engine(DB_LOGIN)
    connection = engine_aws.connect()
    galaxy_details = {}
    for galaxy in connection.execute(select([GALAXY])):
        if galaxy[GALAXY.c.version_number] == 1:
            name = galaxy[GALAXY.c.name]
        else:
            name = '{0}_V{1}'.format(galaxy[GALAXY.c.name], galaxy[GALAXY.c.version_number])

        galaxy_details[name] = (galaxy[GALAXY.c.dimension_z], galaxy[GALAXY.c.pixels_processed])
        if len(galaxy_details) % 100 == 0:
            LOG.info('Retrieved {0}'.format(len(galaxy_details)))
    connection.close()
    # Get the list of files
    LOG.info('Getting the galaxies list from Cortex')
    response = urllib2.urlopen("http://cortex.ivec.org:7780/QUERY?query=files_list&format=list")
    web_page = response.read()
    data = {}
    LOG.info('Collecting the data')
    for line in StringIO.StringIO(web_page):
        items = line.split()

        file_size = items[5]

        if int(file_size) > 0:
            file_size_mb = int(file_size) / 1000000.0

            # Get the sizes from the database
            file_name = items[2]
            split = os.path.splitext(file_name)
            name = split[0]

            # Get the galaxy
            galaxy = galaxy_details.get(name)

            # Get the array
            row_data = data.get(galaxy[0])
            if row_data is None:
                row_data = []
                data[galaxy[0]] = row_data
            row_data.append((name, file_size_mb, galaxy[1]))
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
