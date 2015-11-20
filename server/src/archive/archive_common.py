#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012-2016
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
Common code for archiving
"""
import config


def get_chunks(dimension):
    """
    Break the dimension up into chunks
    :param dimension:
    :return: a list with the number of chunks

    >>> get_chunks(1)
    [0]
    >>> get_chunks(10)
    [0]
    >>> get_chunks(1023)
    [0]
    >>> get_chunks(1024)
    [0]
    >>> get_chunks(1025)
    [0, 1]
    >>> get_chunks(2047)
    [0, 1]
    >>> get_chunks(2048)
    [0, 1]
    >>> get_chunks(2049)
    [0, 1, 2]

    """
    return range(((dimension - 1) / config.MAX_X_Y_BLOCK) + 1)


def get_size(block, dimension):
    """
    How big is this axis
    :param block:
    :param dimension:
    :return:

    >>> get_size(0, 50)
    50
    >>> get_size(0, 1024)
    1024
    >>> get_size(0, 2244)
    1024
    >>> get_size(1, 2244)
    1024
    >>> get_size(2, 2244)
    196
    """
    elements = get_chunks(dimension)
    if len(elements) == 1:
        return dimension
    elif block < len(elements) - 1:
        return config.MAX_X_Y_BLOCK

    return dimension - (block * config.MAX_X_Y_BLOCK)


def pixel_in_block(raw_x, raw_y, block_x, block_y):
    """
    Is the pixel inside the block we're processing

    :param raw_x:
    :param raw_y:
    :param block_x:
    :param block_y:
    :return:
    >>> pixel_in_block(0, 0, 0, 0)
    True
    >>> pixel_in_block(0, 0, 0, 1)
    False
    >>> pixel_in_block(0,0,1,0)
    False
    >>> pixel_in_block(1023,0,0,0)
    True
    >>> pixel_in_block(1024,0,0,0)
    False
    >>> pixel_in_block(1024,0,1,0)
    True
    >>> pixel_in_block(0,1024,0,1)
    True
    >>> pixel_in_block(1024,1024,0,1)
    False
    >>> pixel_in_block(1024,1024,1,0)
    False
    """
    block_top_x = block_x * config.MAX_X_Y_BLOCK
    block_top_y = block_y * config.MAX_X_Y_BLOCK
    block_bottom_x = block_top_x + config.MAX_X_Y_BLOCK - 1
    block_bottom_y = block_top_y + config.MAX_X_Y_BLOCK - 1
    return block_top_x <= raw_x <= block_bottom_x and block_top_y <= raw_y <= block_bottom_y
