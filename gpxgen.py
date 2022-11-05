import subprocess
import os
import shutil
import gpxpy
import exiftool

import lib


GPX_FORMAT_FILE = "gpx.fmt"
GPX_TEMP_DIR = "gpx_temp_dir" + os.sep


def parse_segment(file):
    """instantiate gpxpy segment objects from GPX files

    Args:
        file (str): usually an LRV file containing gpx metadata

    Returns:
        GPXTrackSegment: to be merged into one Track
    """
    with exiftool.ExifTool() as et:
        return gpxpy.parse(
            et.execute(
            "-p", GPX_FORMAT_FILE, "-ee", "-ext", lib.INPUT_VIDEO_EXT, file
                )
            )
