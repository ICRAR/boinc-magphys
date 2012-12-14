"""

"""
import h5py
import logging
import numpy
import time

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)

FILENAME = '/tmp/test.hdf5'
DIM = 100

def write():
    start_time = time.time()
    h5_file = h5py.File(FILENAME, 'w')
    group = h5_file.create_group('group')
    data_set = group.create_dataset('data_set', (DIM, DIM), dtype=numpy.float, compression='gzip')
    for i in range(DIM):
        for j in range(DIM):
            data_set[i, j] = 0.0

    h5_file.close()
    end_time = time.time()
    total_time = end_time - start_time
    LOG.info('Total time %.3f secs', total_time)


def update(x, y):
    start_time = time.time()
    h5_file = h5py.File(FILENAME, 'a')
    group = h5_file['group']
    data_set = group['data_set']
    data_set[x, y] = 1.0

    h5_file.close()
    end_time = time.time()
    total_time = end_time - start_time
    LOG.info('Total time %.3f secs', total_time)

write()

update(0,0)
update(1,1)
update(2,2)
update(3,3)
update(4,4)
update(5,5)
update(6,6)
update(7,7)
