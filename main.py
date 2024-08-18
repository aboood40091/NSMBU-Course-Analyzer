from time import gmtime, strftime
import os
from typing import Tuple, Dict, Set, Optional, List

from courseData import CourseData, CD_FILE_MAX_NUM, NextGoto, AreaData, CourseDataFile


TAreaID = Tuple[int, int]
TNextGotoID = Tuple[int, int]
TAreaTree = Dict[TAreaID, Set[TAreaID]]


logBuffer = []
logToFile = True
enableTestLog = False


def warn(*args) -> None:
    log("Warning:", *args)


def log_test(*args, **kwargs) -> None:
    if enableTestLog:
        print(*args, **kwargs)


def log(*args) -> None:
    if logToFile:
        global logBuffer
        logBuffer.extend((' '.join(map(str, args)), '\n'))
    else:
        print(*args)


def now() -> str:
    return strftime("%Y-%m-%d %H.%M.%S", gmtime())


def AreaContainsNextGoto(area: AreaData, nextGoto: NextGoto, iAreaID: int) -> bool:
    return (area.offset__x <= nextGoto.offset__x <= area.offset__x + area.size__x and \
            area.offset__y <= nextGoto.offset__y <= area.offset__y + area.size__y) or nextGoto.area == iAreaID


def FindContainmentArea(file: CourseDataFile, nextGoto: NextGoto) -> Optional[AreaData]:
    assert file.isValid()
    for area in file.getAreaData():
        if AreaContainsNextGoto(area, nextGoto, area.ID):
            return area

    return None


explored_nextGoto: Set[TNextGotoID] = set()
isCoinOrBoost = False


def explore_area(areas: TAreaTree, areaID: TAreaID) -> None:
    if areaID in areas:
        adjacency = areas[areaID]
    else:
        adjacency = set()
        areas[areaID] = adjacency

    file = CourseData.getCourseDataFile(areaID[0])
    if not file.isValid():
        warn("Trying to visit file %d area %d, but file does not exist!" % areaID)
        return
    
    area = file.getAreaDataByID(areaID[1])
    if area is None:
        warn("Trying to visit file %d area %d, but area does not exist!" % areaID)
        return
    
    for nextGoto in file.getNextGoto():
        log_test("Test: file %d area %d, area %d nextGoto %d" % (*areaID, nextGoto.area, nextGoto.ID))
        if not AreaContainsNextGoto(area, nextGoto, areaID[1]):
            continue

        if nextGoto.flag & 0x80:
            continue

        dstFile = nextGoto.destination__file
        if dstFile <= 0:
            dstFile = areaID[0]
        else:
            dstFile -= 1
            if dstFile == areaID[0]:
                warn("File %d, area %d: NextGoto %d leads to the same file, but uses file ID explicitly instead of 0." % (*areaID, nextGoto.ID))

        dstAreaID = explore_nextGoto(areas, (dstFile, nextGoto.destination__next_goto), nextGoto.destination__file == 0 and nextGoto.destination__next_goto == 0)
        if dstAreaID is not None:
            adjacency.add(dstAreaID)

    for i, actor in enumerate(file.getMapActorData()):
        actorAsNextGotoID = (areaID[0], 0x10000 | i)
        if actorAsNextGotoID in explored_nextGoto:
            continue
        else:
            explored_nextGoto.add(actorAsNextGotoID)

        if not AreaContainsNextGoto(area, actor, areaID[1]):
            continue

        if actor.type == 424:
            dstFile = actor.settings_0 >> 8 & 0xFF
            if dstFile <= 0:
                dstFile = areaID[0]
            else:
                dstFile -= 1
                # if dstFile == areaID[0]:
                #     warn("File %d, area %d: Pipe Cannon to Airship leads to the same file, but uses file ID explicitly instead of 0." % areaID)

            dstAreaID = explore_nextGoto(areas, (dstFile, actor.settings_0 & 0xFF))
            if dstAreaID is not None:
                adjacency.add(dstAreaID)

        if actor.type == 497:
            dstFile = actor.settings_0 & 0xFF
            if dstFile <= 0:
                dstFile = areaID[0]
            else:
                dstFile -= 1
                # if dstFile == areaID[0]:
                #     warn("File %d, area %d: Final Bowser Battle Controller leads to the same file, but uses file ID explicitly instead of 0." % areaID)

            dstFileObj = CourseData.getCourseDataFile(dstFile)
            if dstFileObj.isValid():
                dstAreaID = explore_nextGoto(areas, (dstFile, dstFileObj.getOptions().start_next_goto_coin_boost if isCoinOrBoost else dstFileObj.getOptions().start_next_goto))
                if dstAreaID is not None:
                    adjacency.add(dstAreaID)
            else:
                warn("Trying to visit file %d through Final Bowser, but file does not exist!" % dstFile)


def explore_nextGoto(areas: TAreaTree, nextGotoID: TNextGotoID, suppress_warn: bool = False) -> Optional[TAreaID]:
    if nextGotoID in explored_nextGoto:
        return

    explored_nextGoto.add(nextGotoID)
    log_test("File %d nextGoto %d" % (nextGotoID[0], nextGotoID[1]))

    file = CourseData.getCourseDataFile(nextGotoID[0])
    if not file.isValid():
        warn("Trying to visit file %d nextGoto %d, but file does not exist!" % nextGotoID)
        return None

    nextGoto = file.getNextGotoByID(nextGotoID[1])
    if nextGoto is None:
        if not suppress_warn:
            warn("Trying to visit file %d nextGoto %d, but nextGoto does not exist!" % nextGotoID)
        return None
    
    area = FindContainmentArea(file, nextGoto)
    if area is None:
        warn("Trying to visit file %d nextGoto %d, but nextGoto is not contained in any area!" % nextGotoID)
        return None
    
    dstAreaID = (nextGotoID[0], area.ID)
    explore_area(areas, dstAreaID)
    return dstAreaID


def findVisitableAreas() -> Tuple[TAreaTree, Optional[TAreaTree]]:
    global explored_nextGoto
    global isCoinOrBoost

    visitable_areas: TAreaTree = {}
    visitable_areas_cb: Optional[TAreaTree] = None
    
    for i in range(CD_FILE_MAX_NUM):
        file = CourseData.getCourseDataFile(i)
        if not file.isValid():
            continue
        for area in file.getAreaData():
            log_test("Has File %d area %d" % (i, area.ID))

    for i in range(CD_FILE_MAX_NUM):
        file = CourseData.getCourseDataFile(i)
        if not file.isValid():
            continue
        for nextGoto in file.getNextGoto():
            log_test("Has File %d area %d nextGoto %d" % (i, nextGoto.area, nextGoto.ID))

    file0 = CourseData.getCourseDataFile(0)
    assert file0.isValid()

    nextGotoID = file0.getOptions().start_next_goto
    isCoinOrBoost = False
    explore_nextGoto(visitable_areas, (0, nextGotoID))
    explored_nextGoto.clear()

    nextGotoID = file0.getOptions().start_next_goto_coin_boost
    if nextGotoID != 0:
        visitable_areas_cb = {}
        isCoinOrBoost = True
        explore_nextGoto(visitable_areas_cb, (0, nextGotoID))
        isCoinOrBoost = False
        explored_nextGoto.clear()

    return visitable_areas, visitable_areas_cb


def findUnvisitableAreas(visitable_areas: TAreaTree) -> List[TAreaID]:
    ret: List[TAreaID] = []

    for fileID in range(CD_FILE_MAX_NUM):
        file = CourseData.getCourseDataFile(fileID)
        if not file.isValid():
            continue

        for area in file.getAreaData():
            areaID = (fileID, area.ID)
            if areaID not in visitable_areas:
                ret.append(areaID)

    return ret


def scanPath(path: str, isNSMBUDX: bool) -> None:
    for fname in os.listdir(path):
        file_path = os.path.join(path, fname)
        log("Loading:", file_path)
        CourseData.loadFromPack(file_path, isNSMBUDX)
        visitable_areas, visitable_areas_cb = findVisitableAreas()
        if visitable_areas:
            log("Visitable areas tree:")
            log(visitable_areas)
        else:
            warn("Course not even enterable through start_next_goto!")
        if visitable_areas_cb is not None and not visitable_areas_cb:
            warn("Course not even enterable through start_next_goto_coin_boost!")

        unvisitable_areas = findUnvisitableAreas(visitable_areas)
        if visitable_areas_cb is not None:
            unvisitable_areas_cb = findUnvisitableAreas(visitable_areas_cb)
        else:
            unvisitable_areas_cb = None

        if unvisitable_areas:
            log("Unvisitable areas:")
            log('\n'.join(map(str, unvisitable_areas)))

        if unvisitable_areas_cb:
            log("Unvisitable areas in Coin Battle and Boost Rush specifically:")
            log('\n'.join(map(str, unvisitable_areas_cb)))

        log()


def main() -> None:
    scanPath('SARC', False)
    scanPath('SARC-RDash', False)
    scanPath('DX\\Course', True)
    scanPath('DX\\RDashRes\\Course', True)


if __name__ == '__main__':
    main()

    if logBuffer:
        logMsg = ''.join(logBuffer).encode('utf-8')
        with open(str(now()) + '.txt', 'wb') as outf:
            outf.write(logMsg)
