"""
Initialise the Constants used
"""

import re

# The file bands in wavelength order - the order IS VERY IMPORTANT
FILTER_BANDS = [
    'GALEXFUV',  # 00
    'GALEXNUV',  # 01
    'SDSSu',     # 02
    'SDSSg',     # 03
    'SDSSr',     # 04
    'SDSSi',     # 05
    'SDSSz',     # 06
    'WISEW1',    # 07
    'WISEW2',    # 08
    'WISEW3',    # 09
    'WISEW4',    # 10
    ]

INFRARED_BANDS = {
    'WISEW1': 7,
    'WISEW2': 8,
    'WISEW3': 9,
    'WISEW4': 10,
}

OPTICAL_BANDS = {
    'SDSSu': 2,
    'SDSSg': 3,
    'SDSSr': 4,
    'SDSSi': 5,
    'SDSSz': 6,
}

ULTRAVIOLET_BANDS = {
    'GALEXFUV': 0,
    'GALEXNUV': 1,
}

HEADER_PATTERNS = [re.compile('CDELT[0-9]+'),
                   re.compile('CROTA[0-9]+'),
                   re.compile('CRPIX[0-9]+'),
                   re.compile('CRVAL[0-9]+'),
                   re.compile('CTYPE[0-9]+'),
                   re.compile('EQUINOX'),
                   re.compile('EPOCH'),
                   re.compile('RA_CENT'),
                   re.compile('DEC_CENT'),
                   ]
