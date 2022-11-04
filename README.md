This extracts embedded GPX data inside gopro LRVs via exiftool:
```gpxgen.generate_gpxes(dir, video_ext=".lrv")```
It can convert extracted GPX data from XML to CSV via gpxpy:
```csvgen.CSVGenerator(input, output, newuser=False, skip_flatten=False).main()```
Meteostat integration for weather data:
```meteo.weather_from_gpx(gpx)```



Usage:
- pip install gpxpy
- mount gopro sdcard
- python main.py path/to/gopro/videos csv/dump/dir