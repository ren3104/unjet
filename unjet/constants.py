from pathlib import Path


JET_FILE_EXTENSIONS = (".jet", ".pak")
JET_V1_HEADER_FORMAT = "<5IH2s"
CURSOR_FILE = "cursor.txt"
SPINE_CONVERTER = Path(__file__).parent.parent / "SpineSkeletonDataConverter"
