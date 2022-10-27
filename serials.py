import subprocess
import json


def load_serial_map():
    with open('serials.json') as f:
        return json.load(f)

def save_serial_map(serials):
    with open('serials.json', 'w+') as f:
        json.dump(serials, f)

# the sixth line on these LRV files contains the gopro serial number
# the problem is that currently i am 1. scanning the whole file with strings, and
# 2. video data preceeding strings is sometimes valid utf-8?
def get_serial_from_file(file):
    with open(file) as f:
        strings = subprocess.run(("strings", file), capture_output=True).stdout
    sed = subprocess.Popen(("sed", "6q;d"), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    bytes = sed.communicate(strings)[0].strip()
    return bytes.decode()

def add_serial(serial, name):
    serials = load_serial_map()
    serials[serial] = name
    save_serial_map(serials)