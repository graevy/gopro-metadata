import argparse
from os import sep

import lib
import csvgen
import session
import sessionfilter


def parse_args():
    """collects cli args

    Returns:
        argparse.ArgumentParser: with args represented as class fields
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", help="directory of gopro LRVs (and MP4s, THMs)")

    parser.add_argument("-c", "--csv",
        help=f"write csv files in {lib.CSV_OUTPUT_DIR}",
        action='store_true')
    parser.add_argument("-o", "--output-dir",
        help=f"force a non-default csv write dir",
        action='store')

    # argparse replaces - with _ to avoid having to use e.g. args.__dict__["skip-flatten"]
    parser.add_argument("-sf", "--skip-flatten",
        help="don't combine track segments into one output csv",
        action='store_true')

    return parser.parse_args()


if __name__ == '__main__':
    # collect args
    args = parse_args()

    # filter all the input videos into sessions based on their start and end times
    sessions = sessionfilter.generate_sessions(args)

    # for convenience
    mts = [mt for session in sessions for mt in session.meta_tracks]

    # csv dumping. awkward with all the conditional args
    if args.csv:
        root = args.output_dir if args.output_dir else lib.CSV_OUTPUT_DIR
        for session in sessions:
            for mt in session.meta_tracks:
                out_dir = root + sep + mt.user + sep
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

    sessions[0].hilight_reel()
