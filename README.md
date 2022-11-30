This extracts embedded GPX data inside gopro MP4s/LRVs to dump to CSV, KML, or GPX files


Dependencies:
- gpxpy
- simplekml
- meteostat
- exiftool
- llist

Usage:
- py main.py path/to/gopro/videos [--csv] [--gpx] [--kml]

TODO:
- automate csv -> google maps
- automate some meteostat features
    - smart amount of stations instead of just 10?
- logger instead of stdout?
- test suite with nov 3rd data
- UHF propagation conditions (SFI, KI, AI) would be better than meteostat for this
    - see https://www.dxmaps.com/spots/mapg.php?Lan=E&Frec=430&ML=&Map=NA&HF=&DXC=ING2&GL=
