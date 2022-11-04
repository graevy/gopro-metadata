import subprocess
import os
import shutil
import gpxpy

import lib


GPX_FORMAT_FILE = "gpx.fmt"
GPX_TEMP_DIR = "gpx_temp_dir" + os.sep


# run exiftool to generate GPX files (GPX is an XML subset) from video metadata,
# sourced from gopro "Low Resolution Video" files: 240p 30fps MP4 w/ identical metadata
# decided not to roll these into a class/map
# TODO P2: pyexiftool integration pls
def generate_gpxes(gopro_dir):
    """creates gpx files from gopro LRVs via exiftool
    """
    # if os.path.exists(GPX_TEMP_DIR):
    #     raise Exception(GPX_TEMP_DIR + " already exists; would be removed; aborting")
    os.makedirs(GPX_TEMP_DIR, exist_ok=True)
    subprocess.run((
        "exiftool", "-p", GPX_FORMAT_FILE, "-ee", "-ext", lib.INPUT_VIDEO_EXT,
        "-w", GPX_TEMP_DIR + r"%f.gpx", gopro_dir
    ))

def delete_gpxes():
    shutil.rmtree(GPX_TEMP_DIR)

def get_gpxes():
    return (file for file in sorted(os.listdir(GPX_TEMP_DIR)))

def parse_segment(file):
    """instantiate gpxpy segment objects from GPX files

    Args:
        file (str): a gpx file created by exiftool

    Returns:
        GPXTrackSegment: to be merged into one Track in main()
    """
    with open(GPX_TEMP_DIR + file) as input:
        return gpxpy.parse(input).tracks[0].segments[0]
