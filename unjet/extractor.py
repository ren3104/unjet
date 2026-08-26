import logging
from pathlib import Path
import zlib
import struct
from functools import partial

from .models import SegmentHeader, Segment
from .parsers import *
from .constants import CURSOR_FILE


logger = logging.getLogger("unjet")
logger.setLevel(logging.INFO)
# logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter("{levelname:<8s} | {message}", style="{"))
logger.addHandler(ch)

SEGMENT_HEADER_SIZE = 24
PARSER_FUNCS = {
    b"RW": parse_rw_file,
    b"SN": parse_sn_file,
    b"I2": parse_i2_file,
    b"S2": parse_s2_file,
    b"AT": parse_at_file,
    b"IM": parse_im_file,
    b"SP": parse_sp_file,
    b"AN": parse_an_file
}
PARSER_FUNCS_OLDJET = {
    b"IM": parse_im_file,
    b"SP": partial(parse_sp_file, old_version=True),
    b"AN": partial(parse_an_file, old_version=True),
    b"M2": parse_m2_file
}


def extract_jet_file(data: bytes, out: Path, version: int) -> None:
    # logger.info(f"Processing file: {inp}")
 
    if version == 0:
        return extract_old_jet_file(data, out)

    for idx, segment in enumerate(_iter_segments(data), start=1):
        logger.debug(f"Segment {idx:03d}:")
        logger.debug(segment)

        segment_out = out / f"{segment.header.file_id}.bin"
        segment_data = data[segment.data_start:segment.data_end]
        try:
            segment_data = zlib.decompressobj().decompress(segment_data)
        except zlib.error:
            pass

        if segment.header.full_size != segment.header.segment_size:
            if segment.header.segment_no == 0:
                segment_out.write_bytes(segment_data)
                continue
            else:
                is_final = any(
                    (segment.header.segment_no * (10 ** k) + segment.header.segment_size) == segment.header.full_size
                    for k in range(len(str(segment.header.full_size)) - 1, 0, -1)
                )
                if is_final:
                    segment_data = segment_out.read_bytes() + segment_data
                else:
                    with segment_out.open("ab") as f:
                        f.write(segment_data)
                    continue
        
        segment_type = segment_data[:2]
        if segment_type in PARSER_FUNCS:
            file_out = PARSER_FUNCS[segment_type](segment_data, segment_out)
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
    while pos + SEGMENT_HEADER_SIZE <= len(data):
        header = SegmentHeader.from_bytes(data[pos:pos+SEGMENT_HEADER_SIZE])
        data_start = pos + SEGMENT_HEADER_SIZE
        data_end = data_start + header.rel_pos_end
        segment = Segment(pos, data_start, data_end, header)
        yield segment
        pos = data_end


def extract_old_jet_file(data: bytes, out: Path) -> None:
    tmp_file = out / f"temporary.bin"

    cursor_path = out / CURSOR_FILE
    if cursor_path.exists():
        counter, remain = map(int, cursor_path.read_text().strip().split(","))
    else:
        counter, remain = 0, 0

    data = zlib.decompressobj().decompress(data)

    offset = 0
    while offset < len(data):
        segment_out = out / f"{counter}.bin"

        if remain == 0:
            try:
                expected_size = _old_segment_size(data, offset)
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
        if segment_type in PARSER_FUNCS_OLDJET:
            file_out = PARSER_FUNCS_OLDJET[segment_type](segment_data, segment_out)
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


def _old_segment_size(data: bytes, offset: int) -> int:
    segment_type = data[offset:offset + 2]
    if segment_type == b"IM":
        _, flag, width, height = struct.unpack("<2sB2H", data[offset:offset + 7])
        size = 7
        if flag == 0:
            size += width * height * 2
        elif flag == 2:
            size += width * height * 3
        elif flag == 6:
            size += width * height
        else:
            raise RuntimeError(f"Unsupported image flag: {flag}")
        return size
    elif segment_type == b"SP":
        block_count = struct.unpack("<H", data[offset + 2:offset + 4])[0]
        return block_count * 6 + 12
    elif segment_type == b"AN":
        block_count = struct.unpack("<H", data[offset + 2:offset + 4])[0]
        return block_count * 6 + 4
    elif segment_type == b"M2":
        _, file_size = struct.unpack("<iI", data[offset + 2:offset + 10])
        return file_size + 10
    else:
        raise RuntimeError(f"Unsupported data type: {segment_type!r}")
