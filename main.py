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
        help=f"write csv files in specified dir",
        action='store')

    # argparse replaces - with _ to avoid having to use e.g. args.__dict__["skip-flatten"]
    parser.add_argument("-sf", "--skip-flatten",
        help="don't combine input files into one output file",
        action='store_true')

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    sessions = sessionfilter.generate_sessions(args)

    if args.csv:
        for session in sessions:
            for mt in session.meta_tracks:
                out_dir = lib.CSV_OUTPUT_DIR + os.sep + mt.user + os.sep
                if args.skip_flatten:
                    csvgen.write_csv(
                        points=(point for segment in mt.track.segments for point in segment),
                        out_file=out_dir + mt.get_time_bounds()[0].isoformat() + ".csv",
                        ).main()
                else:
                    for segment in mt.track.segments:
                        csvgen.write_csv(
                            points=segment.points,
                            out_file=out_dir + segment.get_time_bounds()[0].isoformat() + ".csv",
                        )
