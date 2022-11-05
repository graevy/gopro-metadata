import json

import exiftool


SERIAL_METADATA_STRING = 'QuickTime:CameraSerialNumber'
SERIAL_FILE = 'serials.json'


def _load_serial_map():
    with open(SERIAL_FILE) as f:
        return json.load(f)

def _save_serial_map(serials):
    with open(SERIAL_FILE, 'w+') as f:
        json.dump(serials, f)

def _get_serial_from_file(file):
    # note: if this errors it's usually because it requires a full file path
    # get_tags() returns a list...of a map...of a tag...
    return exiftool.ExifToolHelper().get_tags(
        file, SERIAL_METADATA_STRING
        )[0][SERIAL_METADATA_STRING]

def _add_serial(serial, name):
    serials = _load_serial_map()
    serials[serial] = name
    _save_serial_map(serials)

def check_file(file):
    """queries cli to handle unrecognized gopro serials

    Args:
        file (str): gopro (LRV) file

    Returns:
        str: name of gopro user
    """
    serials = _load_serial_map()
    serial = _get_serial_from_file(file)
    if serial not in serials:
        newuser = input(f"""unknown gopro serial '{serial}'. 
        name it or leave blank if unknown >>>""")
        _add_serial(serial, newuser if newuser != "" else serial)
        return newuser
    else:
        return serials[serial]