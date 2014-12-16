#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012-2013
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
Configure a logger
"""
import logging
import logging.handlers
from logger.DetailedSocketHandler import DetailedSocketHandler

# Set up the root logger as the project likes it
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)


def config_logger(name):
    """
    Get a logger

    :param name:
    :return:
    """
    logger = logging.getLogger(name)

    return logger


def add_socket_handler_to_root(host, port):
    """
    Old way of adding a socket handler. Will NOT specify the remote filename to write to.
    :param host:
    :param port:
    :return:
    """
    formatter = logging.Formatter('%(asctime)-15s:' + logging.BASIC_FORMAT)
    socket_handler = logging.handlers.SocketHandler(host, port)
    socket_handler.setFormatter(formatter)
    logging.getLogger().addHandler(socket_handler)


def add_special_handler_to_root(host, port, fname):
    """
    New way of adding a socket handler. Specify a filename for the remote server to write to.
    :param host:
    :param port:
    :param fname:
    :return:
    """
    formatter = logging.Formatter('%(asctime)-15s:' + logging.BASIC_FORMAT)
    special_handler = DetailedSocketHandler(host, port, fname)
    special_handler.setFormatter(formatter)
    logging.getLogger().addHandler(special_handler)


def add_file_handler_to_root(file_name):
    """
    Added a file logger to the root

    :param file_name:
    :return:
    """
    formatter = logging.Formatter('%(asctime)-15s:' + logging.BASIC_FORMAT)
    file_handler = logging.FileHandler(file_name)
    file_handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
