# Mocap Cleanup - Alastair Macleod 2016
# GPL License = http://www.gnu.org/licenses/gpl.txt 

from peel.cleanup import markerset as ms
import maya.cmds as m
from peel.util import roots


def selectSourceMarkers():
    m.select(cl=True)
    for rn in rootNodes():
        for active in m.peelSolve(s=rn, la=True, nosolve=True):
            if not m.objExists(active + ".peelTarget"):
                print("No target for: ", active)
                continue

            m.select(m.listConnections(active + ".peelTarget", s=True, d=False), add=True)


def setSquare():
    for shape, transform in getLocators(type='peelSquareLocator'):
        m.setAttr(shape + ".displayMode", 1)


def rootNodes():
    ret = []
    for i in m.ls(type='peelSolveOptions'):
        for rn in m.getAttr(i + ".rootNodes"):
            if m.objExists(rn):
                ret.append(rn)
    return ret


def runSolve(start=None, end=None):
    if start is None: start = m.playbackOptions(q=True, min=True)
    if end is None: end = m.playbackOptions(q=True, max=True)

    for rn in rootNodes():
        print("Solving: " + rn)
        apply_scale(root=rn)
        m.peelSolve(s=rn, start=start, end=end, inc=1)


def getLocators(type="peelLocator"):
    loc = m.ls(type=type, l=True)
    ret = []
    for i in loc:
        ret.append((i, m.listRelatives(i, p=True, f=True)[0]))

    return ret


def isRigidbody(transform):
    con = m.listConnections(transform + '.translate', p=True, s=False, type="rigidbodyNode")
    if con is None: return None
    if not '.local[' in con[0]: return None
    return con[0].replace('.local[', '.input[')


def isValid(transform):
    return m.objExists(transform + ".peelTarget")


def isConnected(nattr):
    # regular marker
    con = m.listConnections(nattr, s=True, d=False, p=True)
    # if con is not None :
    #    for i in con : print "  CONNECTED -> " + str(con)
    return con is not None


def find_pairing(transform):
    if not transform.endswith("_Marker"): return False
    if transform.startswith('RB_'): transform = transform[3:]
    src = m.ls(transform[:-7])
    if len(src) > 1: raise RuntimeError("Duplicate Markers in the scene")
    if len(src) == 1: return src[0]
    return None


def connect():
    """ connect peelTargets to their sources """

    print("Connecting peelTargets")

    for shape, transform in getLocators("peelLocator"):

        pos = transform.rfind('|')
        name = transform if pos is None else transform[pos + 1:]

        rigid_body_chan = isRigidbody(transform)
        if rigid_body_chan is not None:

            # check to see if the marker is already connected to something, 
            # e.g. a rigidbody
            if isConnected(rigid_body_chan):
                print("Already connected: " + transform + " (can be ignored for rigidbodies)")
                continue

            src = find_pairing(name)
            if src is None:
                print("Could not find pairing for rigidbody marker: ", name)
                continue

            print(str(src) + "  --- rigidbody ---> " + rigid_body_chan)
            m.connectAttr(str(src) + ".worldMatrix", rigid_body_chan)
            continue

        if not isValid(transform):
            print(">>> Skipping Invalid: ", name)
            continue

        if isConnected(transform + ".peelTarget"):
            print(">>> Already connected: ", name)
            continue

        src = find_pairing(name)
        if src is None:
            print("No match found for: ", name)
            continue
        if src is False:
            print("Could not determine match for: ", name)
            continue

        print(src + "  ---> " + name)
        m.connectAttr(src + ".worldMatrix", transform + ".peelTarget")


def apply_scale(prefix=None, root=None):

    """ look for the mocapScale attribute on the template and apply it to the optical root """

    optical_root = roots.optical()

    if optical_root is None:
        return ["Could not find optical root for: " + str(prefix)]

    err = []

    skel_roots = [root] if root is not None else roots.ls()

    for skel_root in skel_roots:
        if not m.objExists(skel_root + ".mocapScale"):
            err.append("%s.mocapScale not set in the template!" % skel_root)
            continue

        value = m.getAttr(skel_root + ".mocapScale")

        print("Setting optical root " + optical_root + " scale to " + str(value))
        m.setAttr(optical_root + ".sx", value)
        m.setAttr(optical_root + ".sy", value)
        m.setAttr(optical_root + ".sz", value)

    return err


def set_template_scale():

    """ prompt the user for the scale and set it as the mocapScale attribute """

    ret = m.promptDialog(m="Scale", text="1.0")
    if ret != 'Confirm':
        return

    value = float(m.promptDialog(q=True, text=True))

    if value == 0.0:
        m.error("Invalid scale")
        return

    for i in m.getAttr("peelSolveOptions.rootNodes"):
        if not m.objExists(i):
            m.warning(i + " does not exist")
            continue

        print("Setting scale attribute on: ", i)
        m.addAttr(i, sn='ms', ln='mocapScale', at='float')
        m.setAttr(i + ".mocapScale", keyable=True)
        m.setAttr(i + ".mocapScale", value)
