import os
import csv

import lib
import gpxgen
import serials


class CSVGenerator:
    def __init__(self, input, output, skip_flatten):
        self.input = input
        self.output = output
        self.skip_flatten = skip_flatten

        self.gopro_dir = self.input + os.sep
        self.csv_dir = self.output + os.sep

    def write_csv(self, points, gopro_user, out_file):
        """given iterable<GPXTrackPoint>, write csv to specified path

        Args:
            points (iterable<GPXTrackPoint>): latitude, longitude, elevation, time
            gopro_user (str): user associated with a gopro
            out_file (str): name the .csv (no extension)
        """
        csv_subdir = self.csv_dir + gopro_user + os.sep
        os.makedirs(csv_subdir, exist_ok=True)
        with open(csv_subdir + out_file + ".csv", "w+", newline='') as out_file:
            writer = csv.writer(out_file)

            # first point is skipped because of exiftool bug
            for point in points[1:]:
                writer.writerow([
                    point.latitude,
                    point.longitude,
                    point.elevation,
                    point.time
                ])

    def main(self):
        os.makedirs(self.csv_dir, exist_ok=True)

        # prepare gpx segments to call write_csv with
        # this is a fucking mess because of the exiftool bug*
        # and maybe skip-flatten is unnecessary
        # i refactored this 4 times and it still feels like it should be broken up more
        points = []
        for file in gpxgen.get_gpxes():
            segment = gpxgen.parse_segment(file)
            # strip file extension because this string is going to be used to both
            # name the output .csv file, and grab the gopro serial
            file = file.rsplit(".")[0]
            gopro_user = serials.check_file(self.gopro_dir + file + "." + lib.INPUT_VIDEO_EXT)

            if len(segment.points) < 3:
                # sometimes the gopro generates tiny segments
                # TODO P3: delete tiny segments w/ confirmation
                raise Exception(f"gpx file {file} needs at least 2 points")

            if self.skip_flatten:
                self.write_csv(segment.points, gopro_user, file)
            else:
                points.extend(segment.points)

        if not self.skip_flatten:
            self.write_csv(points, gopro_user, "out")

        # TODO P2: if --preserve, stream the gpx files into the csv writer?
        # probably via exiftool piping wizardry


# *
# TODO P3: first csv row has null time and elevation data
# so i just drop the first point..
# this is likely related to exiftool not understanding some metadata:
# "Warning: [Minor] Tag 'Main:gpsaltitude' not defined"
# "Warning: [Minor] Tag 'Main:gpsdatetime' not defined"
