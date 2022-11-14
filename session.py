import datetime
import gpxpy
import dataclasses
import meteostat
import typing

import meteo


@dataclasses.dataclass
class MetaTrack:
    user: str
    track: gpxpy.gpx.GPXTrack
    files: list
    weather: typing.Optional[meteostat.Hourly] = None
    hilights: list = dataclasses.field(
        default_factory=lambda : []
        ) 


@dataclasses.dataclass
class HiLight:
    time: datetime.datetime
    user: str
    location: gpxpy.gpx.GPXTrackPoint


@dataclasses.dataclass
class HiLightCluster:
    entries: tuple
    center_time: datetime.datetime
    center_pos: gpxpy.gpx.GPXTrackPoint
    humidity: typing.Optional[float]
    temperature: typing.Optional[float]


class Session:
    def __init__(self, meta_segments):
        self.users = set(mt.user for mt in meta_segments)

        self.mt_map = {
            user:MetaTrack(
                user=user, track=gpxpy.gpx.GPXTrack(), files=[]
            ) for user in self.users
        }
        self.meta_tracks = tuple(self.mt_map.values())

        # unpack the metasegments into metatracks; attach hilights
        for ms in meta_segments:
            mt = self.mt_map[ms.user]
            mt.track.segments.append(ms.segment)
            mt.files.append(ms.file)
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

    def get_time_bounds(self):
        return (self.t_0, self.t_f)

    def locations_at_time(self, time):
        return tuple(mt.track.get_location_at(time) for mt in self.meta_tracks)

    # if a highlight is within 10s of another highlight, treat them as the same
    # quick and dirty linearithmic
    def _filter_hilights(self):
        """groups hilights into clusters more than 10s apart

        Returns:
            list[list[hilight]]: of clusters
        """
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
        for cluster in self._filter_hilights():
            # TODO P3: naming hell
            cluster_avg_time = datetime.datetime.fromtimestamp(
                sum(hl.time.timestamp() for hl in cluster) / len(cluster),
                # TODO P2: timezone hell
                tz=gpxpy.gpxfield.SimpleTZ("Z")
            )

            loc_map = {
                mt.user:\
                mt.track.get_location_at(cluster_avg_time)\
                for mt in self.meta_tracks
            }

            center_lat, center_long, center_ele = 0, 0, 0
            for point in loc_map.values():
                for loc in point:
                    center_lat += loc.latitude
                    center_long += loc.longitude
                    center_ele += loc.elevation
            center_lat /= len(loc_map)
            center_long /= len(loc_map)
            center_ele /= len(loc_map)

            center = tuple((center_lat, center_long, center_ele))

            # TODO P1: test
            print(f"""Event at {cluster_avg_time.time()} \
                from {len(cluster)} devices centered at {center}: """)

            for entry in cluster:
                lat_offset  = entry.latitude  - center.latitude
                long_offset = entry.longitude - center.longitude
                ele_offset  = entry.elevation - center.elevation
                dist_from_center = (
                    lat_offset  ** 2 +\
                    long_offset ** 2 +\
                    ele_offset ** 2
                ) ** (1/2)

                print(f"""    User {entry.user} recorded {dist_from_center} from center: \
                    {lat_offset} ΔLat., {long_offset} ΔLong., {ele_offset} ΔElev.""")
