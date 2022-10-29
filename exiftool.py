import subprocess
import os

import gpxpy


GPX_FORMAT_FILE = r"gpx.fmt"
GPX_TEMP_DIR = r"gpx_temp_dir/"


def generate_gpxes(gopro_dir, video_ext):
    """creates gpx files from gopro LRVs via exiftool
    """
    if os.path.exists(GPX_TEMP_DIR):
        raise Exception(GPX_TEMP_DIR + " already exists; would be removed; aborting")
    os.makedirs(GPX_TEMP_DIR)
    subprocess.run((
        "exiftool", "-p", GPX_FORMAT_FILE, "-ee", "-ext", video_ext,
        "-w", GPX_TEMP_DIR + r"%f.gpx", gopro_dir
    ))

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