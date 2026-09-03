from .rw_parser import ParserRW
from .sn_parser import ParserSN
from .i2_parser import ParserI2
from .s2_parser import ParserS2
from .at_parser import ParserAT
from .im_parser import ParserIM
from .sp_parser import ParserSP
from .an_parser import ParserAN
from .m2_parser import ParserM2
from .vn_parser import ParserVN


PARSERS = {
    b"RW": ParserRW,
    b"SN": ParserSN,
    b"I2": ParserI2,
    b"S2": ParserS2,
    b"AT": ParserAT,
    b"IM": ParserIM,
    b"SP": ParserSP,
    b"AN": ParserAN,
    b"M2": ParserM2,
}


__all__ = [
    "ParserRW",
    "ParserSN",
    "ParserI2",
    "ParserS2",
    "ParserAT",
    "ParserIM",
    "ParserSP",
    "ParserAN",
    "ParserM2",
    "ParserVN",
    "PARSERS",
]
