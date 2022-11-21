import gpxpy
import exiftool
import dataclasses
import datetime
import llist

import lib
import serials
import hilight


@dataclasses.dataclass
class MetaSegment:
    segment: gpxpy.gpx.GPXTrackSegment
    file: str
    user: str
    start_time: datetime.datetime
    end_time: datetime.datetime
    hilights: list


# TODO P3: can remove llist dependency by truncating segments at bad indexes,
# instead of removing individually bad data

# gopros occasionally spawn incorrect gps data*, so
# delete timestamps before file creation date minus file duration.
# subtract file duration because file creation is tagged
# arbitrarily between start and end time! fun
# also, lat/long/ele can be absurd too
# 0,0,0 coordinates in the middle of the pacific, etc
def sanity_check(file, seg):
    """discards bad gps data

    Args:
        file (str): to source metadata via exiftool from
        seg (GPXTrackSegment): to sanity-check

    Returns:
        GPXTrackSegment: with junk data discarded
    """
    if len(seg.points) == 0:
        print("empty segment passed from:",file)
        return seg
    # grabbing file creation date and duration
    with exiftool.ExifToolHelper() as et:
        tags = et.get_tags(file, ["QuickTime:CreateDate", "QuickTime:Duration"])[0]

    # unfortunately gopro has their own gps format, so convert to valid iso...
    # e.g. 2011:10:09 16:01:35 -> 2011-10-09 16:01:35
    create = tags["QuickTime:CreateDate"].replace(":","-",2)
    create = datetime.datetime.fromisoformat(create).replace(
        # sometimes the gopro corrects for timezone. sometimes it doesn't
        # whenever this bug occurs it's usually years off.
        # i'm picturing an edge case where it doesn't log hour. and we happen
        # to be recording past 4pm PST (00:00 utc)
        # judging by my understanding of the bug, this is fine
        tzinfo=datetime.timezone(datetime.timedelta(hours=8))
        )
    duration = datetime.timedelta(seconds=tags["QuickTime:Duration"])

    # this is our anchor point. timestamps before this must be invalid
    sanity_time = create - duration
    
    # now check for bad timestamps
    for point in seg.points:
        if point.time:
            if point.time < sanity_time:
                point.time = None

            # i have never seen timestamps revert after syncing. break here
            else: break

    # now check for bad locations: if a location is way off avg, discard it
    # use doubly linked list for O(1) removal
    dll = llist.dllist(seg.points)

    # "way off avg" is defined as the diff > the avg lat/long divided by this value,
    # this should work for all cases except supersonic
    # e.g. if avg_lat is 50 and point.latitude is suddenly 60,
    # if abs(50 - 60) > avg_lat/threshold, discard the point
    comparison_threshold = 20

    # remove points with no location or location set to 0,0
    bad_idxes = [idx for idx,point in enumerate(dll)\
        if not point.latitude or not point.longitude]
    
    # (removing a value from the linked list will cancel iteration)
    for idx in bad_idxes:
        dll.remove(dll.nodeat(idx))

    # starting from segment end,
    # compare subsequent points to previous point and remove if bad.
    # this relies on accurate end-of-segment data;
    # gps usually synchronizes during a segment
    # TODO P3: once junk data is identified, stop iterating?
    bad_idxes.clear()
    idx = len(dll) - 1
    prev_lat  = dll.last.value.latitude
    prev_long = dll.last.value.longitude
    for point in reversed(dll):
        idx -= 1
        lat_diff  = point.latitude  - prev_lat
        long_diff = point.longitude - prev_long
        lat_comparator = abs(prev_lat / comparison_threshold)
        long_comparator = abs(prev_long / comparison_threshold)
        if lat_diff > lat_comparator or\
            long_diff > long_comparator:
            bad_idxes.append(idx)
        else:
            prev_lat = point.latitude
            prev_long = point.longitude

    for idx in bad_idxes:
        dll.remove(dll.nodeat(idx))
    
    seg.points = [point for point in dll]

    return seg


def parse_segment(file):
    """instantiate gpxpy segment objects from GPX files

    Args:
        file (str): usually an LRV file containing gpx metadata

    Returns:
        GPXTrackSegment: to be merged into one Track
    """
    with exiftool.ExifTool() as et:
        gpx = gpxpy.parse(
            et.execute(
            "-p", lib.GPX_FORMAT_FILE, "-ee", file
                )
            )

    seg = gpx.tracks[0].segments[0]
    seg = sanity_check(file, seg)
    serial = serials.get_serial_from_file(file)
    start_time, end_time = seg.get_time_bounds()

    hilights = []
    for hl in sorted(hilight.examine_mp4(file)):
        hilights.append(hilight.HiLight(
            # every hilight is just a time float, so adding it to the start time
            # gets the moment it occurred
            time = start_time + datetime.timedelta(seconds=hl),
            user = serial
        ))

    return MetaSegment(seg, file, serial, start_time, end_time, hilights)


# example of gpsdatetime initialization bug
# $ exiftool -ee -G3 -X sample_data/GL010007.LRV | rg -i datetime
#  <Track4:GPSDateTime>2015:10:18 00:00:04.345</Track4:GPSDateTime>
#  <Track4:GPSDateTime>2015:10:23 23:00:45.167</Track4:GPSDateTime>
#  <Track4:GPSDateTime>2015:10:23 23:00:46.185</Track4:GPSDateTime>
#  <Track4:GPSDateTime>2015:10:23 23:00:47.175</Track4:GPSDateTime>
#  <Track4:GPSDateTime>2015:10:23 23:00:48.165</Track4:GPSDateTime>
#  <Track4:GPSDateTime>2015:10:23 23:00:49.155</Track4:GPSDateTime>
#  <Track4:GPSDateTime>2022:11:11 23:00:50.145</Track4:GPSDateTime>
#  <Track4:GPSDateTime>2022:11:11 23:00:51.135</Track4:GPSDateTime>
#  <Track4:GPSDateTime>2022:11:11 23:00:52.125</Track4:GPSDateTime>
#  <Track4:GPSDateTime>2022:11:11 23:00:53.115</Track4:GPSDateTime>
#  <Track4:GPSDateTime>2022:11:11 23:00:54.160</Track4:GPSDateTime>

# judging by timestamps, this gopro took about 6 seconds to sync clocks with a gps network
# rather than simply not log incorrect gps data, the gopro assumes its data is correct?
# because it is partially accurate (to the second, then 10s, then hour, etc)
# just guessing really. smells like race condition
