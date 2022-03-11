import re
import sys

from . import frame_access, info


def print_usage_info():
    print('usage: ycbvideo')
    print('                DATASET_ROOT [-v | -vv]')


# sys.argv[0] is the name of the file executed
if (argument_count := len(sys.argv)) >= 2:
    dataset = sys.argv[1]
    verbosity = 0
    frame_sequences = (f"{index:04d}" for index in range(92))

    if len(sys.argv) > 2:
        # verbosity level -v == 0 is the default
        if match := re.match(r'^-(?P<vstring>[v]+)$', sys.argv[2]):
            verbosity = len(match.group('vstring'))

    info.print_frame_info(frame_access.FrameAccessor(dataset), frame_sequences, verbosity)
else:
    print_usage_info()
