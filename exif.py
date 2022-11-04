import exiftool
import os

import lib
import gpxgen
import hilight

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

d = 'backup_sample_data/oct26/alex/'
files = [d+file for file in os.listdir(d)]

# with exiftool.ExifToolHelper() as et:
#     for file in files:
#         print(et.get_tags(file, 'QuickTime:CameraSerialNumber')[0]['QuickTime:CameraSerialNumber'])
for file in files:
    print(exiftool.ExifToolHelper(logger=logger).get_metadata(file))

# print(hilight.main(files))