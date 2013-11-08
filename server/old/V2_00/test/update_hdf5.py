"""

"""
import h5py
from utils.logging_helper import config_logger
import numpy
import time

LOG = config_logger(__name__)

FILENAME = '/tmp/test.hdf5'
DIM = 200
data_type_pixel_histogram = numpy.dtype([
    ('x_axis', float),
    ('hist_value', float),
])


def write():
    start_time = time.time()
    h5_file = h5py.File(FILENAME, 'w')
    group = h5_file.create_group('group')
    data_set = group.create_dataset('data_set', (DIM, DIM), dtype=numpy.float, compression='gzip')
    data_pixel_histograms_list = group.create_dataset('pixel_histograms_list', (DIM,), dtype=data_type_pixel_histogram, compression='gzip', maxshape=(None,))
    for i in range(DIM):
        for j in range(DIM):
            data_set[i, j] = 0.0

    for i in range(DIM):
        data_pixel_histograms_list[i] = (i, i)

    h5_file.close()
    end_time = time.time()
    total_time = end_time - start_time
    LOG.info('Write - Total time %.3f secs', total_time)


def update(x, y):
    start_time = time.time()
    h5_file = h5py.File(FILENAME, 'a')
    group = h5_file['group']
    data_set = group['data_set']
    data_set[x, y] = 1.0

    h5_file.close()
    end_time = time.time()
    total_time = end_time - start_time
    LOG.info('Update - Total time %.3f secs', total_time)

def extend(x):
    start_time = time.time()
    h5_file = h5py.File(FILENAME, 'a')
    group = h5_file['group']
    data_pixel_histograms_list = group['pixel_histograms_list']
    (old_size,) = data_pixel_histograms_list.shape
    data_pixel_histograms_list.resize((old_size + x,))

    for i in range(x):
        data_pixel_histograms_list[old_size + i] = (i,i)

    h5_file.close()
    end_time = time.time()
    total_time = end_time - start_time
    LOG.info('Extend - Total time %.3f secs', total_time)

write()

update(0,0)
update(1,1)
update(2,2)
update(3,3)
update(4,4)
update(5,5)
update(6,6)
update(7,7)

extend(50)
extend(100)
extend(200)
extend(300)
extend(400)
extend(500)
extend(600)
extend(700)
extend(800)
extend(900)
