import gpxgen


class TrackTracker:
    def __init__(self):
        self.track = gpxgen.new_track()
        for file in gpxgen.get_gpxes():
            segment = gpxgen.parse_segment(file)
            # while we're inside this loop, populate track
            self.track.segments.append(segment)

    