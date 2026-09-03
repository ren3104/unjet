from pathlib import Path


JET_FILE_EXTENSIONS = (".jet", ".pak")
JET_V1_HEADER_FORMAT = "<3IQH2s"
B38_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ._"

CURSOR_FILE = "cursor.txt"
SPINE_CONVERTER = Path(__file__).parent.parent / "SpineSkeletonDataConverter"
