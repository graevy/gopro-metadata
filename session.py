import os
import datetime
import gpxpy.gpx as gpx
import dataclasses
from gpxpy.gpxfield import SimpleTZ
import meteostat

import lib
import serials
import gpxgen
import meteo
import hilight


@dataclasses.dataclass
class MetaTrack:
    user: str
    track: gpx.GPXTrack = gpx.GPXTrack()
    weather: meteostat.Hourly = None
    hilights: list = dataclasses.field(default_factory=lambda : [])


@dataclasses.dataclass
class HiLight:
    time: datetime.datetime
    user: str


# TODO P2: i think session should just take a file list, and session should be
# handled by something that automatically determines what a session is --
# most likely, files grouped with e.g. > 10 hours difference between them
# it's unrealistic to expect everyone to not accidentally upload old gopro videos
class Session:
    def __init__(self, args, files):
        self.input_dir = args.input_dir
        self.output_dir = args.output_dir

        input_files = files

        # assemble a set of unique gopro users
        self.users = set(serials.check_file(args.input_dir + os.sep + file) for file in input_files)
        # each user gets a track
        self.mt_map = {user:MetaTrack(user) for user in self.users}
        self.meta_tracks = tuple(self.mt_map.values())

        # each gopro file is a segment, belonging to a user's track
        # the segments must be loaded into that track
        # each file also contains gopro hilights, which represent user timestamps
        for file in input_files:
            if file.endswith(lib.INPUT_VIDEO_EXT):
                abs_path = args.input_dir + os.sep + file
                user = serials.check_file(abs_path)
                mt = self.mt_map[user]
                file_no_ext = file.split(".", maxsplit=1)[0]
                segment = gpxgen.parse_segment(file_no_ext + ".gpx")
                mt.track.segments.append(segment)

                # attach any corresponding gopro hilights
                # the hilight code is so awful i don't want to touch it
                # i'm just datetiming its output here
                t_0 = segment.get_time_bounds()[0]
                mt.hilights.extend(
                    HiLight(
                        t_0 + datetime.timedelta(seconds=hl), user
                    ) for hl in sorted(
                        hilight.examine_mp4(abs_path)
                        )
                    )

        # session weather needs the earliest and last track times
        if len(self.meta_tracks) < 1:
            raise Exception("session instantiated with zero tracks")
        self.t_0, self.t_f = self.meta_tracks[0].track.get_time_bounds()
        if len(self.meta_tracks) > 1:
            for mt in self.meta_tracks:
                t_min, t_max = mt.track.get_time_bounds()
                if t_min < self.t_0:
                    self.t_0 = t_min
                if t_max > self.t_f:
                    self.t_f = t_max
                print(f"considered: min {t_min}, max {t_max}")
                print(f"current: min {self.t_0}, max {self.t_f}")

        # center of the edges of the session
        center_latitude = sum(mt.track.get_center().latitude for mt in self.meta_tracks) \
            / len(self.meta_tracks)
        center_longitude = sum(mt.track.get_center().longitude for mt in self.meta_tracks) \
            / len(self.meta_tracks)
        self.center = (center_latitude, center_longitude)

        # weather
        try:
            self.weather = meteo.weather_from_data(
                center_latitude, center_longitude, self.t_0, self.t_f
                )
        except:
            self.weather = None
            print("didn't connect to weather service")
        
    def locations_at_time(self, time):
        return tuple(mt.track.get_location_at(time) for mt in self.meta_tracks)

    # TODO: P1
    def weather_at_time(self, time): pass

    # if a highlight is within 15 seconds of another highlight, treat them as the same
    # quick and dirty linearithmic
    # return clusters: [[datetime.datetime(hilight)]]
    def filter_hilights(self):
        # hilights need a custom hashing function that chunks them into discrete intervals
        # this will have to do
        hilights = sorted((hl for track in self.meta_tracks for hl in track.hilights),
            key=lambda hl: hl.time)
        if not hilights:
            print("no highlights to filter")
            return []

        clusters = []
        current_cluster = []
        for i, hl in enumerate(hilights, start=1):
            current_cluster.append(hl)
            if i == len(hilights):
                clusters.append(current_cluster)
                break
            if hilights[i].time.second - hl.time.second > 10:
                clusters.append(current_cluster)
                current_cluster.clear()

        return clusters

    def hilight_reel(self):
        for cluster in self.filter_hilights():
            # TODO P3: naming hell
            cluster_avg_time = datetime.datetime.fromtimestamp(
                sum(hl.time.timestamp() for hl in cluster) / len(cluster),
                # TODO P2: timezone hell
                tz=SimpleTZ("Z")
            )

            locs = tuple(mt.track.get_location_at(cluster_avg_time) for mt in self.meta_tracks)
            for segment in locs:
                loc_lat  = sum(loc.latitude  for loc in segment) / len(locs)
                loc_long = sum(loc.longitude for loc in segment) / len(locs)
            loc = tuple((loc_lat, loc_long))
            # TODO P1: test
            print(f"""Event at {cluster_avg_time.time()} from {len(cluster)} devices centered at {loc}: """)
            for entry in cluster:
                print(f"""    Device owned by {entry.user} recorded at {self.mt_map[entry.user].track.get_location_at(cluster_avg_time)}""")
        # sort lowest-to-highest (incl negatives) 3d distance from center of all hilights?


