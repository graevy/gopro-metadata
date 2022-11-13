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
    start_time: datetime.datetime
    end_time: datetime.datetime
    hilights: tuple


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
        # print("close!")
        return True
    else:
        # print("far!")
        return False

def generate_sessions(args):
    # firstly, filter and process files
    meta_segments = []
    for file in os.listdir(args.input_dir):
        if file.endswith(lib.INPUT_VIDEO_EXT):
            path = args.input_dir + os.sep + file
            user = serials.get_serial_from_file(path)
            segment = gpxgen.parse_segment(path).tracks[0].segments[0]
            start_time, end_time = segment.get_time_bounds()

            hilights = tuple(
                hilight.HiLight(
                    # every hilight is just a time float, so adding it to the start time
                    # gets the moment it occurred
                    # maybe unnecessary to work with absolute time?
                    time = start_time + datetime.timedelta(seconds=hl),
                    user = user
                    ) for hl in sorted(
                hilight.examine_mp4(path)
                    )
            )

            meta_segments.append(
                MetaSegment(
                    file, path, user, segment, start_time, end_time, hilights
                )
            )

    meta_segments.sort(key=lambda ms: ms.start_time)

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