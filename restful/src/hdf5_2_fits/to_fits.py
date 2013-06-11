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
The Celery tasks to convert an HDF5 file to a series of zip files
http://cortex.ivec.org:7780/QUERY?query=files_list&format=list
http://cortex.ivec.org:7780/RETRIEVE?file_id=NGC3055.hdf5

"""
import os
import smtplib
import subprocess
import urllib
import shlex
from email.mime.text import MIMEText
import uuid
from celery import Task
import h5py
import tarfile
from extract_from_hdf5_mod import build_fits_image
from hdf5_2_fits import HDF5_DIRECTORY, FROM_EMAIL, SMTP_SERVER, OUTPUT_DIRECTORY
from start import celery

# A dictionary to the results so it can be cleaned up nicely in the on_failure and on_success
results_dict = {}


class SpecialTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        If the task fails email that it has
        """
        print('on_failure called')
        print('self    = {0}'.format(self.request))
        print('exc     = {0}'.format(exc))
        print('task_id = {0}'.format(task_id))
        print('args    = {0}'.format(args))
        print('kwargs  = {0}'.format(kwargs))
        print('einfo   = {0}'.format(einfo))

        # Fail and send email
        results = results_dict.pop(task_id, 'ERROR')
        send_email(kwargs['email'], results, kwargs['galaxy_name'])

        super(SpecialTask, self).on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """
        We're retrying a task
        """
        print('on_retry called')
        super(SpecialTask, self).on_retry(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        print('on_success called')
        results_dict.pop(task_id, None)
        super(SpecialTask, self).on_success(retval, task_id, args, kwargs)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        print('after_return called')
        super(SpecialTask, self).after_return(status, retval, task_id, args, kwargs, einfo)


@celery.task(ignore_result=True, name='to_fits.generate_files')
def generate_files(galaxy_name=None, email=None, features=None, layers=None, uuid_str=None):
    """
    Generate the files request by the user from the HDF5 file and email them telling them where to download them from

    :param galaxy_name: the galaxy to process
    :param email: the email to explain progress
    :param features: the features requested
    :param layers: the layers requested
    :return:
    """
    if galaxy_name is not None and features is not None and layers is not None:
        if uuid_str is None:
            uuid_str = str(uuid.uuid4())
        get_hdf5_file.delay(galaxy_name=galaxy_name, email=email, features=features, layers=layers, uuid_string=uuid_str)

    else:
        raise ValueError('generate_files all four arguments must be supplied')


@celery.task(base=SpecialTask, ignore_result=True, name='to_fits.get_hdf5_file')
def get_hdf5_file(galaxy_name=None, email=None, features=None, layers=None, uuid_string=None):
    """
    Get the file from cortex.
    http://cortex.ivec.org:7780/RETRIEVE?file_id=NGC3055.hdf5

    If the get fails retry depending on how many times it has failed (as cortex might not be available)

    :param galaxy_name: the galaxy to process
    :param email: the email to explain progress
    :param features: the features requested
    :param layers: the layers requested
    :return:
    """
    print('{0} - {1}'.format(galaxy_name, get_hdf5_file.request.id))
    ngas_file_name = galaxy_name + '.hdf5'
    path_name = get_file_name(HDF5_DIRECTORY, uuid_string, galaxy_name, 'hdf5')
    command_string = 'wget -O {0} http://cortex.ivec.org:7780/RETRIEVE?file_id={1}&processing=ngamsMWACortexStageDppi'.format(path_name, urllib.quote(ngas_file_name, ''))
    print(command_string)
    try:
        output = subprocess.check_output(shlex.split(command_string), stderr=subprocess.STDOUT)
        result = check_results(output, path_name)

        if result:
            # Submit to the next step in the chain
            build_files.delay(galaxy_name=galaxy_name, email=email, features=features, layers=layers, uuid_string=uuid_string)

        else:
            # Store the result in the task
            results_dict[get_hdf5_file.request.id] = result

            # Retry
            raise get_hdf5_file.retry()
    except subprocess.CalledProcessError as e:
        print('CalledProcessError - {0}'.format(e.output))
        # Store the result in the task
        results_dict[get_hdf5_file.request.id] = e.output

        # If it is an Error 400: Bad Request - fail
        if check_failure(e.output):
            raise
        else:
            print('Retrying')
            # Retry
            raise get_hdf5_file.retry()


@celery.task(base=SpecialTask, ignore_result=True, name='to_fits.build_files')
def build_files(galaxy_name=None, email=None, features=None, layers=None, uuid_string=None):
    """
    Build the files we need in parallel

    :param galaxy_name: the galaxy to process
    :param email: the email to explain progress
    :param features: the features requested
    :param layers: the layers requested
    :return:
    """
    print('Building files for {0} - {1} - {2}'.format(galaxy_name, features, layers))
    file_name = get_file_name(HDF5_DIRECTORY, uuid_string, galaxy_name, 'hdf5')
    if os.path.isfile(file_name):
        h5_file = h5py.File(file_name, 'r')
        galaxy_group = h5_file['galaxy']
        pixel_group = galaxy_group['pixel']
        pixel_data = pixel_group['pixels']

        file_names = []
        output_dir = create_if_necessary(OUTPUT_DIRECTORY, uuid_string)
        for feature in features:
            for layer in layers:
                file_names.append(build_fits_image(feature, layer, output_dir, galaxy_group, pixel_data))

        h5_file.close()
        zip_files_and_email.delay(galaxy_name=galaxy_name, email=email, file_names=file_names, uuid_string=uuid_string)

    else:
        error = 'The file {0} does not exist'.format(file_name)
        results_dict[build_files.request.id] = error
        raise ValueError(error)


@celery.task(base=SpecialTask, ignore_result=True, name='to_fits.zip_files_and_email')
def zip_files_and_email(galaxy_name=None, email=None, file_names=None, uuid_string=None):
    """
    Zip the files and send the email

    :param galaxy_name: the galaxy to process
    :param email: the email to explain progress
    :param file_names: the fits files to be bundled
    :return:
    """
    zip_up_files(galaxy_name, file_names, uuid_string)
    if email is not None:
        send_email(email, get_final_message(galaxy_name, file_names, uuid_string), galaxy_name)
    clean_up_file(galaxy_name, uuid_string)


def create_if_necessary(directory, uuid_str):
    """
    Create the directory if needed

    :param directory: the parent directory
    :param uuid_str: the uuid string that will become holding directory
    :return:
    """
    # Find the name of the directory to use
    dir_name = os.path.join(directory, uuid_str)

    # Build it if needs be
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    return dir_name


def get_file_name(directory, uuid_str, galaxy_name, extension):
    """
    Get the file name from the galaxy

    :param directory: the base directory
    :param uuid_str: the uuid string for this task
    :param extension: the extension to be used
    :param galaxy_name: the galaxy name
    :return:
    """
    # Find the name of the directory to use
    dir_name = create_if_necessary(directory, uuid_str)

    # Now we can put a file in it
    return os.path.join(dir_name, galaxy_name + '.' + extension)


def zip_up_files(galaxy_name, file_names, uuid_string):
    """
    Zip all the files up into a file

    :param uuid_string: the UUID string
    :param galaxy_name: the galaxy name
    :param file_names: the files to add
    :return:
    """
    tar_file_name = get_file_name(OUTPUT_DIRECTORY, uuid_string, galaxy_name, 'tar.gz')
    with tarfile.open(tar_file_name, 'w:gz') as tar_file:
        for file_name in file_names:
            tar_file.add(file_name, arcname=os.path.basename(file_name))
            os.remove(file_name)


def check_results(output, path_name):
    """
    Check the output from the command to get a file

    :param output: the text
    :param path_name: the file that should have been written
    :return: True if the files was downloaded correctly
    """
    print('checking file transfer')
    if output.find('HTTP request sent, awaiting response... 200 OK') >= 0 and output.find('Length:') >= 0 and output.find('Saving to:') >= 0 \
            and os.path.exists(path_name) and os.path.getsize(path_name) > 100:
        return True
    return output


def check_failure(output):
    """
    Check the output message for a failure condition

    :param output: the output message
    :return: True if a failure is detected
    """
    print('check_failure - {0}'.format(output))
    if output.find('HTTP request sent, awaiting response... 400 Bad Request') >= 0:
        return True

    return False


def send_email(email, message, galaxy_name):
    """
    Send and email to the user with a message
    :param email: the users email address
    :param message: the message to send the user
    :param galaxy_name: the galaxy name
    :return:
    """

    # Build the message
    print('send_email {0} {1} {2}'.format(email, galaxy_name, message))
    message = MIMEText(message)
    message['Subject'] = galaxy_name
    message['To'] = email
    message['From'] = FROM_EMAIL

    # Send it
    smtp = smtplib.SMTP(SMTP_SERVER)
    smtp.sendmail(FROM_EMAIL, [email], message.as_string())
    smtp.quit()


def get_final_message(galaxy_name, file_names, uuid_string):
    """
    Build the email message to send

    :param uuid_string: the UUID string
    :param galaxy_name: the galaxy name
    :param file_names: the files built
    :return: the built message
    """
    string = 'The files you requested for the galaxy {0} are:\n'.format(galaxy_name)
    for file_name in file_names:
        string += ' * {0}\n'.format(os.path.basename(file_name))
    string += '''
These files have been put in a gzip file called {0}.tar.gz.

The file is available for download from http://ict.icrar.org/skynet-rest/downloads/{1}/.

The file will be available for 5 days and will then be deleted.'''.format(galaxy_name, uuid_string)
    return string


def clean_up_file(galaxy_name, uuid_string):
    """
    Remove the HDF file as it is not needed now
    :param uuid_string: the UUID string
    :param galaxy_name: the galaxy
    :return:
    """
    os.remove(get_file_name(HDF5_DIRECTORY, uuid_string, galaxy_name, 'hdf5'))
    if HDF5_DIRECTORY != OUTPUT_DIRECTORY:
        os.rmdir(os.path.join(HDF5_DIRECTORY, uuid_string))

