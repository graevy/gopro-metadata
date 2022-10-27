import subprocess
import os
import json
import argparse
import csv

import gpxpy

import serials


GOPRO_FILES_DIR = r"/mnt/tmp/DCIM/100GOPRO/"
GPX_FORMAT_FILE = r"/home/a/code/milo/gpx.fmt"
GPX_TEMP_DIR = r"gpx_temp_dir/"
CSV_OUTPUT_DIR = r"/home/a/code/milo/csv/"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="directory of gopro LRVs (and MP4s, THMs)")
    parser.add_argument("output", help="directory to dump CSVs")
    parser.add_argument("-e", "--extension", default='LRV',
        help="file extension for videos. defaults to LRV")
    parser.add_argument("-n", "--newuser",
        help="assign and save unrecognized serial numbers to this name")
    parser.add_argument("-f", "--flatten", help="combine all input segments into one file")
    return parser.parse_args()


def main():
    args = parse_args()

    gopro_dir = args.input
    csv_dir = args.output
    video_ext = args.extension.upper()

    # make directories
    if os.path.exists(GPX_TEMP_DIR):
        raise Exception(GPX_TEMP_DIR + " already exists; would be removed; aborting")
    subprocess.run(("mkdir", "-p", GPX_TEMP_DIR))
    subprocess.run(("mkdir", "-p", csv_dir))

    # run exiftool to generate GPX files (GPX is an XML subset) from video metadata,
    # sourced from gopro "LRV" files:
    # "Low Resolution Video"; it's a renamed MP4 in 240p 30fps
    # (slightly faster for exiftool to process)
    subprocess.run([
        "exiftool", "-p", GPX_FORMAT_FILE, "-ee", "-ext", video_ext,
        "-w", GPX_TEMP_DIR + r"%f.gpx", gopro_dir
    ])

    gopro_serial_numbers = serials.load_serial_map()

    for file in sorted(os.listdir(GPX_TEMP_DIR)):
        # strip extensions
        file = file.rsplit(".",maxsplit=1)[0]
        
        # check the serial number of each video file. my current method is pretty bad
        # note that this is using the filename to check the gopro dir, and not the gpx dir
        serial = serials.get_serial_from_file(gopro_dir + os.sep + file + '.' + video_ext)
        if serial not in gopro_serial_numbers:
            if args.newuser:
                gopro_serial_numbers[serial] = args.newuser
                gopro_user = args.newuser
            else:
                raise Exception(
                    f"""unrecognized gopro serial no {serial} in file {gopro_dir}{os.sep}{file}.{video_ext}
                    try running with -n newuser""")
        else:
            gopro_user = gopro_serial_numbers[serial]

        # gpx data interpretation happens here
        with open(GPX_TEMP_DIR + file + ".gpx") as in_file:
            segment = gpxpy.parse(in_file).tracks[0].segments[0]

        # csv dumping
        csv_subdir = csv_dir + os.sep + gopro_user + os.sep
        os.makedirs(csv_subdir, exist_ok=True)
        with open(csv_subdir + file + ".csv", "w+", newline='') as out_file:
            writer = csv.writer(out_file)

            # we need at least 2 points for speed calculation*
            if len(segment.points) < 3:
                raise Exception(f"gpx file {in_file} needs at least 3 points")
            # track previous point for speed calculation
            previous = segment.points[1]
            for point in segment.points[2:]:
                writer.writerow([
                    point.time,
                    point.elevation,
                    point.latitude,
                    point.longitude,
                    # speed in m/s
                    # gpxpy.gpx.GPXTrackPoint.speed_between(point, previous)
                ])
                previous = point

    # remove gpx files
    # the next step should definitely just stream the gpx files into the csv writer
    subprocess.run(("rm", "-rf", GPX_TEMP_DIR))
    serials.save_serial_map(gopro_serial_numbers)


if __name__ == "__main__": main()


# *
# TODO P3: bug? first csv row has null time and elevation data
# so i just drop the first point..
# this is likely related to exiftool not understanding some metadata:
# "Warning: [Minor] Tag 'Main:gpsaltitude' not defined"
# "Warning: [Minor] Tag 'Main:gpsdatetime' not defined"
# this might also explain why gpxpy isn't populating points' speed fields by default?