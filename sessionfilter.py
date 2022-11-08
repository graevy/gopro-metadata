import os
import lib
import dataclasses
import gpxpy
import datetime

import session
import gpxgen
import serials
import hilight


@dataclasses.dataclass
class MetaSegment:
    name: str
    path: str
    user: str
    segment: gpxpy.gpx.GPXTrackSegment
    hilights: tuple


def _same_session(seg_a, seg_b):
    a_start, a_end = (bound.timestamp() for bound in seg_a.get_time_bounds())
    b_start, b_end = (bound.timestamp() for bound in seg_b.get_time_bounds())

    def bounds_close(bound_a, bound_b):
        # i pegged sessions at about 5 hours difference (18k seconds)
        return True if abs(bound_a - bound_b < 18000) else False

    # if either of the endpoints are close, they belong to the same session
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
    meta_segments = []
    for file in os.listdir(args.input_dir):
        if file.endswith(lib.INPUT_VIDEO_EXT):
            name = file
            path = args.input_dir + os.sep + file
            user = serials.check_file(path)
            segment = gpxgen.parse_segment(path).tracks[0].segments[0]
            start_time = segment.points[0].time
            hilights = tuple(
                hilight.HiLight(
                    time = start_time + datetime.timedelta(seconds=hl),
                    user = user
                    ) for hl in sorted(
                hilight.examine_mp4(path)
                    )
            )

            meta_segments.append(
                MetaSegment(
                    name, path, user, segment, hilights
                )
            )

    if len(meta_segments) < 1:
        print(f"no {lib.INPUT_VIDEO_EXT} files in {args.input_dir}")
        return []

    # secondly, sort them into sessions
    sessions = []
    current_session = []
    for i, ms in enumerate(meta_segments, start=1):
        current_session.append(ms)
        if i == len(meta_segments):
            sessions.append(current_session)
            break

        if _same_session(meta_segments[i].segment, ms.segment):
            sessions.append(current_session)
            current_session.clear()

    # instantiate the sessions:
    sessions = [session.Session(s) for s in sessions]

    # lastly, each session should have 1 track per user
    # this is probably best left to the session constructor
    return sessions