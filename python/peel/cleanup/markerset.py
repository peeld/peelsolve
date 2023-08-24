# Mocap Cleanup - Alastair Macleod 2016
# GPL License = http://www.gnu.org/licenses/gpl.txt 

import maya.cmds as m
import os.path
import os
import json
import shutil
import platform

"""
Representation of a markerset with a character prefix.  Motive, Arena and mocapclub.com data sets supported
Markersets are saved in the markerset directory in json format and loaded in to the Markerset objects by loadAll()
"""

markersets = {}


def markers_dir():

    appdata = None
    if platform.system() == "Windows":
        appdata = os.getenv("APPDATA")
    if platform.system() == "Darwin":
        appdata = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    if appdata is None:
        raise RuntimeError("Could not get a location to save markersets")

    return os.path.join(appdata, "PeelSolve2", "markersets")


def copy_default():
    global markersets

    user_dir = markers_dir()

    print("Creating user copy of markersets")

    # copy the installed (read only) markersets to the user directory
    d = os.path.join(os.path.split(__file__)[0], "markersets")
    d = os.path.abspath(d)
    if os.path.isdir(d):
        for i in os.listdir(d):
            shutil.copy(os.path.join(d, i), os.path.join(user_dir, i))


def load_all():
    global markersets

    markersets = {}

    user_dir = markers_dir()

    if not os.path.isdir(user_dir):
        os.makedirs(user_dir)
        copy_default()

    print("Loading markersets from: " + str(user_dir))

    for i in os.listdir(user_dir):

        mobj = Markerset()
        name = mobj.load(os.path.join(user_dir, i))
        if name is None:
            continue
        markersets[name] = mobj

    print("%d markersets loaded" % len(markersets))


def all():
    """ finds the prefixes and markersets in the scene
    :return: [ (prefix, markerset-name), ... ]
    """

    global markersets
    ret = []
    for pfx in prefixes():
        # for each possible prefix, guess the markerset
        setName = guess(pfx)
        if setName is None:
            continue
        mset = markersets[setName]
        ret.append((pfx, mset))
    return ret


def guess(prefix, items=None):
    """ find the markerset with the most matching markers, returns the name """

    global markersets

    if len(markersets) == 0:
        raise RuntimeError("No Markersets loaded")

    results = []
    for ms in markersets:
        found, missing = markersets[ms].test(prefix, items)
        if len(found) > 0:
            results.append((ms, len(found)))

    if len(results) == 0:
        return None
    return max(results, key=lambda v: v[1])[0]


def prefixes():
    """ returns the set() of all possible prefixes.  All markersets are tested """

    global markersets

    if len(markersets) == 0:
        load_all()

    res = set()
    for n in markersets:
        for prefix in markersets[n].prefixes():
            res.add(prefix)

    return res


def display_mode_all(mode, value=3):
    """ sets the display mode for all markers in the scene.  Sets the .displayMode attribute on all
    peelSquareLocators """

    for i in m.ls(type="peelSquareLocator"):
        parent = m.listRelatives(i, p=True)[0]
        if m.objExists(parent + '.displayMode'):
            m.setAttr(parent + '.displayMode', 3)


class Markerset(object):
    """ The base class for a markerset.
     A markerset contains:
       - a list of the marker names (without a prefix)
       - the lines that connect the markers (optional)
       - rigidbody definitions (optional)
     """

    def __init__(self):

        self.markerList = []
        self.lineList = []
        self.rigidbodies = []
        self.name = ""

    def __str__(self):
        v = (self.name, len(self.markerList), len(self.lineList), len(self.rigidbodies))
        return "Markerset: %s  Markers: %d Lines: %d  Rigidbodies: %d" % v

    def markers(self, prefix=None):
        """ subclass will return a list of all the markers in the markerset """
        if prefix is None:
            return self.markerList

        return [prefix + i for i in self.markerList]

    def lines(self):
        """ subclass will return a 2d list of line connections [ [ 'a', 'b', 'c'], ['b', 'd', 'e'] ] """
        return self.lineList

    def draw_lines(self, prefix, clear=False):

        """ draws the lines between the markers, if clear is set it will delete all lines for all markerset """

        if self.lineList is None or len(self.lineList) == 0:
            m.warning("No lines defined")
            return

        marker0 = prefix + self.lineList[0][0]
        if not m.objExists(marker0):
            m.warning("Could not find markers to draw lines: " + marker0)
            return

        top_node = m.listRelatives(marker0, p=True)[0]

        group = top_node + "|LINES"

        if clear:
            if m.objExists(group):
                m.delete(group)
            return

        if not m.objExists(group):
            group = m.group(em=True, name="LINES", parent=top_node)
            m.setAttr(group + ".template", 1)

        for grp in self.lineList:

            # check all markers in the group exist
            check = True
            for marker in grp:

                if not m.objExists(prefix + marker):
                    m.warning("Marker missing while drawing lines, skipping group.  " + prefix + marker)
                    check = False

            if not check:
                continue

            # create the line
            loc = m.createNode("PeelLine", p=group, name=grp[0] + "LineShape")
            for i, marker in enumerate(grp):
                m.connectAttr(prefix + marker + ".translate", loc + ".points[%d]" % i)

    def set_color(self, prefix, color):
        """ Changes the marker colors """
        for marker in self.markerList:
            find = m.ls(prefix + marker, type='transform')
            if len(find) == 0:
                print("Skipping color on: " + prefix + marker)
                continue

            for i in find:
                chld = m.listRelatives(i, s=True)
                if chld is not None and len(chld) > 0:
                    m.setAttr(chld[0] + ".overrideEnabled", 1)
                    m.setAttr(chld[0] + ".overrideColor", color)

    def set_display_mode(self, prefix, mode):

        """ sets the display mode for the markers in the set """

        for marker in self.markerList:
            if not m.objExists(prefix + marker): continue
            cld = m.listRelatives(prefix + marker, s=True)
            if len(cld) == 0: continue
            m.setAttr(cld[0] + ".displayMode", mode)

    def test(self, prefix, items=None):

        """ returns (found, missing) marker names for the given set/prefix """

        if self.markerList is None:
            return None

        # for each marker check that it exists in the scene
        missing = []
        found = []
        for marker in self.markerList:

            if items is None:
                check = m.objExists(prefix + marker)
            else:
                check = prefix + marker in items

            if check:
                found.append(prefix + marker)
            else:
                missing.append(prefix + marker)

        # return the number of missing markers
        return found, missing

    def prefixes(self):
        """ returns the possible prefixes for this markerset """

        pfx = set()
        for i in m.ls(type="peelSquareLocator"):
            pp = m.listRelatives(i, p=True)[0]
            for marker in self.markerList:
                if pp.endswith(marker):
                    pfx.add(pp[: -len(marker)])

        return list(pfx)

    def prefixed(self, prefix):
        ret = []
        for marker in self.markers():
            if m.objExists(prefix + marker):
                ret.append(prefix + marker)

        return ret

    def select(self, prefix):

        """ select the markers for the given prefix """

        m.select(cl=True)
        for marker in self.markerList:
            scene_marker = m.ls(prefix + marker, type='transform', l=True)
            if scene_marker is None or len(scene_marker) == 0:
                continue

            if len(scene_marker) > 0:
                m.warning("More than one marker named: " + marker + " while selecting")

            for i in scene_marker:
                m.select(scene_marker, add=True)

    def save(self, name, file_name):

        data = {'name': name,
                'markers': self.markerList,
                'lines': self.lineList,
                'rigidbodies': self.rigidbodies}

        data = json.dumps(data, indent=4)

        fp = open(file_name, 'w')
        if not fp:
            m.error("could not open file: " + str(file_name))
            return

        fp.write(data)
        fp.close()

    def load(self, file_name):

        fp = None
        try:
            fp = open(file_name, 'r')
        except Exception as e:
            m.warning(str(e))

        if not fp:
            m.warning("could not open file: " + str(file_name))
            return

        try:
            data = json.load(fp)
        except Exception as e:
            m.warning(file_name + " " + str(e))
            fp.close()
            return None

        self.markerList = data['markers'] if 'markers' in data else []
        self.lineList = data['lines'] if 'lines' in data else []
        self.rigidbodies = data['rigidbodies'] if 'rigidbodies' in data else []
        self.name = data['name']

        ret = data['name']
        fp.close()
        return ret


def from_selection():
    """ Create a new markerset from the selected markers in the scene """

    # new empty markerset
    ms = Markerset()

    # get selection and strip prefix
    sel = m.ls(sl=True, l=True)
    names = [i[i.rfind('|') + 1:] for i in m.ls(sl=True, l=True)]
    prefix = os.path.commonprefix(names)
    ms.markerList = [i[len(prefix):] for i in names]

    # get connected PeelLine nodes
    nodes = set()
    for node in sel:
        con = m.listConnections(node, s=False, d=True, p=True, type='PeelLine')
        if con is None: continue
        for c in con: nodes.add(c.split('.')[0])

    # save the lines
    ms.lineList = []

    for line in nodes:

        items = []
        for i in range(m.getAttr(line + '.points', size=True)):
            src = m.listConnections(line + ".points[%d]" % i, s=True, d=False, p=True)
            if src is None: continue
            src = src[0]
            src = src[: src.find('.')]
            if '|' in src: src = src[src.rfind('|') + 1:]

            if len(prefix) > 0:
                if not src.startswith(prefix):
                    m.warning("No prefix on: " + src[0])
                    continue
                items.append(src[len(prefix):])
            else:
                items.append(src)

        ms.lineList.append(items)

    # save the rigidbodies
    items = {}
    sel = m.ls(sl=True)
    for i in sel:
        con = m.listConnections(i + ".worldMatrix", d=True, s=False, type='rigidbodyNode')
        if con is not None:
            for c in con:
                if c not in items:
                    items[c] = set()
                items[c].add(str(i[len(prefix):]))

    for mlist in items.values():
        ms.rigidbodies.append(tuple(mlist))

    return ms


def clear_marker_lines():
    """ remove all marker lines in the scene (leaves the group) """

    delme = set()
    for i in m.ls(type="PeelLine"):
        delme.add(m.listRelatives(i, p=True)[0])

    m.delete(list(delme))


def set_display_mode(mode):
    """ sets the display mode for all markers """

    for marker in m.ls(type="peelSquareLocator"):
        m.setAttr(marker + ".displayMode", mode)
    return
