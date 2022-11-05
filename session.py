import os
import datetime
import gpxpy
import dataclasses
import meteostat

import lib
import serials
import gpxgen
import meteo
import hilight


@dataclasses.dataclass
class MetaTrack:
    user: str
    track: gpxpy.gpx.GPXTrack = gpxpy.gpx.GPXTrack()
    weather: meteostat.Hourly = None
    hilights: list = dataclasses.field(
        default_factory=lambda : []
        )


@dataclasses.dataclass
class HiLight:
    time: datetime.datetime
    user: str


class Session:
    def __init__(self, meta_segments):
        self.users = set(mt.user for mt in meta_segments)

        self.mt_map = {user:MetaTrack(user) for user in self.users}
        self.meta_tracks = tuple(self.mt_map.values())

        # unpack the metasegments into metatracks; attach hilights
        for ms in meta_segments:
            mt = self.mt_map[ms.user]
            mt.track.segments.append(ms.segment)
            mt.hilights.append(ms.hilights)

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

    # if a highlight is within 10s of another highlight, treat them as the same
    # quick and dirty linearithmic
    def filter_hilights(self):
        hilights = sorted(
            (hl for mt in self.meta_tracks for hl in mt.hilights),
            key=lambda hl: hl.time
            )

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
            if hilights[i].time.timestamp() - hl.time.timestamp() > 10:
                clusters.append(current_cluster)
                current_cluster.clear()
        return clusters

    def hilight_reel(self):
        for cluster in self.filter_hilights():
            # TODO P3: naming hell
            cluster_avg_time = datetime.datetime.fromtimestamp(
                sum(hl.time.timestamp() for hl in cluster) / len(cluster),
                # TODO P2: timezone hell
                tz=gpxpy.gpxfield.SimpleTZ("Z")
            )

            locs = tuple(
                mt.track.get_location_at(cluster_avg_time) for mt in self.meta_tracks
                )

            for segment in locs:
                loc_lat  = sum(loc.latitude  for loc in segment) / len(locs)
                loc_long = sum(loc.longitude for loc in segment) / len(locs)
            loc = tuple((loc_lat, loc_long))

            # TODO P1: test
            print(f"""Event at {cluster_avg_time.time()} \
                from {len(cluster)} devices centered at {loc}: """)

            for entry in cluster:
                print(f"""    Device owned by {entry.user} recorded at \
                    {self.mt_map[entry.user].track.get_location_at(cluster_avg_time)}""")

        # sort lowest-to-highest (incl negatives) 3d distance from center of all hilights?
