import subprocess
import os
import argparse
import csv

import gpxpy


GOPRO_FILES_DIR = r"/mnt/tmp/DCIM/100GOPRO/"
GPX_FORMAT_FILE = r"/home/a/code/milo/gpx.fmt"
GPX_TEMP_DIR = r"gpx_temp_dir/"
CSV_OUTPUT_DIR = r"/home/a/code/milo/csv/"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="directory of gopro LRVs (and MP4s, THMs)")
    parser.add_argument("output", help="directory to dump CSVs")
    args = parser.parse_args()

    gopro_dir = args.input_dir
    csv_dir = args.output_dir

    # make directories
    subprocess.run(["mkdir", "-p", GPX_TEMP_DIR])
    subprocess.run(["mkdir", "-p", csv_dir])

    # run exiftool to generate GPX files (GPX is an XML subset) from video metadata,
    # sourced from gopro "LRV" files:
    # "Low Resolution Video"; it's a renamed MP4 in 240p 30fps
    # (slightly faster for exiftool to process)
    subprocess.run([
        "exiftool", "-p", GPX_FORMAT_FILE, "-ee", "-ext", "lrv",
        "-w", GPX_TEMP_DIR + r"%f.gpx", gopro_dir
    ])

    for file in sorted(os.listdir(GPX_TEMP_DIR)):
        # strip extensions
        file = file.rsplit(".",maxsplit=1)[0]

        # gpx data extraction
        with open(GPX_TEMP_DIR + file + ".gpx") as in_file:
            segment = gpxpy.parse(in_file).tracks[0].segments[0]

        # csv dumping
        with open(csv_dir + file + ".csv", "w+", newline='') as out_file:
            writer = csv.writer(out_file)

            # we need at least 2 points for speed calculation, but there's a:
            # TODO P3: bug? first csv row has null time and elevation data
            # so i just drop the first point..
            # this is likely related to exiftool not understanding some metadata:
            # "Warning: [Minor] Tag 'Main:gpsaltitude' not defined"
            # "Warning: [Minor] Tag 'Main:gpsdatetime' not defined"
            # this might also explain why gpxpy isn't populating points' speed fields by default?
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
                    gpxpy.gpx.GPXTrackPoint.speed_between(point, previous)
                ])
                previous = point

    # remove gpx files
    # the next step should definitely just stream the gpx files into the csv writer
    subprocess.run(["rm", "-rf", GPX_TEMP_DIR])


if __name__ == "__main__": main()