import argparse
import os

import lib
import csvgen
import meteo
import gpxgen
import session

import hilight

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", help="directory of gopro LRVs (and MP4s, THMs)")
    parser.add_argument("output_dir", help="directory to dump CSVs")
    # argparse replaces - with _ to avoid having to use e.g. args.__dict__["skip-flatten"]
    parser.add_argument("-sf", "--skip-flatten",
        help="don't combine input files into one output file", action='store_true')
    # DEBUG
    parser.add_argument("-sg", "--skip-gpx",
        help=f"skip generation of gpx files in {lib.GPX_TEMP_DIR}", action='store_true')
    parser.add_argument("-sc", "--skip-csv",
        help=f"skip generation of csv files in {lib.CSV_OUTPUT_DIR}", action='store_true')
    parser.add_argument("-p", "--preserve",
        help=f"preserve {lib.GPX_TEMP_DIR} and files after completion", action='store_true')
    return parser.parse_args()


# this is intentionally shitty pending actually learning to use exiftool
# it's also just a copy of the clustering algorithm session.filter_hilights
# an actually good clustering algorithm would track the ends as well as the starts, AVERY
# this will need to exist in some form post-refactor
# and makes gpxfile a painfully obvious class choice in retrospect
def input_clusters(input_dir):
    class Gpxfile:
        def __init__(self, name):
            self.name = name
            self.gpxname = name.split(".", maxsplit=1)[0] + ".gpx"
            self.segment = gpxgen.parse_segment(self.gpxname)
    
    gpxfiles = sorted([Gpxfile(file) for file in input_dir if file.endswith(".LRV")],
        key=lambda file: file.segment.get_time_bounds()[0])

    clusters = []
    current_cluster = []
    for i, file in enumerate(gpxfiles, start=1):
        current_cluster.append(file.name)
        if i == len(gpxfiles):
            clusters.append(current_cluster)
            break

        if gpxfiles[i].segment.get_time_bounds()[0].timestamp() - file.segment.get_time_bounds()[0].timestamp() > 36000:
            clusters.append(current_cluster)
            current_cluster.clear()

    return clusters


if __name__ == '__main__':
    args = parse_args()
    # currently input_clusters() is generating gpx files. post-refactor it won't be
    # if not args.skip_gpx:
    #     gpxgen.generate_gpxes(args.input_dir)
    if not args.skip_csv:
        csvgen.CSVGenerator(
            args.input_dir, args.output_dir, args.skip_flatten
            ).main()

    sessions = tuple(session.Session(args, cluster) for cluster in input_clusters(os.listdir(args.input_dir)))

    sesh = sessions[0]

    if not args.preserve:
        gpxgen.delete_gpxes()