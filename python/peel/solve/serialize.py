from __future__ import print_function
from peel.cleanup import markerset, joints
import maya.cmds as m
from maya import mel
import json

""" functions for managing the solve process, including serializing a solve template """


def namespaces(joint_map):
    """ get the scene namespaces for the given jointMap list """

    ns = set()

    for jointId in joint_map:
        for found in m.ls('*:' + joints.fbx[jointId]):
            ns.add(found.split(':')[0])

    return list(ns)


def connect_mapped(prefix, namespace, mapping):
    """ connect the marker prefix to the joint name space using the provided jointMap (mapping) """

    for jointId in mapping:
        for mkr, weight in mapping[jointId]:
            src = prefix + mkr
            dst = namespace + ':' + joints.fbx[jointId]

            for jid, altid in [(joints.ARMROLLR, joints.SHOULDERR),
                               (joints.ARMROLLL, joints.SHOULDERL),
                               (joints.FOREROLLL, joints.ELBOWL),
                               (joints.FOREROLLR, joints.ELBOWR)]:

                if jointId == jid and not m.objExists(dst):
                    dst = namespace + ':' + joints.fbx[altid]

            if m.objExists(src) and m.objExists(dst):
                mel.eval('peelSolve2Connect( 1 , { "%s", "%s" } )' % (src, dst))


def get_rigidbody(activeNode):
    """ return the rigidbody node associated with the rigidbody active node """

    drivenBy = m.listConnections(activeNode + ".t", s=True, d=False)
    if drivenBy is None or len(drivenBy) == 0:
        return None

    if m.nodeType(drivenBy[0]) == 'rigidbodyNode':
        return drivenBy[0]

    return None


def strip_left(source, value):
    if value is None:
        return source
    if not source.startswith(value):
        return value
    return source[len(value):]


def data(root, strip_marker=None, strip_joint=None):
    """ serialize the solve settings for the given root node """

    allData = {}

    activeList = []
    allData['active'] = activeList

    # Active Markers

    for activeMarker in m.peelSolve(s=root, la=True, ns=True):

        markerName = activeMarker
        if '|' in markerName: markerName = markerName.split('|')[-1]
        if ':' in markerName: markerName = markerName.split(':')[-1]

        source = m.listConnections(activeMarker + ".peelTarget", s=True, d=False)
        if source is None or len(source) == 0:
            # marker is not connected - this may because we are parsing a template file
            m.warning("unconnected marker: " + str(activeMarker))
            source = markerName
            if source.endswith('_Marker'):
                source = source[:-7]
        else:
            source = source[0]

        parent = m.listRelatives(activeMarker, p=True)[0]

        data = {}

        data['marker'] = strip_left(markerName, strip_marker)
        data['marker_raw'] = markerName
        data['source'] = strip_left(source, strip_marker)
        data['source_raw'] = source
        data['parent'] = strip_left(parent, strip_joint)
        data['parent_raw'] = parent
        data['peelType'] = m.getAttr(activeMarker + ".peelType")
        data['tWeight'] = m.getAttr(activeMarker + ".translationWeight")
        data['rWeight'] = m.getAttr(activeMarker + ".rotationWeight")

        if m.objExists(source):
            rigidbody = get_rigidbody(source)

            if rigidbody:
                # the marker is connect to a rigidbody - get the details for that

                rbdata = []
                for index in m.getAttr(rigidbody + ".input", mi=True):

                    # for each marker in the rigidbody                    
                    ch = "[%d]" % index
                    rb_source = m.listConnections(rigidbody + ".input" + ch, s=True, d=False)
                    if rb_source is None or len(rb_source) == 0:
                        rb_local = m.listConnections(rigidbody + ".local" + ch, s=True, d=False)
                        if rb_local is None or len(rb_local) == 0:
                            raise RuntimeError("Disconnected local rigidbody: " + str(rigidbody))
                        rb_source = rb_local[0]
                        if rb_source.endswith('_Marker'):
                            rb_source = rb_source[:-7]
                        m.warning("Disconnected rigidbody: " + str(rigidbody))

                    rb_weight = m.getAttr(rigidbody + ".weight" + ch)
                    rb_source_stripped = strip_left(rb_source[0], strip_marker)
                    rbdata.append((rb_source_stripped, rb_weight))
                data['rigidbody'] = rbdata

        activeList.append(data)

    # Rotation stiffness (passive markers)

    rotstiff = {}
    for passiveTransform in m.peelSolve(s=root, lp=True, ns=True):
        if m.objExists(passiveTransform + ".rotStiff"):
            markerName = passiveTransform
            if '|' in markerName: markerName = markerName.split('|')[-1]
            if ':' in markerName: markerName = markerName.split(':')[-1]
            stiff = m.getAttr(passiveTransform + ".rotStiff")
            px = m.getAttr(passiveTransform + '.preferredAngleX')
            py = m.getAttr(passiveTransform + '.preferredAngleY')
            pz = m.getAttr(passiveTransform + '.preferredAngleZ')
            rotstiff[markerName] = (stiff, px, py, pz)

    allData['rotstiff'] = rotstiff

    return allData


def find_transform(name):
    """ returns the node skipping, hik joints """

    ret = []
    for node in m.ls(name):
        if m.nodeType(node) == 'hikFKJoint': continue
        ret.append(node)
    return ret


def connect(src, dst, peelType, tWeight, rWeight):
    """ connect a marker to a target """

    lineLoc = mel.eval('peelSolve2CreateLineLocator("%s", "%s")' % (src, dst))
    mel.eval('peelSolve2CreateTransform({"%s"}, %d)' % (lineLoc[0], peelType))

    m.connectAttr(src + ".worldMatrix[0]", lineLoc[0] + ".peelTarget")

    if m.objExists(lineLoc[0] + ".translationWeight"):
        m.connectAttr(lineLoc[0] + ".translationWeight", lineLoc[1] + ".tWeight")
        m.setAttr(lineLoc[0] + ".translationWeight", tWeight)

    if m.objExists(lineLoc[0] + ".rotationWeight"):
        m.connectAttr(lineLoc[0] + ".rotationWeight", lineLoc[1] + ".rWeight")
        m.setAttr(lineLoc[0] + ".rotationWeight", rWeight)

    print("Connected: %s to %s  type: %d  tw: %f  rw: %f" % (src, dst, peelType, tWeight, rWeight))

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

            src = find_transform(prefix + active['source'])
            if not src:
                print("Could not find source for : " + prefix + active['source'])
                continue
            src = src[0]
        dst = find_transform(namespace + active['parent'])
        if not dst:
            raise RuntimeError("Cannot find: " + namespace + active['parent'])
        connect(src, dst[0], active['peelType'], active['tWeight'], active['rWeight'])


def save(root=None, template_data=None, out_path=None):
    """ Prompt the user for a file path, and serialize the data for the root to that file """

    if out_path is None:
        out_path = m.fileDialog2(fm=0, cap="Save solve template", ff="*.template")
        if not out_path or len(out_path) == 0: return
        out_path = out_path[0]

    if root is not None:
        template_data = data(root)

    if template_data is None:
        raise ValueError("No root or template data")

    fp = open(out_path, 'w')
    if not fp:
        m.error("Could not write to file: " + str(out_path))
        return

    json.dump(template_data, fp, indent=4)
    print("Template saved.  (%d bytes)" % fp.tell())
    fp.close()


def load():
    """ Load a solve template from a file and reconnect it """

    in_path = m.fileDialog2(fm=1, cap="Load solve template", ff="*.template")
    if not in_path or len(in_path) == 0: return

    fp = open(in_path[0], 'r')
    if not fp:
        m.error("Could not read file: " + str(in_path))
        return

    template_data = json.load(fp)
    fp.close()

    return template_data

    # print "Connecting template"
    # connect_data(template_data)
