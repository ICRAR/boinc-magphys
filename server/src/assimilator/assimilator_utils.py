"""
Some utilities for the Assimilator
"""

MAGIC_NUMBER = '\x1f\x8b'

def is_gzip(outFile):
    """
    Test if the file is a gzip file by opening it and reading the magic number

    >>> is_gzip('/Users/kevinvinsen/Downloads/boinc-magphys/NGC1209__wu719/NGC1209__wu719_0_0.gzip')
    True
    >>> is_gzip('/Users/kevinvinsen/Downloads/boinc-magphys/NGC1209__wu719/NGC1209__wu719_1_0.gzip')
    True
    >>> is_gzip('/Users/kevinvinsen/Downloads/boinc-magphys/NGC1209__wu719/NGC1209__wu719_0_0')
    False
    >>> is_gzip('/Users/kevinvinsen/Downloads/boinc-magphys/NGC1209__wu719/NGC1209__wu719_1_0')
    False
    >>> is_gzip('/Users/kevinvinsen/Downloads/boinc-magphys/NGC1209__wu719/empty')
    False
    """
    result = False
    f = open(outFile , "rb")
    try:
        bytes = f.read(2)
        if len(bytes) == 2:
            result = bytes == MAGIC_NUMBER
    except IOError:
        pass
    finally:
        f.close()
    return result