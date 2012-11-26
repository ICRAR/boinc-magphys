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
from matplotlib import pyplot

def plot_differences(range_mse, galaxy_details, array01, i, j):
    """
    Calculate the raw differences and plot them
    """
    for x in range(galaxy_details[0].dimension_x):
        for y in range(galaxy_details[0].dimension_y):
            for z in range_mse:
                if array01[x][y][z][i].value is not None and array01[x][y][z][j].value is not None:
                    pass # TODO
                if array01[x][y][z][i].median is not None and array01[x][y][z][j].median is not None:
                    pass #TODO
                if array01[x][y][z][i].highest_prob_bin is not None and array01[x][y][z][j].highest_prob_bin is not None:
                    pass #TODO

figure = pyplot.figure(1)         # the first figure
figure.subplots_adjust(hspace=.5)
pyplot.subplot(3,1,1)             # the first subplot in the first figure
pyplot.title('Value')
pyplot.plot([1,2,3])

pyplot.subplot(3,1,2)             # the second subplot in the first figure
pyplot.title('Median')
pyplot.plot([4,5,6])

pyplot.subplot(3,1,3)             # the third subplot
pyplot.title('Highest Probability Bin')   # subplot 211 title

pyplot.show()
