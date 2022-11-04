# i did one pass over this script i found on github
# the price i pay for pure python
# TODO P3: refactor this


"""
GoPro Highlight Parser:  https://github.com/icegoogles/GoPro-Highlight-Parser
The code for extracting the mp4 boxes/atoms is from 'Human Analog' (https://www.kaggle.com/humananalog): 
https://www.kaggle.com/humananalog/examine-mp4-files-with-python-only
"""

import os
import struct


def find_boxes(f, start_offset=0, end_offset=float("inf")):
    """Returns a dictionary of all the data boxes and their absolute starting
    and ending offsets inside the mp4 file.
    Specify a start_offset and end_offset to read sub-boxes.
    """
    s = struct.Struct("> I 4s")
    boxes = {}
    offset = start_offset
    f.seek(offset, 0)
    while offset < end_offset:
        data = f.read(8)               # read box header
        if data == b"": break          # EOF
        length, text = s.unpack(data)
        f.seek(length - 8, 1)          # skip to next box
        boxes[text] = (offset, offset + length)
        offset += length
    return boxes

def examine_mp4(filename):     
    with open(filename, "rb") as f:
        boxes = find_boxes(f)

        # Sanity check that this really is a movie file.
        def fileerror():  # function to call if file is not a movie file
            print("")
            print("ERROR, file is not a mp4-video-file!")

            os.system("pause")
            exit()

        try:
            if boxes[b"ftyp"][0] != 0:
                fileerror()
        except:
            fileerror()


        moov_boxes = find_boxes(f, boxes[b"moov"][0] + 8, boxes[b"moov"][1])
       
        udta_boxes = find_boxes(f, moov_boxes[b"udta"][0] + 8, moov_boxes[b"udta"][1])

        ### get GPMF Box
        highlights = parse_highlights(f, udta_boxes[b'GPMF'][0] + 8, udta_boxes[b'GPMF'][1])

        # print("")
        # print("Filename:", filename)
        # print("Found", len(highlights), "Highlight(s)!")
        # print('Here are all Highlights: ', highlights)

        return highlights


def parse_highlights(f, start_offset=0, end_offset=float("inf")):

    inHighlights = False
    inHLMT = False
    listOfHighlights = []

    offset = start_offset
    f.seek(offset, 0)

    while offset < end_offset:
        data = f.read(4)               # read box header
        if data == b"": break          # EOF

        if data == b'High' and inHighlights == False:
            data = f.read(4)
            if data == b'ligh':
                inHighlights = True  # set flag, that highlights were reached

        if data == b'HLMT' and inHighlights == True and inHLMT == False:
            inHLMT = True  # set flag that HLMT was reached

        if data == b'MANL' and inHighlights == True and inHLMT == True:

            currPos = f.tell()  # remember current pointer/position
            f.seek(currPos - 20)  # go back to highlight timestamp

            data = f.read(4)  # readout highlight
            timestamp = int.from_bytes(data, "big")  #convert to integer

            if timestamp != 0:
                listOfHighlights.append(timestamp)  # append to highlightlist

            f.seek(currPos)  # go forward again (to the saved position)


    return [highlight/1000 for highlight in listOfHighlights]  # convert to seconds and return

# def sec2dtime(secs):
#     """converts seconds to datetimeformat"""
#     milsec = (secs - floor(secs)) * 1000
#     secs = secs % (24 * 3600) 
#     hour = secs // 3600
#     secs %= 3600
#     min = secs // 60
#     secs %= 60
      
#     return "%d:%02d:%02d.%03d" % (hour, min, secs, milsec) 

# def main(files):
    # str2insert = ""

    # for file in files:  

    #     str2insert += file + "\n"

    #     highlights = examine_mp4(file)  # examine each file

    #     highlights.sort()

    #     for i, highl in enumerate(highlights):
    #         str2insert += "(" + str(i+1) + "): "
    #         str2insert += sec2dtime(highl) + "\n"

    #     str2insert += "\n"

    # Create document
    # stripPath, _ = os.path.splitext(files[0])
    # outpFold, newFName = os.path.split(stripPath)

    # newPath = os.path.join(outpFold, 'GP-Highlights_' + newFName + '.txt')

    # with open(newPath, "w") as f:
    #     f.write(str2insert)

    # print("Saved Highlights under: \"" + newPath + "\"")

    # return [sorted(examine_mp4(file)) for file in files]