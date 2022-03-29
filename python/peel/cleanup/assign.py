# Mocap Cleanup - Alastair Macleod 2016
# GPL License = http://www.gnu.org/licenses/gpl.txt 

from peel.cleanup import keyTools, datarate
from peel.util import curve
import maya.cmds as m


def getSourceRange(source, rangemode):
    '''
    Get the keyframe range from a maya object

    :param source: name of the source object to get get the range from
    :param rangemode: one of - all, spike, segment

    all - the entire source range (min, max)
    spike - searches outward from current frame a spike in the data 
    segment - searches outward for a gap in the keys

    Returns: (in, out)
    '''

    source_in = None
    source_out = None

    if rangemode not in ['all', 'spike', 'segment']:
        raise ValueError("Invalid range mode: " + rangemode)

    if not m.objExists(source):
        print(m.error("Source does not exist: " + source))

    source_rate = datarate.nodeRate(source)

    if source_rate is None:
        source_rate = datarate.guess(source)

    if source_rate is None:
        raise RuntimeError("No rate found for node")

    if rangemode == 'all':
        keys = m.keyframe(source, q=True, tc=True)
        source_in = min(keys)
        source_out = max(keys)

    if rangemode == 'spike':

        s = curve.currentSpikeSegment(source, source_rate)
        if s is None: return
        source_in, source_out = s

    if rangemode == 'segment':

        s = curve.currentSegmentOrGap(source, source_rate)
        if s is None or s[0] != 'segment':
            print("Skipping: " + str(source) + " (not currently in a segment)")
            return

        source_in, source_out = s[1]

    if source_in is None or source_out is None:
        print("Mode        " + rangemode)
        m.error("Could not determine range")
        return

    return source_in, source_out


def assign(source, target, rangemode, replacemode):
    ''' Assign a marker, copying from source to destination
    
    :param source: the source marker to copy data from
    :param target: the target marker to paste data on to
    :param replacemode: 'swap' or 'extract'
    :param rangemode: sett getSourceRange

    '''

    print("Assign: %s ---> %s  Modes:  %s/%s" % (source, target, rangemode, replacemode))

    if not m.objExists(target):
        print("renaming: " + source + " as " + target)
        m.rename(source, target)
        return True

    if rangemode == 'gap':

        # fill the gap in the target using keys from the source

        s = curve.currentSegmentOrGap(target, datarate.nodeRate(source))
        if s is None or s[0] != 'gap':
            print("Skipping: " + str(source) + " (not currently in a gap)")
            return

        # values of surrounding keyframes
        source_in, source_out = s[1]
        # contract range
        source_in = source_in + 0.5
        source_out = source_out - 0.5

    else:

        source_in, source_out = getSourceRange(source, rangemode)
        # expand to
        source_in = source_in - 0.5
        source_out = source_out + 0.5

    print("In: %f  Out: %f" % (source_in, source_out))

    if replacemode == 'swap':
        keyTools.swap((source, target), source_in, source_out)

    if replacemode == 'extract':
        # copy the segment over, any clashing keys on the marker will be removed as unlabelled
        keyTools.extract_range(target, source_in, source_out)
        m.cutKey(source, t=(source_in, source_out))
        m.pasteKey(target, option='replace')

    keyTools.set_active_keys(source, delete=True)
    keyTools.set_active_keys(target)
    # m_cmds.select(target)

    m.dgdirty(a=True)
