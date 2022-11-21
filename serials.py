import exiftool


SERIAL_METADATA_STRING = 'QuickTime:CameraSerialNumber'

def get_serial_from_file(file):
    # note: if this errors it's usually because it requires a full file path
    # get_tags() returns a list...of a map...of a tag...
    return exiftool.ExifToolHelper().get_tags(
        file, SERIAL_METADATA_STRING
        )[0][SERIAL_METADATA_STRING]
