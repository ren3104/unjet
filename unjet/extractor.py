import logging
from pathlib import Path
import zlib
import struct
from functools import partial

from .models import JetHeader, JetInfo
from .parsers import PARSERS
from .constants import CURSOR_FILE, JET_V1_HEADER_FORMAT


logger = logging.getLogger("unjet")
logger.setLevel(logging.INFO)
# logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter("{levelname:<8s} | {message}", style="{"))
logger.addHandler(ch)


def extract_jet_file(data: bytes, out: Path, version: int) -> None:
    # logger.info(f"Processing file: {inp}")
 
    if version == 0:
        return extract_old_jet_file(data, out, version)

    for idx, segment in enumerate(_iter_segments(data), start=1):
        logger.debug(f"Segment {idx:03d}:")
        logger.debug(segment)

        segment_out = out / f"{segment.header.resource_id}.bin"
        segment_data = data[segment.data_start:segment.data_end]
        try:
            segment_data = zlib.decompressobj().decompress(segment_data)
        except zlib.error:
            pass

        if segment.header.total_size != segment.header.part_size:
            if segment.header.part_index == 0:
                segment_out.write_bytes(segment_data)
                continue
            else:
                is_final = any(
                    (segment.header.part_index * (10 ** k) + segment.header.part_size) == segment.header.total_size
                    for k in range(len(str(segment.header.total_size)) - 1, 0, -1)
                )
                if is_final:
                    segment_data = segment_out.read_bytes() + segment_data
                else:
                    with segment_out.open("ab") as f:
                        f.write(segment_data)
                    continue
        
        segment_type = segment_data[:2]
        if segment_type in PARSERS:
            file_out = PARSERS[segment_type].parse_resource(segment_data, segment_out, version)
            segment_out.unlink(missing_ok=True)
            if isinstance(file_out, tuple):
                for p in file_out:
                    logger.info(f"-> {p.name}")
            elif file_out is not None:
                logger.info(f"-> {file_out.name}")
        else:
            logger.warning(f"Unsupported segment type: {segment_type}")
            if not segment_out.exists():
                segment_out.write_bytes(segment_data)
            logger.info(f"-> {segment_out.name}")


def _iter_segments(data: bytes):
    pos = 0
    header_size = struct.calcsize(JET_V1_HEADER_FORMAT)
    while pos + header_size <= len(data):
        header = JetHeader.from_bytes(data[pos:pos+header_size])
        data_start = pos + header_size
        data_end = data_start + header.relative_data_end
        segment = JetInfo(pos, data_start, data_end, header)
        yield segment
        pos = data_end


def extract_old_jet_file(data: bytes, out: Path, version: int) -> None:
    tmp_file = out / f"temporary.bin"

    cursor_path = out / CURSOR_FILE
    if cursor_path.exists():
        counter, remain = map(int, cursor_path.read_text().strip().split(","))
    else:
        counter, remain = 0, 0

    data = zlib.decompressobj().decompress(data)

    offset = 0
    while offset < len(data):
        segment_type = data[offset:offset + 2]
        segment_out = out / f"{counter}.bin"

        if remain == 0:
            try:
                expected_size = PARSERS[segment_type].calc_data_size(
                    memoryview(data)[offset:])
            except RuntimeError:
                segment_out = segment_out.with_suffix(".bin")
                segment_out.write_bytes(data)
                logger.info(f"-> {segment_out.name}")
                raise
        else:
            expected_size = remain
        
        if offset + expected_size > len(data):
            with tmp_file.open("ab") as f:
                f.write(data[offset:])
            remain = expected_size - (len(data) - offset)
            logger.debug(f"-> {tmp_file.name}")
            break
        elif remain != 0:
            segment_data = tmp_file.read_bytes() + data[:expected_size]
            tmp_file.unlink(missing_ok=True)
            remain = 0
        else:
            segment_data = data[offset:offset+expected_size]

        counter += 1
        
        offset += expected_size

        segment_type = segment_data[:2]
        if segment_type in PARSERS:
            file_out = PARSERS[segment_type].parse_resource(segment_data, segment_out, version)
            if isinstance(file_out, tuple):
                for p in file_out:
                    logger.info(f"-> {p.name}")
            elif file_out is not None:
                logger.info(f"-> {file_out.name}")
        else:
            logger.warning(f"Unsupported segment type: {segment_type}")
            if not segment_out.exists():
                segment_out.write_bytes(segment_data)
            logger.info(f"-> {segment_out.name}")
    
    cursor_path.write_text(f"{counter},{remain}")
