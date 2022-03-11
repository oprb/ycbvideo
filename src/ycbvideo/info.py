import pkgutil
import re
from typing import List, Tuple, Callable, Iterable, Dict, TypeVar

from .frame_access import FrameAccessor

T = TypeVar('T')

FRAME_INFO_PATTERN = re.compile(r'^(?P<framesequence>[^:]+): (?P<framecount>[0-9]+)$')


def get_item_ranges(collection: List[T], check_consecution: Callable[[T, T], bool]) -> List[Tuple[int, int]]:
    number_of_items = len(collection)
    if number_of_items == 0:
        return []
    if number_of_items == 1:
        return [(0, 1)]

    ranges = []
    range_start = 0
    previous_item = collection[0]

    for index, item in enumerate(collection[1:], 1):
        if not check_consecution(previous_item, item):
            ranges.append((range_start, index))
            range_start = index

        previous_item = item

    ranges.append((range_start, number_of_items))

    return ranges


def format_in_ranges(items: List[str], check_consecution: Callable[[str, str], bool]) -> [str]:
    formatted_item_ranges = []
    for range_start, range_stop in get_item_ranges(items, check_consecution):
        if range_stop == range_start + 1:
            formatted_item_ranges.append(items[range_start])
        else:
            formatted_item_ranges.append(f"{items[range_start]} - {items[range_stop - 1]}")

    return formatted_item_ranges


def check_sequence_or_frame_consecution(sequence1: str, sequence2: str) -> bool:
    if sequence1.isdigit() and sequence2.isdigit():
        return int(sequence2) == int(sequence1) + 1

    # includes the 'data_syn' sequence
    return False


def read_frame_count_per_frame_sequence() -> Dict[str, int]:
    frames_per_sequence = {}
    frame_info = pkgutil.get_data(__package__, 'frame_info.txt').decode('utf-8').split('\n')

    # skip the newline line at the end of the file
    for entry in frame_info[:-1]:
        # if there is no match, the file would be corrupt
        match = FRAME_INFO_PATTERN.match(entry)
        sequence = match.group('framesequence')
        frame_count = int(match.group('framecount'))

        frames_per_sequence[sequence] = frame_count

    return frames_per_sequence


def print_frame_info(frame_accessor: FrameAccessor, sequences: Iterable[str], verbosity: int = 0):
    frames_info = frame_accessor.frames_info()
    sequence_count = len(frames_info)
    frames_total = read_frame_count_per_frame_sequence()
    missing_sequences = []

    for sequence in sequences:
        if sequence not in frames_info:
            missing_sequences.append(sequence)

    print('Frames')
    print('------')
    print()
    print(f"Frame sequences available: {sequence_count} (total: 92)")
    if verbosity > 0:
        print(f"Available: {format_in_ranges(list(frames_info.keys()), check_sequence_or_frame_consecution)}")
    print(f"Missing: {format_in_ranges(missing_sequences, check_sequence_or_frame_consecution)}")
    print()
    print('Available frame sequences:')
    print('sequence: complete/incomplete/dataset total')
    for sequence, frame_sets in frames_info.items():
        complete_frame_sets = []
        incomplete_frame_sets = []
        for frame_set, missing_files in frame_sets.items():
            if missing_files:
                incomplete_frame_sets.append(frame_set)
            else:
                complete_frame_sets.append(frame_set)
        print(f"{sequence:>8}: {len(complete_frame_sets)}/{len(incomplete_frame_sets)}/{frames_total[sequence]})")
        if incomplete_frame_sets:
            print('Incomplete frame sets:')
            for frame_set in sorted(incomplete_frame_sets):
                print(f"{frame_set}: {frame_sets[frame_set]} missing")
        elif verbosity > 1:
            print('Incomplete frame sets: none')
        if verbosity > 0:
            print('Complete frame sets:')
            print(format_in_ranges(sorted(complete_frame_sets), check_consecution=check_sequence_or_frame_consecution))
