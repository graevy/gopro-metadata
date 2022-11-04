import json

import exiftool


SERIAL_METADATA_STRING = 'QuickTime:CameraSerialNumber'
SERIAL_FILE = 'serials.json'


def load_serial_map():
    with open(SERIAL_FILE) as f:
        return json.load(f)

def save_serial_map(serials):
    with open(SERIAL_FILE, 'w+') as f:
        json.dump(serials, f)

def get_serial_from_file(file):
    # note: if this errors it's usually because it requires a full file path
    # it returns a list...of a map...of a tag...
    # there's probably a better way to do this inside exiftool.execute()
    return exiftool.ExifToolHelper().get_tags(
        file, SERIAL_METADATA_STRING
        )[0][SERIAL_METADATA_STRING]

def add_serial(serial, name):
    serials = load_serial_map()
    serials[serial] = name
    save_serial_map(serials)

def check_file(file):
    """queries cli to handle unrecognized gopro serials

    Args:
        file (str): gopro LRV filename

    Returns:
        str: name of gopro user
    """
    serials = load_serial_map()
    serial = get_serial_from_file(file)
    if serial not in serials:
        newuser = input(f"""unknown gopro serial '{serial}'. 
        name it or leave blank if unknown >>>""")
        add_serial(serial, newuser if newuser != "" else serial)
        return newuser
    else:
        return serials[serial]