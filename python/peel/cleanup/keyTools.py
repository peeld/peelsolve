# Mocap Cleanup - Alastair Macleod 2016
# GPL License = http://www.gnu.org/licenses/gpl.txt 

import maya.cmds as m
import maya.mel as mel

import bisect
from peel.cleanup import datarate
from peel.util import curve
import math


def find_animated_node(nodes):
    """ find all the nodes in the list that have more than two keys """

    for i in nodes:
        keys = m.keyFrame(i)
        if keys is None or len(keys) < 2:
            continue
        return keys
    return None


def zero_anim(nodes=None, channels=('tx', 'ty', 'tz')):
    """ move a clip on joints back to frame 1  - e.g. for timecoded data """

    if nodes is None: nodes = m.ls(sl=True)
    if nodes is None or len(nodes) == 0:
        print("nothing nodes")
        return

    keys = m.keyframe(nodes, q=True)
    if keys is None or len(keys) == 0:
        print("No keys found")
        return

    offset_by = (min(keys) * -1) + 1
    print("Offsetting  %d " % offset_by)

    # offet the keys
    (win, pc) = progress_start("Zeroing...", len(nodes))
    for i in nodes:

        current_offset = 0

        if not progress_inc(pc): break

        # this command is VERY slow:
        # m_cmds.keyframe( i, r=True, tc= offsetBy )

        # this is faster:
        for ch in channels:
            c = curve.fcurve(i, ch)
            c.fetch()
            c.offset(offset_by)
            c.apply()

        # set a frame offset attribute on each node, for future reference
        if not m.objExists(i + ".frameOffset"):
            m.addAttr(i, ln="frameOffset", at="float")
        else:
            current_offset = m.getAttr(i + ".frameOffset")

        try:
            m.setAttr(i + ".frameOffset", offset_by + current_offset)
        except  RuntimeError:
            pass

    progress_end(win, pc)

    set_range()


def set_range():
    """ Set the playback range to the minimum/maximum keys on selected objects """

    sel = m.ls(sl=True)
    if sel is None or len(sel) == 0:
        print("Nothing selected")
        return

    keys = m.keyframe(sel, q=True)
    if keys is None or len(keys) == 0: return
    m.playbackOptions(min=math.floor(min(keys)), max=math.ceil(max(keys)))


def progress_start(title, size):
    """ create a progress bar with max value of size - returns (win, pc)"""

    if size == 0:
        return None, None
    win = m.window(title=title)
    m.columnLayout()
    pc = m.progressBar(maxValue=size, width=300)
    m.showWindow(win)
    m.progressBar(pc, e=True, bp=True, ii=True, status=title)
    return win, pc


def progress_inc(pc):
    """ update the progress """

    if pc is None: return
    if m.progressBar(pc, q=True, isCancelled=True): return False;
    m.progressBar(pc, e=True, step=1)
    return True


def progress_end(win, pc):
    """ end the progress """

    if win is None or pc is None: return
    m.progressBar(pc, e=True, ep=True)
    m.deleteUI(win)


def filter_selected_nodes():
    """ apply a default filter to the skelected objects (markers) """

    units = m.currentUnit(q=True, time=True)
    m.currentUnit(time="120fps")

    x = 0
    sel = m.ls(sl=True)

    (win, pc) = progress_start("Filtering", len(sel))

    for i in sel:
        if not progress_inc(pc): break
        kx = m.keyframe(i + ".tx", q=True)
        ky = m.keyframe(i + ".ty", q=True)
        kz = m.keyframe(i + ".tz", q=True)
        if kx is not None:
            mel.eval("peelFilter -st %f -et %f %s.tx" % (min(kx), max(kx), i))
        if ky is not None:
            mel.eval("peelFilter -st %f -et %f %s.ty" % (min(ky), max(ky), i))
        if kz is not None:
            mel.eval("peelFilter -st %f -et %f %s.tz" % (min(kz), max(kz), i))
    progress_end(win, pc)
    m.currentUnit(time=units)


def delete_animation(nattr):
    """ delete the animation on the node/attribute """

    for i in m.listConnections(nattr, s=True, d=False):
        if i.startswith('animCurve'):
            m.delete(i)


def set_selected_active():
    """ set active keys on the current selection """

    for i in m.ls(sl=True): set_active_keys(i)


def fix_name(node):
    fixed = m.ls(node, type='transform')
    if len(fixed) == 0:
        raise ValueError("Node does not exist: " + str(node))

    if len(fixed) > 1:
        raise ValueError("More than one node named: " + str(node))

    return fixed[0]


def set_active_keys(node, delete=False):
    print("Setting active on : " + str(node) + " delete is: " + str(delete))

    """
    sets the value of .actve attribute on a peel marker to being 1 or 0 if data
    exists one the translate.x channel.  This is used to change the display of
    the marker from a square to a cross in the display.
    """

    try:
        node = fix_name(node)
    except RuntimeError as e:
        m.warning(str(e))
        return

    if type(node) not in [str, unicode]: raise ValueError("Invalid type for setActiveKeys: " + str(type(node)))

    interval = datarate.get(node)
    if interval is None:
        m.warning("No interval for node while setting active keys: " + str(node))
        return

    if m.nodeType(node) != "transform":
        m.warning("Not a transform while setting active: " + str(node) + '  ' + str(m.nodeType(node)))
        return

    if not m.objExists(node):
        m.warning("Object does not exist while setting active: " + str(node))
        return

    if not m.objExists(node + ".active"):
        m.warning("Object does not have active channel while setting active keys: " + str(node))
        return

    # check the tx time values
    times = m.keyframe(node + ".tx", q=True, timeChange=True)
    if times is None:

        print("No keys on: " + str(node))

        conn = m.listConnections(node, d=True, s=False, type='PeelLine', p=True)
        if delete and (conn is None or len(conn) == 0):
            m.delete(node)
        else:
            m.cutKey(node + '.active')
            m.setAttr(node + '.active', 0)
        return

    times = sorted(times)

    if len(times) == 0: return

    cdata = curve.fcurve(node, "atv")

    # iterate over each frame and set the active channel when the state changes (stepped)
    last_frame = None

    for frame in times:

        if last_frame is None:
            # first frame
            cdata.data[frame - interval] = 0.0
            cdata.data[frame] = 1.0
        else:
            gapsize = frame - last_frame

            if abs(gapsize - interval) > 0.1:
                # print str( gapsize ) + '   ' + str(interval) + '  ' + str(  abs(gapsize - interval) ) + '    ' + str(frame)
                cdata.data[last_frame + interval] = 0.0
                cdata.data[frame] = 1.0

        last_frame = frame

    cdata.data[times[-1] + interval] = 0

    cdata.apply(stepped=True)

    m.dgdirty(node)


def goto_next_gap():
    """ Moves the timeline to the next gap in .tx """

    gap = next_gap()
    if gap is not None:
        (start, end) = gap
        m.currentTime(start + (end - start) / 2)


def next_gap(item=None, current_time=None):
    """
    Finds the next gap in the current .tx of the current selection
    @param item: the node to search on
    @param step: the expected spacing between the keys, if null a sample will be taken
    @param current_time: time to start the search
    @param maxSize: maximum gap size, useful for finding small gaps
    """

    try:
        if item is None:
            item = get_item()
        if item is None:
            return
    except ValueError as e:
        print("Could not find next gap: " + str(e))
        return

    step = datarate.get(item)
    times = sorted(m.keyframe(item + ".tx", q=True))

    if current_time is None: current_time = m.currentTime(q=True)

    # for each key-time
    for i in range(0, len(times) - 1):

        if times[i] < current_time or times[i + 1] - times[i] <= step * 1.95:
            continue
        return times[i], times[i + 1]

    return None


def select_current(id=""):
    """ Select the 'current' working marker, as defined by setCurrent (optionVar) """

    currentItem = m.optionVar(q="mocap_currentItem" + id)
    m.select(currentItem, replace=True)


def set_current(id="", nodeName=None):
    """
    Store what the current working marker is, used for future 'paste' actions, saved as an optionVar
    @param id: the id of the slot to save to
    @param nodeName: the name of the node to save, or if None will use the current selection

    """
    if nodeName is None:
        sel = m.ls(sl=True)
        if (len(sel) != 1):
            print("Select one item to use")
            return
        nodeName = sel[0]

    print("Setting current #" + id + " to " + nodeName)

    m.optionVar(sv=["mocap_currentItem" + id, nodeName])


def key_current_to_match(id=""):
    """ key current to being at the same position as selected[0] """

    currentItem = m.optionVar(q="mocap_currentItem" + id)
    sel = m.ls(sl=True)
    if len(sel) == 0:
        print("Select an item")
        return

    tr = m.xform(sel[0], q=True, t=True, ws=True)
    m.setKeyframe(currentItem + ".translateX", value=tr[0])
    m.setKeyframe(currentItem + ".translateY", value=tr[1])
    m.setKeyframe(currentItem + ".translateZ", value=tr[2])


def move_to_current(id=""):
    """ move all the keys on selected[0] to current item """

    sel = m.ls(sl=True)
    if (len(sel) != 1):
        print("Select one item to use")
        return
    current_item = m.optionVar(q="mocap_currentItem" + id)

    if current_item is None or current_item == 0:
        print("No current item #" + id)
        return

    # move sel[0] to temp
    print("Copying keys from: %s" % sel[0])
    anim_curves = m.keyframe(q=True, name=True)
    select_times = m.keyframe(anim_curves[0], q=True, sl=True, timeChange=True)
    if select_times is None or len(select_times) == 0:
        print("No keys selected, moving all keys")
        m.select(current_item, add=True)
        move_first_to_second()
        m.select(current_item)
        return

    box = create_box()  # temp item, current not needed
    print("Pasting %d keys on to: %s" % (len(select_times), box))
    for i in select_times:
        m.cutKey(sel[0], time=(i, i))
        m.pasteKey(box[0], time=(i, i))

    # move currentItem to sel[0]
    print("Moving keys from: %s" % (current_item))
    for i in select_times:
        n = m.cutKey(current_item, time=(i, i))
        if n > 0: m.pasteKey(sel[0], time=(i, i))

    # move temp to currentItem 
    print("Moving from temp to currentItem")
    for i in select_times:
        n = m.cutKey(box, time=(i, i))
        if n > 0: m.pasteKey(current_item, time=(i, i))

    m.delete(box)

    set_active_keys(current_item)

    m.select(current_item)


def move_first_to_second():
    """  move the keys on selected[0] to selected[1] """
    sel = m.ls(sl=True)
    if len(sel) < 2:
        print("Select at least two items to use")
        return

    keys = []
    for i in sel:
        kz = m.keyframe(i + ".tx", q=True)
        if kz is not None: keys.append(set(kz))

    count = 0
    for i in keys: count = count + len(i)

    if count != len(set.union(*keys)):
        ret = m.confirmDialog(m='You may have overlapping keys... continue?', b=['yes', 'no', 'skip'])

        if ret not in ['yes', 'skip']: return

        if ret == 'skip':
            # do not copy any keys if there is one already on the target
            for i in range(len(sel) - 1):
                for k in keys[i]:
                    if k in keys[-1]: continue
                    m.cutKey(sel[i], time=(k, k))
                    m.pasteKey(sel[-1], option='merge')
            return

    for i in sel[:-1]:
        if m.cutKey(i) > 0: m.pasteKey(sel[-1], option="merge")
        m.delete(i)

    m.select(sel[-1])

    set_active_keys(sel[-1])


def cut_after():
    """ cut the keys from current to end on selected """

    cur = m.currentTime(q=True)
    end = m.playbackOptions(q=True, max=True)
    sel = m.ls(sl=True)
    for i in sel: m.cutKey(i, time=(cur, end))


def cut_before():
    """ cut the keys from 0 to current """

    cur = m.currentTime(q=True)
    start = m.playbackOptions(q=True, min=True)
    sel = m.ls(sl=True)
    for i in sel: m.cutKey(i, time=(0, cur))


def swap_all(item1=None, item2=None):
    """ swap the data on items1/2 """

    swap(None, 'all', 'all')


def swap(markers=None, inPoint=None, outPoint=None):
    """ swap data on two markers, between the in and out
        @param markers: list of 2 markers to swap, defaults to selection
        @param inPoint: frame to start swap, defaults to current frame
        @param outPoint: frame to end swap, defaults to last frame """

    if markers is None:
        markers = m.ls(sl=True)
        if len(markers) != 2:
            print("select two markers to swap")
            return

    # these do not need to be sorted
    keysA = m.keyframe(markers[0], q=True)
    keysB = m.keyframe(markers[1], q=True)

    if inPoint is None: inPoint = m.currentTime(q=True)
    if outPoint is None: outPoint = max(keysA)

    # cut the keys from markers 0
    if inPoint == 'all':
        count = m.cutKey(markers[0])
    else:
        count = m.cutKey(markers[0], time=(inPoint, outPoint))

    loc = None

    if count > 0:
        # paste the key to a temp object
        loc = create_box(boxName="temp")  # temp, current not needed
        m.pasteKey(loc[0], option="replace")

    # cut the keys from markers 1 and paste on to markers 0
    if inPoint == 'all':
        count = m.cutKey(markers[1])
    else:
        count = m.cutKey(markers[1], time=(inPoint, outPoint))

    if count > 0: m.pasteKey(markers[0], option="replace")

    if loc != None:
        # cut the keys from the temp object (markers 0 data) and paste on to markers 1
        m.cutKey(loc[0])
        m.pasteKey(markers[1], option="replace")

        # delete the temp object
        m.delete(loc)


def create_temp_group(current):
    """ create a temporary node with the same transform level as parent """

    par = m.listRelatives(current, p=True)
    if par is None or len(par) == 0: return None

    if par[0] == "extracted" or par[0].endswith("|extracted"):
        return par[0]

    if m.objExists(par[0] + "|extracted"):
        return par[0] + "|extracted"

    node = m.group(em=True, name="extracted", p=par[0])
    m.setAttr(node + ".t", l=True)
    m.setAttr(node + ".r", l=True)
    m.setAttr(node + ".s", l=True)

    return node


def create_box(boxName="unlabeled", current=None, parent=None):
    """ creates a new unlabelled marker 
    @param boxName: the name of the marker to create, defaults to 'unlabeled'
    @param current: name of the marker to copy the data rate.  New marker will be sibling.
    @returns : ( transform, shape )
    """

    rate = None
    displayMode = None
    size = None

    sel = m.ls(sl=True)

    if current is not None:
        parent = create_temp_group(current)
        if m.objExists(current + ".C3dRate"): rate = m.getAttr(current + ".C3dRate")
        if m.objExists(current + ".displayMode"): displayMode = m.getAttr(current + ".displayMode")
        if m.objExists(current + ".size"): size = m.getAttr(current + ".size")

    if parent is not None:
        transform = m.createNode("transform", name=boxName, p=parent)
    else:
        transform = m.createNode("transform", name=boxName)

    box = m.createNode("peelSquareLocator", parent=transform, n=boxName + "Shape")

    if m.objExists(box + ".active"):
        m.addAttr(transform, at="bool", sn="atv", ln="active", k=True)
        m.connectAttr(transform + ".active", box + ".active")

    if rate is not None:
        m.addAttr(transform, at="double", ln="C3dRate", k=False)
        m.setAttr(transform + ".C3dRate", rate)

    if displayMode is not None: m.setAttr(box + ".displayMode", displayMode)
    if size is not None: m.setAttr(box + ".size", size)

    m.select(sel)

    return (transform, box)


def cut_and_fill():
    """ cut the selected keys out and linear fill the gap """

    try:
        item = get_item()
    except ValueError as e:
        print("Unable to cut and fill: " + str(e))
        return

    times = m.keyframe(item, q=True, sl=True)
    m.cutKey(item, time=(min(times), max(times)))
    (start, end) = find_current_gap(item, min(times))
    fill_gap_linear(item, start=start, end=end)


def selected_keys():
    out = set()
    anim_curves = m.keyframe(q=True, name=True)
    for anim_curve in anim_curves:
        select_times = m.keyframe(anim_curve, q=True, sl=True, timeChange=True)
        if select_times is None: continue
        out.update(select_times)

    return list(out)


def extract_selected():
    """
    select a few keys (bad?) and extract them on to a temp locator    
    """

    sel = m.ls(sl=True)
    if sel is None or len(sel) == 0:
        m.warning("Nothing selected to extract from")
        return

    if len(sel) > 1:
        m.error("Error: more than one object selected while extracting")
        return None

    select_times = selected_keys()
    if select_times is None or len(select_times) == 0:
        m.error("Select some keys to extract")
        return

    m.selectKey(clear=True);

    loc = create_box(current=sel[0])

    for i in select_times:
        m.cutKey(sel[0], time=(i, i))
        m.pasteKey(loc[0], time=(i, i))
        if m.objExists(sel[0] + ".active"):
            m.setAttr(sel[0] + ".active", 0)

    set_active_keys(loc[0])

    m.select(sel)

    for i in sel:
        set_active_keys(i)
    set_active_keys(loc[0])
    set_active_keys(sel[0])

    return loc


def extract_range(node, begin, end, inclusive=True):
    """ extract a range of keyframes on to a new locator """

    keys = m.keyframe(node, q=True, t=(begin, end))
    if keys is None or len(keys) == 0: return None

    loc = create_box(node + "_cut", current=node)
    m.cutKey(node, time=(begin, end))
    m.pasteKey(loc[0], option="replace")
    if m.objExists(loc[0] + ".active"):
        m.setKeyframe(loc[0] + ".active", t=begin, v=0)
        m.setKeyframe(loc[0] + ".active", t=end, v=0)

    set_active_keys(loc[0])
    set_active_keys(node)

    return loc


def extract_after():
    """ extract all the keys after the current frame """

    sel = m.ls(sl=True)
    cur = m.currentTime(q=True)
    loc = None
    for i in sel:
        keys = m.keyframe(i, q=True)
        if keys is None: continue
        m.cutKey(i, time=(cur, max(keys)))
        loc = create_box(current=i)
        m.pasteKey(loc[0], option="replace")

    m.select(sel)

    for i in sel:
        set_active_keys(i)

    if loc:
        set_active_keys(loc[0])


def extract_before():
    """ extract all the keys after the current frame """

    sel = m.ls(sl=True)
    cur = m.currentTime(q=True)
    loc = None
    for i in sel:
        keys = m.keyframe(i, q=True)
        if keys is None: continue
        m.cutKey(i, time=(min(keys), cur))
        loc = create_box(current=i)
        m.pasteKey(loc[0], option="replace")

    m.select(sel)

    for i in sel:
        set_active_keys(i)

    if loc:
        set_active_keys(loc[0])


def trim_clip(pad=0):
    """ Delete all keys before and after playback range on selected objects """

    sel = m.ls(sl=True)
    tmin = m.playbackOptions(q=True, min=True)
    tmax = m.playbackOptions(q=True, max=True)
    (win, pc) = progress_start("Trimming", len(sel))
    for i in sel:
        if not progress_inc(pc): break
        keys = m.keyframe(i, q=True)
        if keys is None: continue
        if len(keys) == 1: continue

        trim_in = tmin - 1 - pad
        trim_out = tmax + 1 + pad

        if min(keys) < trim_in: m.cutKey(i, time=(min(keys), trim_in))
        if max(keys) > trim_out: m.cutKey(i, time=(trim_out, max(keys)))
    m.select(sel)
    progress_end(win, pc)


def split_parts():
    """ split the data in to parts based on any gaps in the data """

    sel = m.ls(sl=True)

    for s in sel:
        keys = m.keyframe(s + ".translateX", q=True)
        if keys is None:
            print("No keys for: " + s)
            continue

        last_key = min(keys)
        clip_start = min(keys)
        for i in keys[1:]:
            diff = i - last_key
            if diff > 1:
                print("Clip at : %f - %f (%f)" % (clip_start, last_key, diff))
                loc = extract_range(s, clip_start, last_key)
                for xx in range(0, 10):
                    length = last_key - clip_start
                    if xx <= length < xx + 1:
                        if not m.objExists("|SMALL%d" % i):
                            print("creating group SMALL%d" % i)
                            m.group(em=True, name="SMALL%d" % i)
                        else:
                            print("Group exists SMALL%d" %i)
                        m.parent(loc[0], "|SMALL%d" % i)
                clip_start = i
            last_key = i


def select_empty(threshold=4):
    """ select unlabeled nodes that contain little or no data, so they can be deleted. """
    m.select(cl=True)
    nlabs = m.ls("extracted|*", type="transform")
    if nlabs is None or len(nlabs) == 0: return

    for i in unlabs:

        anim_curves = m.keyframe("%s.tx" % i, q=True, name=True)
        if anim_curves is None or len(anim_curves) == 0:
            m.select(i, add=True)
            continue
        times = m.keyframe(anim_curves[0], q=True, timeChange=True)
        if len(times) < threshold:
            m.select(i, add=True)


def all_markers():
    markers = m.ls(type='peelSquareLocator', l=True)
    if markers is None: return []
    return [m.listRelatives(i, p=True, f=True)[0] for i in markers]


def toggle_connect_vis(markers=None, force=None):
    """ toggle connects the marker visibility to the active value. (or sets the connection if force is set) """

    if markers is None: markers = m.ls(type="peelSquareLocator")
    if markers is None: return
    if len(markers) == 0: return

    markerList = []

    # verify nodes are peelSquareLocators
    for i in markers:

        if m.nodeType(i) == "transform":
            children = m.listRelatives(i, c=True, s=True, f=True)
            if children is None: continue
            for j in children:
                if m.nodeType(j) == "peelSquareLocator":
                    markerList.append(j)

        if m.nodeType(i) == "peelSquareLocator":
            markerList.append(i)

    if len(markerList) == 0: return

    if force is not None:

        connect_vis(markerList, force)

    else:

        # get the current state of first marker for the toggle
        connP = m.listConnections(markerList[0] + ".active", s=True, p=True)
        connN = m.listConnections(markerList[0] + ".active", s=True)

        if m.isConnected(connP[0], connN[0] + ".v"):
            connect_vis(markerList, False)
        else:
            connect_vis(markerList, True)


def connect_vis(markers, connect=True):
    """
    Make a connections between a square transform .active channel to the 
    .visibility channel, so the marker is hidden when not active
    """
    for i in markers:

        if m.nodeType(i) == 'peelSquareLocator':
            i = m.listRelatives(i, p=True)[0]

        if connect:
            try:
                if not m.isConnected(i + ".active", i + ".v"):
                    m.connectAttr(i + ".active", i + ".v", f=True)
            except RuntimeError as e:
                print("Could not connect: " + i + ' ' + str(e))
        else:
            try:
                if m.isConnected(i + ".active", i + ".v"):
                    m.disconnectAttr(i + ".active", i + ".v")
                m.setAttr(i + ".v", 1)
            except RuntimeError as e:
                print("Could not unconnect: " + i + ' ' + str(e))


def fill_gap(fill_obj=None, src_obj=None):

    """
    This is an older method of filling gaps - it uses find current gap, which may be slow
    """
    if fill_obj is None or src_obj is None:
        sel = m.ls(sl=True)

        if len(sel) == 1:
            fill_gap_linear(sel[0])
            return

        if len(sel) != 2:
            print("Select one object to linear fill, two objects to copy fill the gap")
            return

        fill_obj = sel[1]
        src_obj = sel[0]

    try:
        (start, end) = find_current_gap(fill_obj)
    except ValueError:
        print("Could not find gap to fill")
        return

    # get the values for the keys at the gap
    gapval = [
        m.keyframe(fill_obj + ".tx", q=True, time=(start, end), vc=True),
        m.keyframe(fill_obj + ".ty", q=True, time=(start, end), vc=True),
        m.keyframe(fill_obj + ".tz", q=True, time=(start, end), vc=True)]

    # get the curve to paste in
    curve = [
        m.keyframe(src_obj + ".tx", q=True, time=(start, end), vc=True, tc=True),
        m.keyframe(src_obj + ".ty", q=True, time=(start, end), vc=True, tc=True),
        m.keyframe(src_obj + ".tz", q=True, time=(start, end), vc=True, tc=True)]

    startOffset = [
        gapval[0][0] - curve[0][1],
        gapval[1][0] - curve[1][1],
        gapval[2][0] - curve[2][1]]

    endOffset = [
        gapval[0][-1] - curve[0][-1],
        gapval[1][-1] - curve[1][-1],
        gapval[2][-1] - curve[2][-1]]

    chan = [".tx", ".ty", ".tz"]

    for i in range(0, 3):
        it = iter(curve[i])
        for k, v in zip(it, it):
            progress = (k - start) / (end - start)
            addval = startOffset[i] + progress * (endOffset[i] - startOffset[i])
            m.setKeyframe(fill_obj + chan[i], t=k, value=v + addval)
            if i == 1 and m.objExists(fill_obj + ".active"):
                m.setKeyframe(fill_obj + ".active", t=k, value=1)

    set_active_keys(fill_obj)


def fill_gap_linear(item=None, step=None, start=None, end=None):
    try:
        if item is None: item = get_item()
        if step is None: step = datarate.get(item)
        if start is None or end is None:
            (start, end) = find_current_gap(item)

    except ValueError as e:
        print("Could not fill linear gap: " + str(e))
        return

    fill_obj = item

    gapval = [
        m.keyframe(fill_obj + ".tx", q=True, time=(start, end), vc=True),
        m.keyframe(fill_obj + ".ty", q=True, time=(start, end), vc=True),
        m.keyframe(fill_obj + ".tz", q=True, time=(start, end), vc=True)]

    chan = [".tx", ".ty", ".tz"]

    ktime = 0
    for i in range(0, 3):
        ktime = start + step
        while ktime <= end - step:
            progress = (ktime - start) / (end - start)
            kvalue = (gapval[i][-1] - gapval[i][0]) * progress + gapval[i][0]
            m.setKeyframe(fill_obj + chan[i], t=ktime, value=kvalue)
            ktime = ktime + step

    set_active_keys(fill_obj)


def get_item():
    sel = m.ls(sl=True)
    if len(sel) == 0: raise ValueError("Please select at least one item")
    return sel[-1]


def get_items():
    items = m.ls(sl=True)
    if len(items) == 0: raise ValueError("Nothing selected")
    return items


# This is a newer method of filling gaps 
def fill(src=None, dst=None):
    if src is None:
        sel = m.ls(sl=True)

        if len(sel) == 0:
            m.error("Nothing selected")
            return

        if len(sel) > 1:
            dst = sel[0]
            src = sel[1]
        else:
            src = sel[0]

    if not dst:
        fill_channel(src + '.tx')
        fill_channel(src + '.ty')
        fill_channel(src + '.tz')
        set_active_keys(src)
        return

    fill_channel(src + '.tx', dst + '.tx')
    fill_channel(src + '.ty', dst + '.ty')
    fill_channel(src + '.tz', dst + '.tz')
    set_active_keys(src)
    set_active_keys(dst)


def fill_channel(gapChannel, fillChannel=None, currentTime=None):
    if currentTime is None:
        currentTime = m.currentTime(q=True)

    # get keyframes for the channel that has the gap
    gap_curve_obj = curve.fcurve(*gapChannel.split('.'))
    gap_curve_obj.fetch()
    gap_curve_keys = gap_curve_obj.keys()  # returns the time values as a sorted list

    # find the left and right keys of the gap (prev, next)
    # bisect_left returns the index in the keys list 
    gap_index = bisect.bisect_left(gap_curve_keys, currentTime)
    gap_left_key = gap_curve_keys[gap_index - 1]
    gap_right_key = gap_curve_keys[gap_index]
    gap_range_key = gap_right_key - gap_left_key

    gap_left_value = gap_curve_obj[gap_left_key]
    gap_right_value = gap_curve_obj[gap_right_key]

    # how much does the data change within the gap
    gap_range_value = gap_curve_obj[gap_right_key] - gap_curve_obj[gap_left_key]

    if fillChannel is None:

        print("Filling gaps in: %s from %g to %g" % (gapChannel, prev, next))

        rate = datarate.channelRate(gapChannel)
        if rate is None: raise RuntimeError("Could not determine data rate")

        i = prev + rate
        while i < next:
            normalized = (i - gap_left_key) / (next - gap_right_key)
            newval = normalized * gapRange + gap_curve_obj[prev]
            print("%s  %f  %f" % (gapChannel, newval, i))
            m.setKeyframe(gapChannel, v=newval, t=i)
            i += rate

    else:

        print("Filling gaps in: %s with data from %s" % (gapChannel, fillChannel))

        # get the data to fill with
        fill_curve_obj = curve.fcurve(*fillChannel.split('.'))
        fill_curve_obj.fetch()
        fill_curve_keys = fill_curve_obj.keys()

        # find the start end of the data being used to fill with 
        fill_left_index = bisect.bisect_left(fill_curve_keys, gap_left_key)
        fill_right_index = bisect.bisect_right(fill_curve_keys, gap_right_key) - 1

        if fill_right_index > len(fill_curve_keys):
            m.error("Not enough keys for fill")
            return

        if fill_left_index + 1 == fill_right_index:
            m.error("No keys to fill")
            return

        fill_left_key = fill_curve_keys[fill_left_index]
        fill_right_key = fill_curve_keys[fill_right_index]
        fill_range_key = fill_right_key - fill_left_key

        fill_left_value = fill_curve_obj[fill_left_key]
        fill_right_value = fill_curve_obj[fill_right_key]
        fill_range_value = fill_right_value - fill_left_value

        # print "Gap:         %f-%f  Range: %f" % (gap_left_key,    gap_right_key,    gap_range_key)
        # print "Gap Values:  %f-%f  Range: %f" % (gap_left_value,  gap_right_value,  gap_range_value)
        # print "Fill:        %f-%f  Range: %f" % (fill_left_key,   fill_right_key,   fill_range_key)
        # print "Fill Values: %f-%f  Range: %f" % (fill_left_value, fill_right_value, fill_range_value)

        for i in range(fill_left_index, fill_right_index):
            this_key = fill_curve_keys[i]
            key_progress = (this_key - gap_left_key) / gap_range_key

            this_value = fill_curve_obj[this_key]
            normalized_fill = this_value - fill_left_value - (key_progress * fill_range_value)

            new_value = gap_left_value + normalized_fill + key_progress * gap_range_value

            m.setKeyframe(gapChannel, v=new_value, t=this_key)


def find_current_gap(node, currentTime=None):
    if currentTime is None:
        currentTime = m.currentTime(q=True)

    # find start and end of the gap
    gapkeys = sorted(m.keyframe(node + ".tx", q=True))
    prev = None
    for i in gapkeys:
        if i > currentTime:
            return (prev, i)
        prev = i

    raise ValueError("Could not find current range")


def copy_fill_gap(source, target):
    rate = datarate.guess(target)
    ret = curve.currentSegmentOrGap(target + '.tx', rate)
    if ret is None:
        print("Could not find gap on " + str(target))
        return

    mode, gap = ret

    if mode == 'segment':
        print("No gap to fill for " + target)
        return

    a, b = gap

    keys = m.keyframe(source + ".tx", q=True, tc=True)
    if keys is None or len(keys) == 0:
        print("No keys to copy from on " + str(source))
        return

    keys = sorted(keys)

    if a is None: a = min(keys)
    if b is None: b = max(keys)

    keyRange = m.keyframe(source + ".tx", t=(a, b), q=True)
    if keyRange is None or len(keyRange) == 0:
        print("No keys in range to copy from %s   %g-%g" % (source, a, b))
        return

    for ch in ['tx', 'ty', 'tz']:
        m.cutKey(source + '.' + ch, t=(a, b))
        m.pasteKey(target + '.' + ch, option='merge')

    set_active_keys(source)
    set_active_keys(target)


def set_out():
    m.playbackOptions(max=m.currentTime(q=True))


def set_in():
    m.playbackOptions(min=m.currentTime(q=True))


def reset_in_out():
    m.playbackOptions(min=m.playbackOptions(q=True, ast=True))
    m.playbackOptions(max=m.playbackOptions(q=True, aet=True))
