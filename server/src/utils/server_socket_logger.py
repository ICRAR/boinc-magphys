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
import thread
from socket import *
import struct
import cPickle
import logging
import logging.handlers
import sys
import os
import getopt

from config import LOGGER_LOCAL_PORT, LOGGER_LOG_DIRECTORY, LOGGER_MAX_CONNECTION_REQUESTS
from logging_helper import config_logger

#Local logger for server logs
server_log = config_logger('ServerLog')


def main(argv):

    #Local vars
    local_host = gethostname()
    log_directory = LOGGER_LOG_DIRECTORY
    local_port = LOGGER_LOCAL_PORT
    logger_number = '1'

    try:
        opts, args = getopt.getopt(argv, "p:d:", ["l_port=", "l_dir="])

    except getopt.GetoptError as e:
        print e.args[0]
        usage()
        exit(2)

    #Handle command line args
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

    #Need to ensure save_directory ends with a /
    if not log_directory.endswith('/'):
        log_directory += '/'

    #Try to create log file directory
    if not os.path.isdir(log_directory):
        try:
            server_log.info('Creating log directory...')
            os.mkdir(log_directory)

        except OSError as e:
            server_log.info(e.args[1])
            #server_log.info('Log directory already exists')
            exit(-1)

    #Set up sockets
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

            #Handle each new client in a new thread.
            thread.start_new_thread(handle_client, (log_directory, client_socket, logger_number))

        except thread.error as e:
            server_log.error(e.args[1])
            exit(-1)

        except IOError as e:
            server_log.error(e.args[1])
            exit(-1)

        #Next client must use a different local logger. Append '1' to the name of the previous local logger
        logger_number += '1'


def usage():
    print 'Usage: log_server.py -p <port> -d <log directory>'


def handle_client(save_directory, c_socket, l_number):
    file_open = 0
    logger = logging.getLogger(l_number)

    while 1:
        #Try to receive data from the client
        try:
            chunk = c_socket.recv(4)

        except IOError as e:
            server_log.error(e.args[1])
            #server_log.error('Connection closed by client')
            return 0

        if len(chunk) < 4:
            server_log.info('Connection terminated normally')
            return 0

        #This chunk of code extracts a log record from the received data and places it into record
        slen = struct.unpack('>L', chunk)[0]
        chunk = c_socket.recv(slen)

        while len(chunk) < slen:
            chunk = chunk + c_socket.recv(slen - len(chunk))

        obj = cPickle.loads(chunk)
        record = logging.makeLogRecord(obj)

        if file_open == 0:
            #Set up log handler to print logs to file. Need at least one log to obtain name from
            formatter = logging.Formatter('%(asctime)-15s:' + logging.BASIC_FORMAT)
            file_handler = logging.FileHandler(save_directory + record.name + '.log')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            file_open = 1

        #finally, handle the record by printing it to the file specified
        logger.handle(record)


if __name__ == "__main__":
    main(sys.argv[1:])