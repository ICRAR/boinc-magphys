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
The plot routines
"""
import logging
from matplotlib import pyplot
from matplotlib.backends.backend_pdf import PdfPages

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

def plot_differences(image_names, galaxy_details, array01, len_galaxy_ids):
    """
    Calculate the raw differences and plot them
    """
    pdf_pages = PdfPages('plots-{0}.pdf'.format(galaxy_details[0].name))
    for i in range(len_galaxy_ids - 1):
        for j in range(i + 1, len_galaxy_ids):
            LOG.info('Comparing %s with %s', galaxy_details[i].name, galaxy_details[j].name)
            number_elements = len(image_names)
            data = [[[] for _ in range(3)] for _ in range(number_elements)]
            for x in range(galaxy_details[0].dimension_x):
                for y in range(galaxy_details[0].dimension_y):
                    for z in range(number_elements):
                        if array01[x][y][z][i].value is not None and array01[x][y][z][j].value is not None:
                            data[z][0].append(array01[x][y][z][i].value - array01[x][y][z][j].value)
                        if array01[x][y][z][i].median is not None and array01[x][y][z][j].median is not None:
                            data[z][1].append(array01[x][y][z][i].median - array01[x][y][z][j].median)
                        if array01[x][y][z][i].highest_prob_bin is not None and array01[x][y][z][j].highest_prob_bin is not None:
                            data[z][2].append(array01[x][y][z][i].highest_prob_bin - array01[x][y][z][j].highest_prob_bin)

            for z in range(number_elements):
                figure = pyplot.figure()         # the z-th figure
                figure.subplots_adjust(hspace=.6)
                figure.suptitle('{0} vs {1}'.format(galaxy_details[i].name, galaxy_details[j].name))
                pyplot.subplot(3,1,1)             # the first subplot in the figure
                pyplot.title('Value - {0}'.format(image_names[z]))
                pyplot.xlabel('Difference')
                pyplot.ylabel('Number')
                pyplot.grid(True)
                pyplot.hist(data[z][0], bins=99)

                pyplot.subplot(3,1,2)             # the second subplot in the figure
                pyplot.title('Median - {0}'.format(image_names[z]))
                pyplot.xlabel('Difference')
                pyplot.ylabel('Number')
                pyplot.grid(True)
                pyplot.hist(data[z][1], bins=99)

                pyplot.subplot(3,1,3)             # the third subplot
                pyplot.title('Highest Probability Bin - {0}'.format(image_names[z]))
                pyplot.xlabel('Difference')
                pyplot.ylabel('Number')
                pyplot.grid(True)
                pyplot.hist(data[z][2], bins=99)

                pdf_pages.savefig()

    pdf_pages.close()
