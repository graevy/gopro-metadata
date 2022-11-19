import os
import lib

import session
import gpxgen


def _same_session(seg_a, seg_b):
    a_start, a_end = (bound.timestamp() for bound in seg_a.get_time_bounds())
    b_start, b_end = (bound.timestamp() for bound in seg_b.get_time_bounds())

    def bounds_close(bound_a, bound_b):
        # i pegged sessions at about 5 hours difference (18k seconds)
        return True if abs(bound_a - bound_b < 18000) else False

    # if either of the time endpoints are close, they belong to the same session
    if \
    bounds_close(a_start, b_start) or \
    bounds_close(a_start, b_end) or \
    bounds_close(a_end, b_start) or \
    bounds_close(a_end, b_end):
        return True
    else:
        return False

def generate_sessions(args):
    # firstly, filter and process files
    path = args.input_dir + os.sep
    meta_segments = sorted((
        gpxgen.parse_segment(path + file) for file in os.listdir(path)\
            if file.endswith(lib.INPUT_VIDEO_EXT)
        ),
        key=lambda ms: ms.start_time
    )


    if len(meta_segments) < 1:
        print(f"no {lib.INPUT_VIDEO_EXT} files in {args.input_dir}")
        return []

    # secondly, sort them into sessions
    sessions = []
    current_session = []
    for i, ms in enumerate(meta_segments, start=1):
        current_session.append(ms)
        # if this is the last array element, finish
        if i == len(meta_segments):
            sessions.append(current_session)
            break

        if not _same_session(meta_segments[i].segment, ms.segment):
            sessions.append(current_session)
            current_session = []

    # instantiate the sessions:
    sessions = [session.Session(s) for s in sessions]

    # lastly, each session should have 1 track per user
    # this is probably best left to the session constructor
    return sessions