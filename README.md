This extracts embedded GPX data inside gopro LRVs via exiftool,

Converts extracted GPX data from XML to CSV via gpxpy,

Weather data correlation via meteostat integration


Dependencies (via pip):
- gpxpy
- meteostat
- exiftool

Usage:
- mount gopro sdcard
- python -i main.py path/to/gopro/videos [-c] [-o DIR]

TODO:
- automate csv -> google maps
- session & filter documentation
    - session hilight features? feels like a dead end; no hilight annotation
- automate some meteostat features
    - smart amount of stations instead of just 10?
- logger instead of stdout?
- test suite with nov 3rd data
- UHF propagation conditions (SFI, KI, AI) would be better than meteostat for this
    - see https://www.dxmaps.com/spots/mapg.php?Lan=E&Frec=430&ML=&Map=NA&HF=&DXC=ING2&GL=