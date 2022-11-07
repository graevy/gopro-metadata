import os
import csv


def write_csv(points, out_file):
    """given iterable<GPXTrackPoint>, write csv to specified path

    Args:
        points (iterable<GPXTrackPoint>): written, separated by newline
        gopro_user (str): user associated with a gopro
        out_file (str): name the .csv (no extension)
    """
    os.makedirs(out_file.rsplit(os.sep, maxsplit=1)[0], exist_ok=True)
    with open(out_file, "w+", newline='') as out_file:
        writer = csv.writer(out_file)

        # first point is skipped because of exiftool bug
        for point in points[1:]:
            writer.writerow([
                point.latitude,
                point.longitude,
                point.elevation,
                point.time
            ])


# *
# TODO P3: first csv row has null time and elevation data
# so i just drop the first point..
# this is likely related to exiftool not understanding some metadata:
# "Warning: [Minor] Tag 'Main:gpsaltitude' not defined"
# "Warning: [Minor] Tag 'Main:gpsdatetime' not defined"
