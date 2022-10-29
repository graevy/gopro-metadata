import os
import argparse
import csv

import gpxgen
import serials


GPX_FORMAT_FILE = r"gpx.fmt"
GPX_TEMP_DIR = r"gpx_temp_dir/"
CSV_OUTPUT_DIR = r"csv/"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="directory of gopro LRVs (and MP4s, THMs)")
    parser.add_argument("output", help="directory to dump CSVs")
    parser.add_argument("-e", "--extension", default='LRV',
        help="file extension for videos. defaults to LRV")
    parser.add_argument("-n", "--newuser",
        help="assign and save unrecognized serial numbers to this name")
    # argparse replaces - with _ to avoid having to use e.g. args.__dict__["skip-flatten"]
    parser.add_argument("-sf", "--skip-flatten",
        help="don't combine input files into one file", action='store_true')
    return parser.parse_args()


class CSVGenerator:
    def __init__(self):
        self.args = parse_args()
        self.gopro_dir = self.args.input + os.sep
        self.csv_dir = self.args.output + os.sep
        self.video_ext = self.args.extension.upper()
        self.gopro_serials = serials.load_serial_map()
    
    # TODO P3: bad name
    def get_serial(self, file):
        """rips serial metadata from LRVs
        """
        serial = serials.get_serial_from_file(file)
        if serial not in self.gopro_serials:
            if self.args.newuser:
                self.gopro_serials[serial] = self.args.newuser
                self.serial_map_updated = True
                return self.args.newuser
            else:
                raise Exception(
                    f"""unrecognized gopro serial no {serial}. use -n newuser?""")
        else:
            self.serial_map_updated = False
            return self.gopro_serials[serial]

    def write_csv(self, points, gopro_user, out_file):
        """given iterable<GPXTrackPoint>, write csv to specified path

        Args:
            points (iterable<GPXTrackPoint>): time, elevation, latitude, longitude
            gopro_user (str): user associated with a gopro
            out_file (str): name the .csv (no extension)
        """
        csv_subdir = self.csv_dir + gopro_user + os.sep
        os.makedirs(csv_subdir, exist_ok=True)
        with open(csv_subdir + out_file + ".csv", "w+", newline='') as out_file:
            writer = csv.writer(out_file)

            for point in points[1:]:
                writer.writerow([
                    point.time,
                    point.elevation,
                    point.latitude,
                    point.longitude,
                ])

    def main(self):
        os.makedirs(self.csv_dir, exist_ok=True)

        gpxgen.generate_gpxes(self.gopro_dir, self.video_ext)

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
            gopro_user = self.get_serial(self.gopro_dir + file + '.' + self.video_ext)

            if len(segment.points) < 3:
                # sometimes the gopro generates tiny segments
                # TODO P3: delete tiny segments w/ confirmation
                raise Exception(f"gpx file {file} needs at least 2 points")

            if self.args.skip_flatten:
                self.write_csv(segment.points, gopro_user, file)
            else:
                points.extend(segment.points)

        if not self.args.skip_flatten:
            self.write_csv(points, gopro_user, "out")


        # cleanup:
        # - remove gpx files
        # - save the serial map if it updated
        # TODO P2: stream the gpx files into the csv writer
        gpxgen.delete_gpxes()
        if self.serial_map_updated:
            serials.save_serial_map(self.gopro_serial_numbers)


if __name__ == "__main__":
    CSVGenerator().main()


# *
# TODO P3: bug? first csv row has null time and elevation data
# so i just drop the first point..
# this is likely related to exiftool not understanding some metadata:
# "Warning: [Minor] Tag 'Main:gpsaltitude' not defined"
# "Warning: [Minor] Tag 'Main:gpsdatetime' not defined"
# this might also explain why gpxpy isn't populating points' speed fields by default?