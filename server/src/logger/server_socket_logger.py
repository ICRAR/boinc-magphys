#! /usr/bin/env python2.7
#
# (c) UWA, The University of Western Australia
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
from socket import *
import struct
import cPickle
import logging
import logging.handlers
import sys
import os
import getopt
import signal

from config import LOGGER_SERVER_PORT, LOGGER_LOG_DIRECTORY, LOGGER_MAX_CONNECTION_REQUESTS
from utils.logging_helper import config_logger

# Local logger for server logs
server_log = config_logger('ServerLog')
server_log.addHandler(logging.FileHandler('ServerLog'))

def main(argv):
    """
    Main program.
    1.Gets command line arguments and changes local_port or log_directory to match arguments.
      If no arguments are given, the defaults defined in config are used.
    2.Create log directory if it does not exist
    3.Set up socket to listen on specified port
    loop
        4.When connection is received, create new process to handle client
        5.Clean up any defunct processes

    Will only exit when killed or an error occurs
    :param argv: command line args
    :return: void
    """

    # Install sigint handler for shutdown
    signal.signal(signal.SIGINT, shutdown)

    # Local vars
    local_host = gethostname()
    log_directory = LOGGER_LOG_DIRECTORY
    local_port = LOGGER_SERVER_PORT
    logger_number = '1'

    # Get command line args
    try:
        opts, args = getopt.getopt(argv, "p:d:", ["l_port=", "l_dir="])

    except getopt.GetoptError as e:
        print e.args[0]
        usage()
        exit(2)

    # Handle command line args
    for opt, arg in opts:
        if opt in ("-p", "--l_port"):
            try:
                local_port = int(arg)
            except ValueError as e:
                print e.args[0]
                usage()
                exit(2)

        elif opt in ("-d", "--l_dir"):
            log_directory = arg

    # Need to ensure save directory ends with a /
    if not log_directory.endswith('/'):
        log_directory += '/'

    # Try to create log file directory
    if not os.path.isdir(log_directory):
        try:
            server_log.info('Creating log directory...')
            os.mkdir(log_directory)

        except OSError as e:
            server_log.info(e.args[1])
            # Server_log.info('Log directory already exists')
            exit(-1)

    # Set up sockets
    try:
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind((local_host, local_port))

        server_log.info('Listening on %s : %d', local_host, local_port)
        server_socket.listen(LOGGER_MAX_CONNECTION_REQUESTS)
    except IOError as e:
        server_log.error(e.args[1])
        exit(-1)

    while 1:
        try:
            client_socket, addr = server_socket.accept()
            server_log.info('Incoming connection from %s', addr)

            # Handle each new client in a new process.
            pid = os.fork()

            if pid == 0:  # In child
                handle_client(log_directory, client_socket, logger_number)
                exit(0)

            if pid > 0:  # In parent
                # Reclaim any defunct processes to keep process table clean.
                child_reclaim()
                # Next client must use a different local logger. Append '1' to the name of the previous local logger
                logger_number = '' + (int(logger_number) + 1)

        except IOError as e:  # Socket error
            server_log.error(e.args[1])

        except OSError as e:  # Fork error
            server_log.error(e.args[1])


def usage():
    """
    Prints out usage info for the program
    :return: void
    """
    print 'Usage: log_server.py -p <port> -d <log directory>'


def handle_client(save_directory, c_socket, l_number):
    """
    Handles a single client

    Will receive data from the client until the client either sends no more data or the socket connection is interrupted
    somehow.

    Each log is unpacked from the client and record.name of the first record received is used to determine the name of
    the local file to save to. If the client wishes to switch to a different file they must create a new connection.

    :param save_directory: the location in which to save logs from this client
    :param c_socket: the socket the client is connected on
    :param l_number: the logger number to be used by this handle instance
    :return: void
    """
    file_open = 0
    logger = logging.getLogger(l_number)

    while 1:
        # Try to receive a log from the client
        try:
            chunk = c_socket.recv(4)

        except IOError as e:
            server_log.error(e.args[1])
            # Server_log.error('Connection closed by client')
            return 0

        if len(chunk) < 4:
            server_log.info('Connection terminated normally')
            return 0

        # This chunk of code extracts a log record from the received data and places it into record
        slen = struct.unpack('>L', chunk)[0]
        chunk = c_socket.recv(slen)

        while len(chunk) < slen:
            chunk = chunk + c_socket.recv(slen - len(chunk))

        obj = cPickle.loads(chunk)
        record = logging.makeLogRecord(obj)

        if file_open == 0:
            # Set up log handler to print logs to file. Need at least one log to obtain name from
            formatter = logging.Formatter('%(asctime)-15s:' + logging.BASIC_FORMAT)
            file_handler = logging.FileHandler(save_directory + record.name + '.log')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            file_open = 1

        # Finally, handle the record by printing it to the file specified
        logger.handle(record)


def child_reclaim():
    """
    Reclaims defunct child processes

    Checks for any child processes that have exited and reclaims them, removing their defunct entry from the process
    table.
    :return: void
    """
    more = 1

    while more:
        # Wait for any defunct child processes to remove them from the process table
        (pid, status) = os.waitpid(-1, os.P_NOWAIT)
        if pid <= 0:
            more = 0

    return


def shutdown():
    """
    Things to do when a shutdown signal is received.

    :return:
    """
    child_reclaim()
    server_log.info('Logging server shutting down')
    exit(0)


if __name__ == "__main__":
    main(sys.argv[1:])