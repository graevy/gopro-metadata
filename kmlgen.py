import simplekml
import lib
import os


def dump_hilight_clusters(clusters, kmz):
    for cluster in clusters:
        kml = simplekml.Kml()
        time = cluster.center_time.isoformat().replace(":","-") # windows doesn't like colons
        for device,pos in cluster.positions.items():
            if pos is None:
                continue
            kml.newpoint()
            kml.name=f"{device}, {time}"
            kml.coords=[pos.longitude, pos.latitude]
        if kmz:
            os.makedirs(lib.KMZ_OUTPUT_DIR, exist_ok=True)
            kml.savekmz(lib.KMZ_OUTPUT_DIR + os.sep + time + ".kmz")
        else:
            os.makedirs(lib.KML_OUTPUT_DIR, exist_ok=True)
            kml.save(lib.KML_OUTPUT_DIR + os.sep + time + ".kml")
        