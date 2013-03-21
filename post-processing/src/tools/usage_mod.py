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
import collections
import glob
import os
import gzip
import xml.etree.ElementTree as ET
import logging

from datetime import datetime
import csv
from matplotlib import pyplot
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import LogNorm
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

COBBLESTONE_FACTOR = 150.0

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
        expavg_credit =  user.find('expavg_credit').text
        expavg_credit = float(expavg_credit)

        if expavg_credit > 1:
            active_users += 1

        gflops += expavg_credit

    return gflops / COBBLESTONE_FACTOR, active_users, registered_users

def get_usage_data(dir, file_name):
    """
    Get the data we want to plot

    :param dir: where the data files live
    :param file_name: the output file to store the data in
    :return:
    """
    files = os.path.join(dir, '*')

    file_list = {}
    for directory in glob.glob(files):
        if os.path.isdir(directory):
            file = os.path.join(directory, 'user.gz')
            if os.path.isfile(file):
                base_name = os.path.basename(directory)
                elements = base_name.split('_')
                time = datetime(int(elements[1]), int(elements[2]), int(elements[3]), int(elements[4]), int(elements[5]))
                file_list[time] = file

    # Now sort the list
    file_list_sorted = collections.OrderedDict(sorted(file_list.items()))

    output_file = open(file_name, 'w')
    output_file.write('Date, gflops, active_users, registered_users\n')

    for time, file in file_list_sorted.iteritems():
        LOG.info('Processing %s', file)
        gzip_file = gzip.open(file, 'rb')
        contents = gzip_file.read()
        gzip_file.close()

        # Extract the data
        d1, d2, d3 = add_usage_data(contents)

        # Write the aggregated data
        output_file.write('{0}, {1}, {2}, {3}\n'.format(time, d1, d2, d3))

    output_file.close()

def get_individual_data(dir, file_name, max_id):
    """
    Get the data we want to plot

    :param dir: where the data files live
    :param file_name: the output file to store the data in
    :return:
    """
    files = os.path.join(dir, '*')

    file_list = {}
    for directory in glob.glob(files):
        if os.path.isdir(directory):
            file = os.path.join(directory, 'user.gz')
            if os.path.isfile(file):
                base_name = os.path.basename(directory)
                elements = base_name.split('_')
                time = datetime(int(elements[1]), int(elements[2]), int(elements[3]), int(elements[4]), int(elements[5]))
                file_list[time] = file

    # Now sort the list
    file_list_sorted = collections.OrderedDict(sorted(file_list.items()))
    with open(file_name, 'wb') as output_file:
        writer = csv.writer(output_file)
        for time, file in file_list_sorted.iteritems():
            LOG.info('Processing %s', file)
            gzip_file = gzip.open(file, 'rb')
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

                expavg_credit =  user.find('expavg_credit').text
                expavg_credit = float(expavg_credit)

                data[user_id] = expavg_credit

            writer.writerow(data)

def plot_individual_data(file):
    """
    Plot the individual data
    :param file:
    :return:
    """
    input_file = open(file, 'r')
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
    pdf_pages = PdfPages('{0}.pdf'.format(file))
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

def plot_usage_data(file):
    """
    Plot the data
    :param file:
    :return:
    """
    col_headers = ['date','gflops','active_users','registered_users']
    convert_func = lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S')
    my_data = numpy.genfromtxt(file, delimiter=',', names=col_headers, skip_header=1, converters={'date':convert_func}, dtype=None)

    pdf_pages = PdfPages('{0}.pdf'.format(file))
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
