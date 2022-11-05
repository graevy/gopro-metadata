import argparse
import os

import lib
import csvgen
import gpxgen
import session
import sessionfilter


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", help="directory of gopro LRVs (and MP4s, THMs)")

    parser.add_argument("-csv", "--csv",
        help=f"write csv files in {lib.CSV_OUTPUT_DIR}")
    parser.add_argument("output_dir", help="directory to dump CSVs")

    # argparse replaces - with _ to avoid having to use e.g. args.__dict__["skip-flatten"]
    parser.add_argument("-sf", "--skip-flatten",
        help="don't combine input files into one output file", action='store_true')

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    sessions = sessionfilter.generate_sessions(args)

    if args.csv:
        if args.skip_flatten:
            csvgen.CSVGenerator(
                args.input_dir, args.output_dir, args.skip_flatten
                ).main()

    sesh = sessions[0]