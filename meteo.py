from datetime import tzinfo
import meteostat


def weather_from_data(latitude, longitude, start_time, end_time):
    stations = meteostat.Stations().nearby(latitude, longitude).fetch(10)

    # these gpxs are generated with timezone data that has to be discarded
    # alternatively, timezone data could be added, but pytz specifies
    # that localization should occur at-viewing, like a quantum state
    start_time = start_time.replace(tzinfo=None)
    end_time = end_time.replace(tzinfo=None)

    report = meteostat.Hourly(stations, start_time, end_time)
    if report._data.empty:
        print(f"Warning: Empty dataframe from {start_time} until {end_time}")
        return report
    return report.normalize().fetch()

def weather_from_gpx(gpx, owner):
    bounds = gpx.get_bounds()
    stations = meteostat.Stations().nearby(
        (bounds.max_latitude + bounds.min_latitude) / 2,
        (bounds.max_longitude + bounds.min_longitude) / 2
    ).fetch(10)

    start, end = gpx.get_time_bounds()
    start = start.replace(tzinfo=None)
    end = end.replace(tzinfo=None)

    report = meteostat.Hourly(stations, start, end)
    if report._data.empty:
        print(f"Warning: Empty dataframe for gpx owned by {owner} from {start} until {end}")
        return report

    return report.normalize().fetch()