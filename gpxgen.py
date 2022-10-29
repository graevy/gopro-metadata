# this exists as an interface between gpxpy and the rest of the package

import subprocess
import os

import gpxpy


GPX_FORMAT_FILE = r"gpx.fmt"
GPX_TEMP_DIR = r"gpx_temp_dir/"


# run exiftool to generate GPX files (GPX is an XML subset) from video metadata,
# sourced from gopro "Low Resolution Video" files: 240p 30fps MP4 w/ identical metadata
# decided not to roll these into a class/map
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

def delete_gpxes():
    # TODO P3: might want to use shutil for this? rm -rf has me uneasy
    subprocess.run(("rm", "-rf", GPX_TEMP_DIR))

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

def new_track():
    return gpxpy.gpx.GPXTrack()