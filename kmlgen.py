import simplekml
import lib
import os


# TODO P2: refactor eventually
# the timestamping is also pretty bad here
def dump_session_hilights(session):
    for cluster in session.group_hilights():
        kml = simplekml.Kml()
        time = cluster.center_time.time().isoformat().replace(":","-") # windows doesn't like colons

        out_dir = lib.KML_OUTPUT_DIR + os.sep
        out_dir += cluster.center_time.date().isoformat() + os.sep
        os.makedirs(out_dir, exist_ok=True)
        out_file = out_dir + time + ".kml"

        for device,pos in cluster.positions.items():
            if pos is None:
                continue
            kml.newpoint(
                name=f"{device}, {time}",
                coords=[(pos.longitude, pos.latitude)]
            )
        kml.save(out_file)
        