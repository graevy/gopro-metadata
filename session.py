import datetime
import gpxpy
import dataclasses
from typing import Optional

import meteo


class MetaTrack:
    def __init__(self, user, meta_segments):
        self.user = user
        self.track = gpxpy.gpx.GPXTrack()
        self.files = []
        self.hilights = []
        for ms in meta_segments:
            self.track.segments.append(ms.segment)
            self.files.append(ms.file)
            self.hilights.extend(ms.hilights)
            if ms.user != user:
                raise Exception(f"{ms.user} is not {user}, but is in same MetaTrack")

        self.start_time, self.end_time = self.track.get_time_bounds()

    # the GPXTrack.get_location_at method is incomplete. it doesn't return a location
    # and it doesn't approximate location from nearby points
    # it doesn't need to be Ω(points) either
    # TODO P3: submit another gpxpy pr if the first is merged
    def get_location_at(self, time) -> Optional[gpxpy.gpx.GPXTrackPoint]:

        # not sure which time type i want yet
        if type(time) in (int, float):
            time = self.start_time + datetime.timedelta(seconds=time)

        if time < self.start_time or time > self.end_time:
            return None

        # determine which segment to inspect for location
        # time could also be between segments;
        # track the end of the previous segment and the bounds of the current segment
        for segment in self.track.segments:
            seg_start, seg_end = segment.get_time_bounds()
            # case: the time is inside this segment and we're done
            if seg_start <= time <= seg_end:
                points = segment.points
                break
            # case: the time is before the current segment
            # this should never trigger during the first seg
            if time < seg_start:
                return None

        # search the segment to find which points surround time
        # TODO P2: redo this with binary search, approx location
        for point in points:
            if point.time and point.time >= time:
                return point


@dataclasses.dataclass
class HiLightCluster:
    hilights: tuple
    center_time: datetime.datetime
    positions: dict[str:gpxpy.gpx.GPXTrackPoint]
    center_pos: gpxpy.gpx.GPXTrackPoint
    humidity: Optional[float]
    temperature: Optional[float]


class Session:
    def __init__(self, meta_segments):
        self.users = set(ms.user for ms in meta_segments)

        seg_map = {user:[] for user in self.users}
        for ms in meta_segments:
            seg_map[ms.user].append(ms)

        self.meta_tracks = [
            MetaTrack(user, segs) for user, segs in seg_map.items()
        ]

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
        center_latitude  = 0
        center_longitude = 0
        for mt in self.meta_tracks:
            center = mt.track.get_center()
            center_latitude  += center.latitude
            center_longitude += center.longitude
        center_latitude  /= len(self.meta_tracks)
        center_longitude /= len(self.meta_tracks)
        self.center = (center_latitude, center_longitude)

        # weather
        try:
            self.weather = meteo.weather_from_data(
                center_latitude, center_longitude, self.t_0, self.t_f
                )
        except:
            self.weather = None
            print("Failed to connect to weather service")

    def get_time_bounds(self) -> tuple:
        return (self.t_0, self.t_f)

    def locations_at_time(self, time) -> tuple:
        return tuple(mt.track.get_location_at(time) for mt in self.meta_tracks)

    # if a highlight is within 10s of another highlight, treat them as the same
    # quick and dirty linearithmic
    def group_hilights(self) -> list[HiLightCluster]:
        """groups hilights into clusters more than 10s apart

        Returns:
            HiLightCluster
        """
        hilights = sorted(
            (hl for mt in self.meta_tracks for hl in mt.hilights),
            key=lambda hl: hl.time
            )

        if not hilights:
            print("no highlights to filter")
            return []

        # grouping algorithm. if the next hilight is more than 10s from current, split them
        clusters = []
        current_cluster = []
        for idx, hl in enumerate(hilights, start=1):
            current_cluster.append(hl)
            if idx == len(hilights):
                clusters.append(current_cluster)
                break
            if hilights[idx].time.timestamp() - hl.time.timestamp() > 10:
                clusters.append(current_cluster)
                current_cluster = []

        for idx,cluster in enumerate(clusters):

            # get avg time
            center_time=datetime.datetime.fromtimestamp(
                sum(hl.time.timestamp() for hl in cluster) / len(cluster),
                tz=gpxpy.gpxfield.SimpleTZ("Z")
            )

            # get avg location:
            # get each gopro location at center time
            locs = {mt.user:mt.get_location_at(center_time) for mt in self.meta_tracks}

            # average them
            filtered_locs = tuple(filter(None, locs.values()))
            center_lat, center_long = 0,0
            for loc in filtered_locs:
                center_lat += loc.latitude
                center_long += loc.longitude
            center_pos = gpxpy.gpx.GPXTrackPoint(
                latitude=center_lat / len(filtered_locs),
                longitude=center_long / len(filtered_locs)
            )

            clusters[idx] = HiLightCluster(
                hilights=cluster,
                center_time=center_time,
                positions=locs,
                center_pos=center_pos,
                humidity=None,
                temperature=None
            )

        return clusters
                
    def hilight_reel(self):
        for cluster in self.group_hilights():

            center = cluster.center_pos
            print(
f"Event at {cluster.center_time.time()} centered at {center.latitude}, {center.longitude}:"
            )
            for device,loc in cluster.positions.items():
                if loc is not None:
                    print(f"""    Device {device} @ {gpxpy.geo.haversine_distance(
                        center.latitude, center.longitude, loc.latitude, loc.longitude)}""")


#             # map of user:position during each cluster event
#             loc_map = {}
#             for mt in self.meta_tracks:
#                 loc = mt.get_location_at(cluster_avg_time)
#                 if loc is not None:
#                     loc_map[mt.user] = loc

#             # getting the mean position of all gopros in this cluster
#             # center = mt.get_center_from_locations(loc_map.values())
#             center_lat, center_long, center_ele = 0,0,0
#             for gopro in loc_map.values():
#                 center_lat  += gopro.latitude
#                 center_long += gopro.longitude
#                 center_ele  += gopro.elevation

#             center = gpxpy.gpx.GPXTrackPoint(
#                 latitude  = center_lat,
#                 longitude = center_long,
#                 elevation = center_ele
#             )

#             for entry in cluster:
#                 loc = loc_map[entry.user]
#                 lat_offset  = loc.latitude  - center.latitude
#                 long_offset = loc.longitude - center.longitude
#                 ele_offset  = loc.elevation - center.elevation

#                 dist_from_center = (
#                     lat_offset  ** 2 +\
#                     long_offset ** 2 +\
#                     ele_offset ** 2
#                 ) ** (1/2)

#                 print(f"""    User {entry.user} recorded {dist_from_center} from center:
# {lat_offset} ΔLat., {long_offset} ΔLong., {ele_offset} ΔElev.\n""")