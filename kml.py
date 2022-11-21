import simplekml
import os

def generate_kmls(session):
    kml = simplekml.Kml()
    for mt in session.meta_tracks:
        line = kml.newlinestring(
            name=mt.user,
            coords=(point for segment in mt.track.segments for point in segment)
        )

def dump_hilight_clusters(clusters):
    for cluster in clusters:
        kml = simplekml.Kml()
        for device,pos in cluster.positions.items():
            simplekml.Point
            kml.newpoint(name=device, coords=[pos.latitude, pos.longitude])
        