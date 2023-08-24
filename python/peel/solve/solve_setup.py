# Copyright (c) 2021 Alastair Macleod
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import maya.cmds as m
from maya import mel
import json
import math
from peel.solve import locator, rigidbody
import peel.solve.solve as ps
from peel.util import dag, matrix, joint, roots
import os.path
import subprocess
import tempfile

""" Collection of utilities for creating a solve setup"""


def four_points(joint, rb):

    """ Constrain a joint to a rigibody by using 4 markers """

    def name(node):
        if ':' in node: node = node.split(':')[-1]
        if '|' in node: node = node.split('|')[-1]
        return node

    rb_name = name(rb)
    east = m.spaceLocator(name=rb_name + "_east")[0]
    m.parent(east, joint)
    m.setAttr(east + ".tx", 0)
    m.setAttr(east + ".ty", 0)
    m.setAttr(east + ".tz", 20)

    west = m.spaceLocator(name=rb_name + "_west")[0]
    m.parent(west, joint)
    m.setAttr(west + ".tx", 0)
    m.setAttr(west + ".ty", 0)
    m.setAttr(west + ".tz", -20)

    north = m.spaceLocator(name=rb_name + "_north")[0]
    m.parent(north, joint)
    m.setAttr(north + ".tx", 20)
    m.setAttr(north + ".ty", 0)
    m.setAttr(north + ".tz", 0)

    south = m.spaceLocator(name=rb_name + "_south")[0]
    m.parent(south, joint)
    m.setAttr(south + ".tx", -20)
    m.setAttr(south + ".ty", 0)
    m.setAttr(south + ".tz", 0)

    for i in [north, south, east, west]:
        m.parent(i, rb)
        m.select([i, joint])
        mel.eval("peelSolve2TransformAttr(1);")


def midpoint(nodes, prefix=""):

    """ find the midpoint of a set of points """

    #res = [m_cmds.getAttr(prefix + i + ".t")[0] for i in nodes]
    res = [m.xform(prefix + i, q=True, ws=True, t=True) for i in nodes]
    res = [sum(i) for i in zip(*res)]
    return [i / len(nodes) for i in res]


def move_to_origin(prefix, hip_markers):
    """ move the performer to the origin, by moving the optical root"""
    # TODO: This doesn't work with scaled data
    oroot = roots.ls()
    m.setAttr(oroot + ".t", 0, 0, 0)
    n = midpoint(hip_markers, prefix)
    m.setAttr(oroot + ".t", -n[0], 0, -n[2])


def center_hips(root, markers):
    mp = midpoint(markers)
    ty = m.xform(root, q=True, ws=True, t=True)[1]
    m.xform(root, ws=True, t=(mp[0], ty, mp[2]))


def fit_legs(skel_prefix, marker):

    m.setAttr(skel_prefix + 'Hips.t', l=True)
    for i in ['Hips', 'RightLeg', 'RightFoot', 'LeftLeg', 'LeftFoot']:
        m.setAttr(skel_prefix + i + '.r', l=True)

    mkr = []

    ret = locator.connect(1, marker + "RTOE", skel_prefix + "RightFoot")
    m.setAttr(ret + '.t', 18, -7, 0)
    mkr.append(ret)

    ret = locator.connect(1, marker + "RHEL", skel_prefix + "RightFoot")
    m.setAttr(ret + '.t', -7, 3.5, 0)
    mkr.append(ret)

    ret = locator.connect(1, marker + "LTOE", skel_prefix + "LeftFoot")
    m.setAttr(ret + '.t', 18, -7, 0)
    mkr.append(ret)

    ret = locator.connect(1, marker + "LHEL", skel_prefix + "LeftFoot")
    m.setAttr(ret + '.t', -7, 3.5, 0)
    mkr.append(ret)

    ps.frame(root_nodes=[skel + 'Hips'])

    m.setAttr(skel + 'Hips.t', l=False)
    for i in ['Hips', 'RightLeg', 'RightFoot', 'LeftLeg', 'LeftFoot']:
        m.setAttr(skel + i + '.r', l=False)

    m.delete(mkr)


def strip_left(source, value):
    """ if source is prefixed with value, return value with that prefix removed, otherwise return value """
    if value is None or not source.startswith(value):
        return source
    return source[len(value):]


def save(file_path=None, strip_marker=None, strip_joint=None, rb=True, skel=True):

    """ Save the solve setup as a json file
    @param file_path: file to save the json data to, defaults to current scene path with .json extension
    @param strip_marker: prefix to remove from the marker names
    @param strip_joint: prefix to remove from the joint names
    @param rb: list of rigidbodies to solve, or True = All, False = None
    @param skel: list of skeleton roots to solve, or True = All, False = None
    """

    all_roots = roots.ls(extend=False)

    if not rb and not skel:
        raise RuntimeError("Nothing to export, rb or skel were not set")

    count = 0

    ret = {}
    if rb is True:
        ret['rigidbodies'] = rigidbody.serialize()
        print("Exported %d rigidbodies" % len(ret['rigidbodies']))
        count += len(ret['rigidbodies'])

    if isinstance(rb, list):
        ret['rigidbodies'] = rigidbody.serialize(sel=rb)
        count += len(ret['rigidbodies'])

    if skel and all_roots:
        solvers = {}
        for root in all_roots:
            if not m.objExists(root):
                print("Could not find root: " + str(root))
                continue
            print("Saving root: " + root)
            solvers[root] = serialize(root, strip_marker, strip_joint)
        ret['solvers'] = solvers
        count += len(solvers)

    if count == 0:
        raise RuntimeError('Nothing found to export')

    if file_path is not None:
        print("Saved to: " + file_path.replace('/', '\\'))
        with open(file_path, "w") as fp:
            json.dump(ret, fp, indent=4)
            return file_path
    else:
        fd, path = tempfile.mkstemp(prefix="peelsolve")
        with open(path, "w") as fp:
            json.dump(ret, fp, indent=4)
            return path


def scene_path(ext):
    sn = m.file(sn=True, q=True)
    return sn[:sn.rfind('.')] + "." + ext


def solve(file_path=None, rb=True, skel=True):
    """ Run the standalone solver for rigidbodies and skeletons (see save for rb and skel args) """
    solve_config = save(file_path=file_path, rb=rb, skel=skel)
    c3d = m.getAttr(roots.optical() + ".C3dFile")
    print("C3d: " + c3d)
    print("Config: " + solve_config)
    subprocess.call(["m:/bin/peelsolve.exe", c3d, solve_config, solve_config + ".out"])
    import_solved(solve_config + ".out")


def solve_rb():
    """ Solve selected rigidbodies """
    solve(rb=m.ls(sl=True), skel=False)


def serialize(root, strip_marker=None, strip_joint=None):
    """ serialize the solve settings for the given root node """

    active_list = []

    # Active Markers

    for activeMarker in m.peelSolve(s=root, la=True, ns=True):

        marker_name = activeMarker
        if '|' in marker_name: marker_name = marker_name.split('|')[-1]
        if ':' in marker_name: marker_name = marker_name.split(':')[-1]

        source = m.listConnections(activeMarker + ".peelTarget", s=True, d=False)
        if source is None or len(source) == 0:
            # marker is not connected - this may because we are parsing a template file
            m.warning("unconnected marker: " + str(activeMarker))
            source = marker_name
            if source.endswith('_Marker'):
                source = source[:-7]
        else:
            source = source[0]

        parent = m.listRelatives(activeMarker, p=True)[0]

        data = {'name':        strip_left(marker_name, strip_marker),
                'name_raw':    marker_name,
                'source':      strip_left(source, strip_marker),
                'source_raw':  source,
                'parent':      strip_left(parent, strip_joint),
                'parent_raw':  parent,
                'peelType':    m.getAttr(activeMarker + ".peelType"),
                'tWeight':     m.getAttr(activeMarker + ".translationWeight"),
                'translation': m.getAttr(activeMarker + ".t")[0],
                'rotation':    [math.radians(i) for i in m.getAttr(activeMarker + ".r")[0]]}

        if m.objExists(activeMarker + ".rotationWeight"):
            data['rWeight'] = m.getAttr(activeMarker + ".rotationWeight")

        if m.objExists(activeMarker + ".peelTarget"):
            data['target'] = m.getAttr(activeMarker + ".peelTarget")

        if m.objExists(source):
            rigidbody_node = rigidbody.from_active(source)

            if rigidbody_node:
                # the marker is connect to a rigidbody - get the details for that

                rbdata = []
                for index in m.getAttr(rigidbody_node + ".input", mi=True):

                    # for each marker in the rigidbody_node
                    ch = "[%d]" % index
                    rb_source = m.listConnections(rigidbody_node + ".input" + ch, s=True, d=False)
                    if rb_source is None or len(rb_source) == 0:
                        rb_local = m.listConnections(rigidbody_node + ".local" + ch, s=True, d=False)
                        if rb_local is None or len(rb_local) == 0:
                            raise RuntimeError("Disconnected local rigidbody: " + str(rigidbody_node))
                        rb_source = rb_local[0]
                        if rb_source.endswith('_Marker'):
                            rb_source = rb_source[:-7]
                        m.warning("Disconnected rigidbody: " + str(rigidbody_node))

                    rb_weight = m.getAttr(rigidbody_node + ".weight" + ch)
                    rb_source_stripped = strip_left(rb_source[0], strip_marker)
                    rbdata.append((rb_source_stripped, rb_weight))
                data['rigidbody'] = rbdata

        active_list.append(data)

    # Passive Joints

    passive_list  = []
    for passiveTransform in m.peelSolve(s=root, lp=True, ns=True):

        joint_obj = joint.PeelJoint(passiveTransform)

        data = {
            'longName': passiveTransform,
            'name': passiveTransform.split('|')[-1],
            'translation': m.getAttr(passiveTransform + ".t")[0],
            'rotation': [math.radians(i) for i in m.getAttr(passiveTransform + ".r")[0]],
            'preMatrix': matrix.asArray(joint_obj.pre),
            'postMatrix': matrix.asArray(joint_obj.post),
            'dofx': not m.getAttr(passiveTransform + ".rx", l=True),
            'dofy': not m.getAttr(passiveTransform + ".ry", l=True),
            'dofz': not m.getAttr(passiveTransform + ".rz", l=True)
        }

        if passiveTransform == root:
            data['parent'] = None
        else:
            data['parent'] = m.listRelatives(passiveTransform, p=True)[0]

        if m.objExists(passiveTransform + ".lendof"):
            data["lendof"] = m.getAttr(passiveTransform + ".lendof")

        if m.objExists(passiveTransform + ".lengthStiff"):
            data["lengthStiff"] = m.getAttr(passiveTransform + ".lendof")

        if m.objExists(passiveTransform + ".rotStiff"):
            data['rotStiff'] = m.getAttr(passiveTransform + ".rotStiff")

        if m.objExists(passiveTransform + '.preferredAngleX'):
            px = m.getAttr(passiveTransform + '.preferredAngleX')
            py = m.getAttr(passiveTransform + '.preferredAngleY')
            pz = m.getAttr(passiveTransform + '.preferredAngleZ')
            data['preferredAngle'] = (px, py, pz)

        joint_name = passiveTransform
        if '|' in joint_name: joint_name = joint_name.split('|')[-1]
        if ':' in joint_name: joint_name = joint_name.split(':')[-1]

        passive_list.append(data)

    return {'active': active_list, 'passive': passive_list }


def findTransform( name ):

    """ returns the node skipping, hik joints """

    ret = []
    for node in m.ls(name):
        if m.nodeType(node) == 'hikFKJoint':
            continue
        ret.append(node)
    return ret


def connect(src, dst, peel_type, t_weight, r_weight):
    """ connect a marker to a target """

    lineLoc = mel.eval('peelSolve2CreateLineLocator("%s", "%s")' % (src, dst))
    mel.eval('peelSolve2CreateTransform({"%s"}, %d)' % (lineLoc[0], peel_type))

    m.connectAttr(src + ".worldMatrix[0]", lineLoc[0] + ".peelTarget")

    if m.objExists(lineLoc[0] + ".translationWeight"):
        m.connectAttr(lineLoc[0] + ".translationWeight", lineLoc[1] + ".tWeight")
        m.setAttr(lineLoc[0] + ".translationWeight", t_weight)

    if m.objExists(lineLoc[0] + ".rotationWeight"):
        m.connectAttr(lineLoc[0] + ".rotationWeight", lineLoc[1] + ".rWeight")
        m.setAttr(lineLoc[0] + ".rotationWeight", r_weight)

    print("Connected: %s to %s  type: %d  tw: %f  rw: %f" % (src, dst, peel_type, t_weight, r_weight))

    return lineLoc


def connect_data(data, prefix='', namespace=''):
    """ Reconnect the serialized data - see data() """

    if len(namespace) > 0 and namespace[-1] != ':':
        namespace += ":"

    for active in data['active']:
        if 'rigidbody' in active:
            m.select([prefix + i[0] for i in active['rigidbody']])
            rbn = mel.eval("peelSolve2RigidBody();")
            rbt = m.listConnections(rbn + ".OutputTranslation", s=False, d=True)[0]
            src = rbt
        else:

            src = findTransform(prefix + active['source'])
            if not src:
                print("Could not find source for : " + prefix + active['source'])
                continue
            src = src[0]
        dst = findTransform(namespace + active['parent'])
        if not dst:
            raise RuntimeError("Cannot find: " + namespace + active['parent'])
        line_loc, _ = connect(src, dst[0], active['peelType'], active['tWeight'], active['rWeight'])
        m.setAttr(line_loc + ".t", *active['translation'][0])
        m.setAttr(line_loc + ".r", *active['rotation'][0])


def create_setup(marker_prefix, skeleton_prefix):
    """ 
    :param marker_prefix: The prefix to the markers
    :param skeleton_prefix: The prefix to the joints
    Connect the markers to the joints using the global CONNECTIONS relationships
    TODO: use a json file instead
    """
    import maya.mel as mel

    for k, v in CONNECTIONS.iteritems():
        markers = [marker_prefix + i for i in v if m.objExists(marker_prefix + i)]
        m.select(*(markers + [skeleton_prefix + k]))
        mel.eval('peelSolve2TransformAttr(1);')

    roots.set_roots([skeleton_prefix + "Hips"])


def import_solved(in_path):

    """ Applies data that has been created by the standalone solver """

    if not os.path.isfile(in_path):
        raise RuntimeError("Could not find file: " + str(in_path))

    print("Loading: " + str(in_path))
    fp = open(in_path, 'r')

    header = fp.readline().strip().split()[1:]
    
    print("Channels: " + str(len(header)))
        
    frame_data = []
    
    print("Clearing animation/channels")

    for nattr in header:
        frame_data.append({})
        if m.listConnections(nattr):
            m.delete(m.listConnections(nattr))            
            
    print("Loading data")

    while fp:
        line = fp.readline().strip().split()
        if len(line) != len(header) + 1:
            break

        values = [ float(i) for i in line ]
        frame = values[0]
        for channel in range(len(header)):
            frame_data[channel][frame] = values[channel+1]
            
    fp.close()
    
    print("Applying curves")
    
    for i in range(len(header)):
        node, addr = header[i].split(".")
        try:
            dag.apply_curve(node, addr, frame_data[i])
        except RuntimeError as e:
            print(str(e))
        
    print("Import complete")

    return header


def test(root):
    nodes = {}

    for i in m.peelSolve(s=root, ns=True, lp=True):
        name = i
        if '|' in i:
            name = i.split('|')[-1]
        parent = None
        if not i.endswith(root):
            parent = m.listRelatives(i, p=True)[0]
        print(name, parent)

        jj = joint.PeelJoint(i)
        matrix.createLocator("x_" + name, jj.asMatrix())
        for ch in ["tx", "ty", "tz", "rx", "ry", "rz"]:
            m.setAttr("x_" + name + "." + ch, l=True)

        nodes[name] = parent

    for i, parent in nodes:
        print(i, parent)
        if parent:
            m.parent("x_" + i, "x_" + parent)


def motive_setup(prefix):

    d = { 'WaistRFront': (-12.2, 1.5, 12.5),
          'WaistLFront':  (12.2, 1.5, 12.5),
          'WaistLBack':  (-12.2, 1.5, -12.5),
          'WaistRBack': (12.2, 1.5, -12.5) }

    for node, tform in d.items():
        marker, shape = locator.line(prefix + node, "Hips")
        m.setAttr(marker + ".t", *tform)