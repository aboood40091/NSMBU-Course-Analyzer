from enum import Enum
import os
import struct

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal
from typing import Dict, Set, Optional, List, Tuple, Union

import SarcLib


CD_FILE_MAX_NUM = 4
CD_FILE_ENV_PA_SLOT_NAME_MAX_LEN = 32
CD_FILE_ENV_MAX_NUM = 4

CD_FILE_BLOCK_ENVIRONMENT       =  1 - 1
CD_FILE_BLOCK_OPTIONS           =  2 - 1
CD_FILE_BLOCK_SCROLL_DATA       =  3 - 1
                                #  4
CD_FILE_BLOCK_DISTANT_VIEW_DATA =  5 - 1
                                #  6
CD_FILE_BLOCK_NEXT_GOTO         =  7 - 1
CD_FILE_BLOCK_MAP_ACTOR_DATA    =  8 - 1
CD_FILE_BLOCK_MAP_ACTOR_RES     =  9 - 1
CD_FILE_BLOCK_AREA_DATA         = 10 - 1
CD_FILE_BLOCK_LOCATION          = 11 - 1
                                # 12
                                # 13
CD_FILE_BLOCK_RAIL_INFO         = 14 - 1
CD_FILE_BLOCK_RAIL_POINT        = 15 - 1

CD_FILE_BLOCK_NUM = 15

LAYER_1 = 0
LAYER_2 = 1
LAYER_0 = 2

CD_FILE_LAYER_MAX_NUM = 3


def SharcHasFile(arc: SarcLib.SARC_Archive, file: str) -> bool:
    try:
        arc[file]
    except KeyError:
        return False
    else:
        return True


def SharcTryGetFile(arc: SarcLib.SARC_Archive, file: str) -> Optional[bytes]:
    try:
        file = arc[file]
    except KeyError:
        return None
    else:
        return file.data
    

def SharcReadEntries(arc: SarcLib.SARC_Archive) -> List[Tuple[str, bytes]]:
    flatList = []

    def _addToFlatList(folder: Union[SarcLib.Folder, SarcLib.SARC_Archive], path: str) -> None:
        nonlocal flatList

        if path:
            path.replace('\\', '/')
            if not path.endswith('/'):
                path += '/'

        for checkObj in folder.contents:
            if isinstance(checkObj, SarcLib.File):
                flatList.append((path + checkObj.name, checkObj.data))

            else:
                assert isinstance(checkObj, SarcLib.Folder)
                _addToFlatList(checkObj, path + checkObj.name)

    _addToFlatList(arc, '')
    return flatList


class Structures(Enum):
    CdFileBlock  = 'II'
    Options      = 'IIHHBBBBBBBBHH'
    ScrollData   = 'iiiiHHhhBBBB'
    DistantView  = 'Hhhh16sHBB'
    NextGoto     = 'HHHHBBBBBBBBHBBBBBB'
    MapActor     = 'HHHHIIBBBBBBBB'
    Area         = 'HHHHHHBBBBBBBBBBBBBBBB'
    Location     = 'HHHHBBBB'
    Rail         = 'BbHHHI'
    RailPoint    = 'HHffhHBBBB'
    BgCourseData = 'HHHHHBBBBBB'


TEndian = Literal['>', '<']


def GetStructureFormat(endianness: TEndian, structId: Structures) -> str:
    return endianness + structId.value


def GetStructureSize(endianness: TEndian, structId: Structures) -> int:
    return struct.calcsize(GetStructureFormat(endianness, structId))


SID = Structures
FMT = GetStructureFormat
SIZE = GetStructureSize


class CourseDataFileHeader:
    @staticmethod
    def getBlock(index: int, endianness: TEndian, data: bytes, pos: int = 0) -> None:
        assert 0 <= index < CD_FILE_BLOCK_NUM
        offset, size = struct.unpack_from(FMT(endianness, SID.CdFileBlock), data, pos + index * SIZE(endianness, SID.CdFileBlock))
        return data[pos + offset:pos + offset + size]


class Environment:
    pa_slot_name: Tuple[str, str, str, str]

    def __init__(self, data: Optional[bytes] = None, pos: int = 0) -> None:
        if data is not None:
            self.load(data, pos)
        else:
            self.initialize()

    def initialize(self) -> None:
        self.pa_slot_name = ('', '', '', '')

    def load(self, data: bytes, pos: int = 0) -> None:
        pa_slot_name = []
        for i in range(CD_FILE_ENV_MAX_NUM):
            pa_slot_name_i = data[pos + CD_FILE_ENV_PA_SLOT_NAME_MAX_LEN*i:pos + CD_FILE_ENV_PA_SLOT_NAME_MAX_LEN*(i+1)]
            assert b'\0' in pa_slot_name_i
            pa_slot_name.append(pa_slot_name_i.split(b'\0')[0].decode('ascii'))
        
        self.pa_slot_name = tuple(pa_slot_name)

    def save(self) -> bytes:
        for i in range(CD_FILE_ENV_MAX_NUM):
            assert len(self.pa_slot_name[i]) < CD_FILE_ENV_PA_SLOT_NAME_MAX_LEN

        return b''.join(self.pa_slot_name[i].encode('ascii').ljust(CD_FILE_ENV_PA_SLOT_NAME_MAX_LEN, b'\0') for i in range(CD_FILE_ENV_MAX_NUM))


class Options:
    def_events_0: int
    def_events_1: int
    loop: int
    time_0: int
    _unused0_0: int
    _unused0_1: int
    _unused0_2: int
    _unused0_3: int
    start_next_goto: int
    _unused1_0: int
    _unused1_1: int
    start_next_goto_coin_boost: int
    time_1: int
    time_2: int

    def __init__(self, data: Optional[bytes] = None, endianness: TEndian = '>', pos: int = 0) -> None:
        if data is not None:
            self.load(endianness, data, pos)
        else:
            self.initialize()

    def initialize(self) -> None:
        self.def_events_0 = 0
        self.def_events_1 = 0
        self.loop = 0
        self.time_0 = 0
        self._unused0_0 = 0
        self._unused0_1 = 0
        self._unused0_2 = 0
        self._unused0_3 = 0
        self.start_next_goto = 0
        self._unused1_0 = 0
        self._unused1_1 = 0
        self.start_next_goto_coin_boost = 0
        self.time_1 = 0
        self.time_2 = 0

    def load(self, endianness: TEndian, data: bytes, pos: int = 0) -> None:
        (
            self.def_events_0,
            self.def_events_1,
            self.loop,
            self.time_0,
            self._unused0_0,
            self._unused0_1,
            self._unused0_2,
            self._unused0_3,
            self.start_next_goto,
            self._unused1_0,
            self._unused1_1,
            self.start_next_goto_coin_boost,
            self.time_1,
            self.time_2
        ) = struct.unpack_from(FMT(endianness, SID.Options), data, pos)

    def save(self, endianness: TEndian) -> bytes:
        return struct.pack(
            FMT(endianness, SID.Options),
            self.def_events_0,
            self.def_events_1,
            self.loop,
            self.time_0,
            self._unused0_0,
            self._unused0_1,
            self._unused0_2,
            self._unused0_3,
            self.start_next_goto,
            self._unused1_0,
            self._unused1_1,
            self.start_next_goto_coin_boost,
            self.time_1,
            self.time_2
        )


class ScrollData:
    bound_0__upper: int
    bound_0__lower: int
    bound_1__upper: int
    bound_1__lower: int
    ID: int
    flag: int
    mp_bound_adjust__upper: int
    mp_bound_adjust__lower: int
    _unused0_0: int
    _unused0_1: int
    _unused0_2: int
    _unused0_3: int

    def __init__(self, endianness: TEndian, data: bytes, pos: int = 0) -> None:
        self.load(endianness, data, pos)

    def load(self, endianness: TEndian, data: bytes, pos: int = 0) -> None:
        (
            self.bound_0__upper,
            self.bound_0__lower,
            self.bound_1__upper,
            self.bound_1__lower,
            self.ID,
            self.flag,
            self.mp_bound_adjust__upper,
            self.mp_bound_adjust__lower,
            self._unused0_0,
            self._unused0_1,
            self._unused0_2,
            self._unused0_3
        ) = struct.unpack_from(FMT(endianness, SID.ScrollData), data, pos)

    def save(self, endianness: TEndian) -> bytes:
        return struct.pack(
            FMT(endianness, SID.ScrollData),
            self.bound_0__upper,
            self.bound_0__lower,
            self.bound_1__upper,
            self.bound_1__lower,
            self.ID,
            self.flag,
            self.mp_bound_adjust__upper,
            self.mp_bound_adjust__lower,
            self._unused0_0,
            self._unused0_1,
            self._unused0_2,
            self._unused0_3
        )


class DistantViewData:
    ID: int
    offset__x: int
    offset__y: int
    offset__z: int
    name: bytes
    parallax_mode: int
    _pad_0: int
    _pad_1: int

    def __init__(self, endianness: TEndian, data: bytes, pos: int = 0) -> None:
        self.load(endianness, data, pos)

    def load(self, endianness: TEndian, data: bytes, pos: int = 0) -> None:
        (
            self.ID,
            self.offset__x,
            self.offset__y,
            self.offset__z,
            self.name,
            self.parallax_mode,
            self._pad_0,
            self._pad_1
        ) = struct.unpack_from(FMT(endianness, SID.DistantView), data, pos)

    def save(self, endianness: TEndian) -> bytes:
        return struct.pack(
            FMT(endianness, SID.DistantView),
            self.ID,
            self.offset__x,
            self.offset__y,
            self.offset__z,
            self.name,
            self.parallax_mode,
            self._pad_0,
            self._pad_1
        )


class NextGoto:
    offset__x: int
    offset__y: int
    camera_offset__x: int
    camera_offset__y: int
    ID: int
    destination__file: int
    destination__next_goto: int
    type: int
    mp_spawn_flag: int
    area: int
    _unused0: int
    mp_inner_gap: int
    flag: int
    chibi_yoshi_next_goto: int
    coin_edit_priority: int
    rail__info: int
    rail__point: int
    wipe_type: int
    _pad_0: int

    def __init__(self, endianness: TEndian, data: bytes, pos: int = 0) -> None:
        self.load(endianness, data, pos)

    def load(self, endianness: TEndian, data: bytes, pos: int = 0) -> None:
        (
            self.offset__x,
            self.offset__y,
            self.camera_offset__x,
            self.camera_offset__y,
            self.ID,
            self.destination__file,
            self.destination__next_goto,
            self.type,
            self.mp_spawn_flag,
            self.area,
            self._unused0,
            self.mp_inner_gap,
            self.flag,
            self.chibi_yoshi_next_goto,
            self.coin_edit_priority,
            self.rail__info,
            self.rail__point,
            self.wipe_type,
            self._pad_0
        ) = struct.unpack_from(FMT(endianness, SID.NextGoto), data, pos)

    def save(self, endianness: TEndian) -> bytes:
        return struct.pack(
            FMT(endianness, SID.NextGoto),
            self.offset__x,
            self.offset__y,
            self.camera_offset__x,
            self.camera_offset__y,
            self.ID,
            self.destination__file,
            self.destination__next_goto,
            self.type,
            self.mp_spawn_flag,
            self.area,
            self._unused0,
            self.mp_inner_gap,
            self.flag,
            self.chibi_yoshi_next_goto,
            self.coin_edit_priority,
            self.rail__info,
            self.rail__point,
            self.wipe_type,
            self._pad_0
        )


class MapActorData:
    type: int
    offset__x: int
    offset__y: int
    event_ID: int
    settings_0: int
    settings_1: int
    area: int
    layer: int
    movement_ID: int
    link_ID: int
    init_state: int
    _pad_0: int
    _pad_1: int
    _pad_2: int

    def __init__(self, endianness: TEndian, data: bytes, pos: int = 0) -> None:
        self.load(endianness, data, pos)

    def load(self, endianness: TEndian, data: bytes, pos: int = 0) -> None:
        (
            self.type,
            self.offset__x,
            self.offset__y,
            self.event_ID,
            self.settings_0,
            self.settings_1,
            self.area,
            self.layer,
            self.movement_ID,
            self.link_ID,
            self.init_state,
            self._pad_0,
            self._pad_1,
            self._pad_2
        ) = struct.unpack_from(FMT(endianness, SID.MapActor), data, pos)

    def save(self, endianness: TEndian) -> bytes:
        return struct.pack(
            FMT(endianness, SID.MapActor),
            self.type,
            self.offset__x,
            self.offset__y,
            self.event_ID,
            self.settings_0,
            self.settings_1,
            self.area,
            self.layer,
            self.movement_ID,
            self.link_ID,
            self.init_state,
            self._pad_0,
            self._pad_1,
            self._pad_2
        )


class AreaData:
    offset__x: int
    offset__y: int
    size__x: int
    size__y: int
    color_obj: int
    color_bg: int
    ID: int
    scroll: int
    zoom_type: int
    zoom_ID: int
    zoom_change: int
    mask: int
    bg2: int
    bg3: int
    direction: int
    _15: int
    bgm: int
    bgm_mode: int
    dv: int
    flag: int
    _pad_0: int
    _pad_1: int

    def __init__(self, endianness: TEndian, data: bytes, pos: int = 0) -> None:
        self.load(endianness, data, pos)

    def load(self, endianness: TEndian, data: bytes, pos: int = 0) -> None:
        (
            self.offset__x,
            self.offset__y,
            self.size__x,
            self.size__y,
            self.color_obj,
            self.color_bg,
            self.ID,
            self.scroll,
            self.zoom_type,
            self.zoom_ID,
            self.zoom_change,
            self.mask,
            self.bg2,
            self.bg3,
            self.direction,
            self._15,
            self.bgm,
            self.bgm_mode,
            self.dv,
            self.flag,
            self._pad_0,
            self._pad_1
        ) = struct.unpack_from(FMT(endianness, SID.Area), data, pos)

    def save(self, endianness: TEndian) -> bytes:
        return struct.pack(
            FMT(endianness, SID.Area),
            self.offset__x,
            self.offset__y,
            self.size__x,
            self.size__y,
            self.color_obj,
            self.color_bg,
            self.ID,
            self.scroll,
            self.zoom_type,
            self.zoom_ID,
            self.zoom_change,
            self.mask,
            self.bg2,
            self.bg3,
            self.direction,
            self._15,
            self.bgm,
            self.bgm_mode,
            self.dv,
            self.flag,
            self._pad_0,
            self._pad_1
        )


class Location:
    offset__x: int
    offset__y: int
    size__x: int
    size__y: int
    ID: int
    _pad_0: int
    _pad_1: int
    _pad_2: int

    def __init__(self, endianness: TEndian, data: bytes, pos: int = 0) -> None:
        self.load(endianness, data, pos)

    def load(self, endianness: TEndian, data: bytes, pos: int = 0) -> None:
        (
            self.offset__x,
            self.offset__y,
            self.size__x,
            self.size__y,
            self.ID,
            self._pad_0,
            self._pad_1,
            self._pad_2
        ) = struct.unpack_from(FMT(endianness, SID.Location), data, pos)

    def save(self, endianness: TEndian) -> bytes:
        return struct.pack(
            FMT(endianness, SID.Location),
            self.offset__x,
            self.offset__y,
            self.size__x,
            self.size__y,
            self.ID,
            self._pad_0,
            self._pad_1,
            self._pad_2
        )


class RailInfo:
    ID: int
    _1: int
    point__start: int
    point__num: int
    flag: int
    _8: int

    def __init__(self, endianness: TEndian, data: bytes, pos: int = 0) -> None:
        self.load(endianness, data, pos)

    def load(self, endianness: TEndian, data: bytes, pos: int = 0) -> None:
        (
            self.ID,
            self._1,
            self.point__start,
            self.point__num,
            self.flag,
            self._8
        ) = struct.unpack_from(FMT(endianness, SID.Rail), data, pos)

    def save(self, endianness: TEndian) -> bytes:
        return struct.pack(
            FMT(endianness, SID.Rail),
            self.ID,
            self._1,
            self.point__start,
            self.point__num,
            self.flag,
            self._8
        )


class RailPoint:
    offset__x: int
    offset__y: int
    speed: float
    accel: float
    delay: int
    _e: int
    _10: int
    _11: int
    _12: int
    _pad_0: int

    def __init__(self, endianness: TEndian, data: bytes, pos: int = 0) -> None:
        self.load(endianness, data, pos)

    def load(self, endianness: TEndian, data: bytes, pos: int = 0) -> None:
        (
            self.offset__x,
            self.offset__y,
            self.speed,
            self.accel,
            self.delay,
            self._e,
            self._10,
            self._11,
            self._12,
            self._pad_0
        ) = struct.unpack_from(FMT(endianness, SID.RailPoint), data, pos)

    def save(self, endianness: TEndian) -> bytes:
        return struct.pack(
            FMT(endianness, SID.RailPoint),
            self.offset__x,
            self.offset__y,
            self.speed,
            self.accel,
            self.delay,
            self._e,
            self._10,
            self._11,
            self._12,
            self._pad_0
        )


class BgCourseData:
    type: int
    offset__x: int
    offset__y: int
    size__x: int
    size__y: int
    flag: int
    _pad_0: int
    _pad_1: int
    _pad_2: int
    _pad_3: int
    _pad_4: int

    def __init__(self, endianness: TEndian, data: bytes, pos: int = 0) -> None:
        self.load(endianness, data, pos)

    def load(self, endianness: TEndian, data: bytes, pos: int = 0) -> None:
        (
            self.type,
            self.offset__x,
            self.offset__y,
            self.size__x,
            self.size__y,
            self.flag,
            self._pad_0,
            self._pad_1,
            self._pad_2,
            self._pad_3,
            self._pad_4
        ) = struct.unpack_from(FMT(endianness, SID.BgCourseData), data, pos)

    def save(self, endianness: TEndian) -> bytes:
        return struct.pack(
            FMT(endianness, SID.BgCourseData),
            self.type,
            self.offset__x,
            self.offset__y,
            self.size__x,
            self.size__y,
            self.flag,
            self._pad_0,
            self._pad_1,
            self._pad_2,
            self._pad_3,
            self._pad_4
        )


class CourseDataFile:
    _ID: int

    # Bg data for each layer
    _bgData: Tuple[List[BgCourseData], List[BgCourseData], List[BgCourseData]]

    # Blocks
    _environment:     Environment           # 1
    _options:         Options               # 2
    _scrollData:      List[ScrollData]      # 3
                                            # 4
    _distantViewData: List[DistantViewData] # 5
                                            # 6
    _nextGoto:        List[NextGoto]        # 7
    _mapActorData:    List[MapActorData]    # 8
                                            # 9 (List of used map actors' IDs)
    _areaData:        List[AreaData]        # 10
    _location:        List[Location]        # 11
                                            # 12
                                            # 13
    _railInfo:        List[RailInfo]        # 14
    _railPoint:       List[RailPoint]       # 15

    def __init__(self) -> None:
        self._ID: int = -1
        self._bgData = ([], [], [])
        self._environment = Environment()
        self._options = Options()
        self._scrollData = []
        self._distantViewData = []
        self._nextGoto = []
        self._mapActorData = []
        self._areaData = []
        self._location = []
        self._railInfo = []
        self._railPoint = []

    def load(
        self,
        ID: int,
        endianness: TEndian,
        file: Optional[bytes],
        bgdat_L0: Optional[bytes] = None,
        bgdat_L1: Optional[bytes] = None,
        bgdat_L2: Optional[bytes] = None
    ) -> None:
        assert 0 <= ID < CD_FILE_MAX_NUM

        # Clear it
        self.clear()

        # If file if None, return
        if file is None:
            return
        
        self._ID = ID

        self._loadFile(endianness, file)
        self._loadBgDat(LAYER_0, endianness, bgdat_L0)
        self._loadBgDat(LAYER_1, endianness, bgdat_L1)
        self._loadBgDat(LAYER_2, endianness, bgdat_L2)
    
    def save(self, endianness: TEndian) -> Tuple[bytes, bytes, bytes, bytes]:
        return (
            self._saveFile(endianness),
            self._saveBgDat(LAYER_0, endianness),
            self._saveBgDat(LAYER_1, endianness),
            self._saveBgDat(LAYER_2, endianness)
        )
    
    def _loadFile(self, endianness: TEndian, header_b: bytes) -> None:
        block1 = CourseDataFileHeader.getBlock(CD_FILE_BLOCK_ENVIRONMENT, endianness, header_b)
        if block1:
            self._environment.load(block1)

        block2 = CourseDataFileHeader.getBlock(CD_FILE_BLOCK_OPTIONS, endianness, header_b)
        if block2:
            self._options.load(endianness, block2)

        block3 = CourseDataFileHeader.getBlock(CD_FILE_BLOCK_SCROLL_DATA, endianness, header_b)
        if block3:
            block3Size = len(block3)
            scrollDataSize = SIZE(endianness, SID.ScrollData)
            assert block3Size % scrollDataSize == 0
            block3Count = block3Size // scrollDataSize
            self._scrollData = [ScrollData(endianness, block3, i * scrollDataSize) for i in range(block3Count)]

        block5 = CourseDataFileHeader.getBlock(CD_FILE_BLOCK_DISTANT_VIEW_DATA, endianness, header_b)
        if block5:
            block5Size = len(block5)
            distantViewSize = SIZE(endianness, SID.DistantView)
            assert block5Size % distantViewSize == 0
            block5Count = block5Size // distantViewSize
            self._distantViewData = [DistantViewData(endianness, block5, i * distantViewSize) for i in range(block5Count)]

        block7 = CourseDataFileHeader.getBlock(CD_FILE_BLOCK_NEXT_GOTO, endianness, header_b)
        if block7:
            block7Size = len(block7)
            nextGotoSize = SIZE(endianness, SID.NextGoto)
            assert block7Size % nextGotoSize == 0
            block7Count = block7Size // nextGotoSize
            self._nextGoto = [NextGoto(endianness, block7, i * nextGotoSize) for i in range(block7Count)]

        block8 = CourseDataFileHeader.getBlock(CD_FILE_BLOCK_MAP_ACTOR_DATA, endianness, header_b)
        if block8:
            block8Size = len(block8) - 4  # 4 == sizeof(u32)
            assert block8Size > 0
            mapActorSize = SIZE(endianness, SID.MapActor)
            assert block8Size % mapActorSize == 0
            assert block8[-4:] == b'\xFF\xFF\xFF\xFF'  # u32(-1)
            block8Count = block8Size // mapActorSize
            self._mapActorData = [MapActorData(endianness, block8, i * mapActorSize) for i in range(block8Count)]

        block10 = CourseDataFileHeader.getBlock(CD_FILE_BLOCK_AREA_DATA, endianness, header_b)
        if block10:
            block10Size = len(block10)
            areaSize = SIZE(endianness, SID.Area)
            assert block10Size % areaSize == 0
            block10Count = block10Size // areaSize
            self._areaData = [AreaData(endianness, block10, i * areaSize) for i in range(block10Count)]

        block11 = CourseDataFileHeader.getBlock(CD_FILE_BLOCK_LOCATION, endianness, header_b)
        if block11:
            block11Size = len(block11)
            locationSize = SIZE(endianness, SID.Location)
            assert block11Size % locationSize == 0
            block11Count = block11Size // locationSize
            self._location = [Location(endianness, block11, i * locationSize) for i in range(block11Count)]

        block14 = CourseDataFileHeader.getBlock(CD_FILE_BLOCK_RAIL_INFO, endianness, header_b)
        if block14:
            block14Size = len(block14)
            railSize = SIZE(endianness, SID.Rail)
            assert block14Size % railSize == 0
            block14Count = block14Size // railSize
            self._railInfo = [RailInfo(endianness, block14, i * railSize) for i in range(block14Count)]

        block15 = CourseDataFileHeader.getBlock(CD_FILE_BLOCK_RAIL_POINT, endianness, header_b)
        if block15:
            block15Size = len(block15)
            railPointSize = SIZE(endianness, SID.RailPoint)
            assert block15Size % railPointSize == 0
            block15Count = block15Size // railPointSize
            self._railPoint = [RailPoint(endianness, block15, i * railPointSize) for i in range(block15Count)]

    def _loadBgDat(self, layer: int, endianness: TEndian, bgdat_b: Optional[bytes]) -> None:
        if bgdat_b is None:
            return
        
        self_bgdat = self._bgData[layer]
        self_bgdat.clear()

        pos = 0
        while True:
            if bgdat_b[pos:pos+2] == b'\xFF\xFF':
                break
            self_bgdat.append(BgCourseData(endianness, bgdat_b, pos))
            pos += SIZE(endianness, SID.BgCourseData)
    
    def _saveFile(self, endianness: TEndian) -> bytes:
        raise NotImplementedError

    def _saveBgDat(self, layer: int, endianness: TEndian) -> bytes:
        raise NotImplementedError
    
    def clear(self) -> None:
        self._ID = -1

        self._bgData[LAYER_0].clear()
        self._bgData[LAYER_1].clear()
        self._bgData[LAYER_2].clear()

        self._environment.initialize()
        self._options.initialize()

        self._scrollData.clear()
        self._distantViewData.clear()
        self._nextGoto.clear()
        self._mapActorData.clear()
        self._areaData.clear()
        self._location.clear()
        self._railInfo.clear()
        self._railPoint.clear()
    
    def isValid(self) -> bool:
        return 0 <= self._ID < CD_FILE_MAX_NUM
    
    def getID(self) -> int:
        return self._ID
    
    def getEnvironment(self, index: int) -> str:
        assert 0 <= index < CD_FILE_ENV_MAX_NUM
        return self._environment.pa_slot_name[index]

    def setEnvironment(self, index: int, name: str) -> None:
        assert 0 <= index < CD_FILE_ENV_MAX_NUM
        self._environment.pa_slot_name[index] = name[:CD_FILE_ENV_PA_SLOT_NAME_MAX_LEN - 1]

    def getOptions(self) -> Options:
        return self._options
    
    def getScrollData(self) -> List[ScrollData]:
        return self._scrollData

    def getScrollDataIndexByID(self, ID: int, start_index: int = 0) -> int:
        for i in range(max(0, start_index), len(self._scrollData)):
            if self._scrollData[i].ID == ID:
                return i

        return -1

    def getScrollDataByID(self, ID: int, start_index: int = 0) -> Optional[ScrollData]:
        index = self.getScrollDataIndexByID(ID, start_index)
        if index >= 0:
            return self._scrollData[index]
        else:
            return None
        
    def getDistantViewData(self) -> List[DistantViewData]:
        return self._distantViewData
    
    def getDistantViewDataIndexByID(self, ID: int, start_index: int = 0) -> int:
        for i in range(max(0, start_index), len(self._distantViewData)):
            if self._distantViewData[i].ID == ID:
                return i

        return -1

    def getDistantViewDataByID(self, ID: int, start_index: int = 0) -> Optional[DistantViewData]:
        index = self.getDistantViewDataIndexByID(ID, start_index)
        if index >= 0:
            return self._distantViewData[index]
        else:
            return None
        
    def getNextGoto(self) -> List[NextGoto]:
        return self._nextGoto
    
    def getNextGotoIndexByID(self, ID: int, start_index: int = 0) -> int:
        for i in range(max(0, start_index), len(self._nextGoto)):
            if self._nextGoto[i].ID == ID:
                return i

        return -1
    
    def getNextGotoByID(self, ID: int, start_index: int = 0) -> Optional[NextGoto]:
        index = self.getNextGotoIndexByID(ID, start_index)
        if index >= 0:
            return self._nextGoto[index]
        else:
            return None
        
    def getMapActorData(self) -> List[MapActorData]:
        return self._mapActorData
    
    def getAreaData(self) -> List[AreaData]:
        return self._areaData
    
    def getAreaDataIndexByID(self, ID: int, start_index: int = 0) -> int:
        for i in range(max(0, start_index), len(self._areaData)):
            if self._areaData[i].ID == ID:
                return i

        return -1
    
    def getAreaDataByID(self, ID: int, start_index: int = 0) -> Optional[AreaData]:
        index = self.getAreaDataIndexByID(ID, start_index)
        if index >= 0:
            return self._areaData[index]
        else:
            return None
        
    def getLocation(self) -> List[Location]:
        return self._location
    
    def getLocationIndexByID(self, ID: int, start_index: int = 0) -> int:
        for i in range(max(0, start_index), len(self._location)):
            if self._location[i].ID == ID:
                return i

        return -1
    
    def getLocationByID(self, ID: int, start_index: int = 0) -> Optional[Location]:
        index = self.getLocationIndexByID(ID, start_index)
        if index >= 0:
            return self._location[index]
        else:
            return None
        
    def getRailInfo(self) -> List[RailInfo]:
        return self._railInfo
    
    def getRailInfoIndexByID(self, ID: int, start_index: int = 0) -> int:
        for i in range(max(0, start_index), len(self._railInfo)):
            if self._railInfo[i].ID == ID:
                return i

        return -1

    def getRailInfoByID(self, ID: int, start_index: int = 0) -> Optional[RailInfo]:
        index = self.getRailInfoIndexByID(ID, start_index)
        if index >= 0:
            return self._railInfo[index]
        else:
            return None
        
    def getRailPoint(self) -> List[RailPoint]:
        return self._railPoint
    
    def getBgData(self, layer: int) -> List[BgCourseData]:
        assert 0 <= layer < CD_FILE_LAYER_MAX_NUM
        return self._bgData[layer]


class CourseData:
    _file = tuple(CourseDataFile() for _ in range(CD_FILE_MAX_NUM))
    _resData: Dict[str, bytes] = {}

    @classmethod
    def loadFromPack(cls, path: str, isNSMBUDX: bool) -> None:
        endianness: TEndian = '<' if isNSMBUDX else '>'

        with open(path, 'rb') as inf:
            inb = inf.read()

        pack_arc_dat = inb
        pack_arc = SarcLib.SARC_Archive(pack_arc_dat, endianness)

        read_files: Set[str] = set()

        # print("\nLoaded %s\n" % path)

        archive = pack_arc
        inner_archive = False

        if not isNSMBUDX and not SharcHasFile(archive, "course/course1.bin"):
            inner_archive = True
            level_name: str = ""
            level_dat: Optional[bytes] = None

            level_name_dat = SharcTryGetFile(pack_arc, "levelname")
            if level_name_dat is not None:
                level_name = level_name_dat.decode()
                level_dat = SharcTryGetFile(pack_arc, level_name)
                if level_dat is not None:
                    read_files.add("levelname")

            if level_dat is None:
                level_name = os.path.splitext(os.path.basename(path))[0]
                level_dat = SharcTryGetFile(pack_arc, level_name)
                if level_dat is None:
                    raise RuntimeError("Inner level not found...")
                
            assert level_dat is not None
            archive = SarcLib.SARC_Archive(level_dat, endianness)
            read_files.add(level_name)

        for i in range(CD_FILE_MAX_NUM):
            courseDataFileName   = "course/course%d.bin"         % (1 + i)
            courseDataFileL0Name = "course/course%d_bgdatL0.bin" % (1 + i)
            courseDataFileL1Name = "course/course%d_bgdatL1.bin" % (1 + i)
            courseDataFileL2Name = "course/course%d_bgdatL2.bin" % (1 + i)

            cd_file = cls._file[i]
            cd_file.load(
                i,
                endianness,
                SharcTryGetFile(archive, courseDataFileName  ),
                SharcTryGetFile(archive, courseDataFileL0Name),
                SharcTryGetFile(archive, courseDataFileL1Name),
                SharcTryGetFile(archive, courseDataFileL2Name)
            )

            if not inner_archive:
                read_files.add(courseDataFileName)
                read_files.add(courseDataFileL0Name)
                read_files.add(courseDataFileL1Name)
                read_files.add(courseDataFileL2Name)

            if i == 0:
                if not cd_file.isValid():
                    raise ValueError("File 0 must be valid!")

            else:
                if not cd_file.isValid():
                    continue

            # print("Has file %d" % i)

            # for j in range(CD_FILE_ENV_MAX_NUM):
            #     env_name = cd_file.getEnvironment(j)
            #     if env_name:
            #         success = Bg.loadUnit(pack_arc, env_name)
            #         assert success
            #         read_files.add(env_name)

        cls._clearResData()

        entries = SharcReadEntries(pack_arc)
        for name, data in entries:
            if name not in read_files:
                cls._resData[name] = data

    @classmethod
    def save(cls) -> bytes:
        raise NotImplementedError
        return b''

    @classmethod
    def getCourseDataFile(cls, index: int) -> CourseDataFile:
        assert 0 <= index < CD_FILE_MAX_NUM
        return cls._file[index]
    
    @classmethod
    def _clearResData(cls) -> None:
        cls._resData.clear()
