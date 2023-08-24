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

import maya.OpenMayaAnim as oma
import maya.OpenMaya as om
import maya.cmds as m

"""
Python wrappers for useful maya api functions
"""


def anim_curve(node, attr, create=False):
    """ returns a MFnAnimCurve object for the node.attr.
        If create is True the curve will be created, removing any existing curve """

    depFn = fn(node)
    if depFn is None: return

    try:
        plug = depFn.findPlug(attr)
    except:
        m.warning("Could not find attribute: " + attr + " for node: " + node)
        return None

    if create:

        # delete incoming connections and create a new node

        # print node + "." + attr
        conn = m.listConnections(node + '.' + attr, s=True, d=False)
        if conn is not None:
            for i in set(conn):
                if m.nodeType(i).startswith('animCurve'):
                    # print "Delete: " + str(i) + "   " + m_cmds.nodeType(i)
                    m.delete(i)

        dgmod = om.MDGModifier()
        fnCurve = oma.MFnAnimCurve()
        try:
            fnCurve.create(plug, dgmod)
        except RuntimeError as e:
            print("Error creating anim curve for " + node + " " + attr)
            raise e

        return (fnCurve, dgmod)

    else:

        return oma.MFnAnimCurve(plug)


def apply_curve(node, attr, data, stepped=False):
    """ creates an anim curve for the data (dict) """

    k = list(data.keys())
    v = data.values()

    tt = oma.MFnAnimCurve.kTangentStep if stepped else oma.MFnAnimCurve.kTangentGlobal

    times = om.MTimeArray()
    times.setLength(len(k))

    for i in range(len(k)):
        tv = om.MTime(k[i], om.MTime.uiUnit())
        times.set(tv, i)

    su = om.MScriptUtil()
    su.createFromList(v, len(v))
    x = anim_curve(node, attr, create=True)
    if x is None: return
    fn, dgmod = x
    fn.addKeys(times, om.MDoubleArray(su.asDoublePtr(), len(v)), oma.MFnAnimCurve.kTangentGlobal, tt)
    dgmod.doIt()


def fn(node):
    """ returns an MFnDependencyNode for the given node (string), or None """

    sel = om.MSelectionList()
    try:
        sel.add(node)
    except:
        m.warning("Could not find node: " + str(node))
        return None

    obj = om.MObject()
    sel.getDependNode(0, obj)
    return om.MFnDependencyNode(obj)


def get_mdagpath(item):
    """ Returns a MDagPath object for the item (by name) """
    sel = om.MSelectionList()
    sel.add(item)
    if sel.length() == 0: return None
    dp = om.MDagPath()
    sel.getDagPath(0, dp)
    return dp


def get_mdep(item):
    """ Returns an MObject for the item (by name)"""
    sel = om.MSelectionList()
    sel.add(item)
    if sel.length() == 0: return None
    obj = om.MObject()
    sel.getDependNode(0, obj)
    return obj


def dep_fn(node):
    """ returns an MFnDependencyNode for the given node (string), or None """

    obj = get_mdep(node)
    if obj is None:
        return None

    sel = om.MSelectionList()
    sel.add(node)
    if sel.length() == 0:
        raise RuntimeError("Could not find: " + node)
    sel.getDependNode(0, obj)
    return om.MFnDependencyNode(obj)


def get_joint(name):
    dp = get_mdagpath(name)
    if dp is None:
        return None
    if not dp.hasFn(om.MFn.kJoint):
        return None
    return oma.MFnIkJoint(dp)


def get_plug(item):
    """ returns an MPlug for the given item (by name)"""
    sel = om.MSelectionList()
    sel.add(item)
    if sel.length() == 0:
        return None
    plug = om.MPlug()
    sel.getPlug(0, plug)
    return plug


def plug_info(plug):
    """ prints information about a MPlug to the console """

    if isinstance(plug, basestring):
        plug = get_plug(plug)

    print("name:   " + plug.name())
    print("array:  " + str(plug.isArray()))
    if plug.isArray():
        print("ele:    " + str(plug.numElements()))
    print("net:    " + str(plug.isNetworked()))
    print("null:   " + str(plug.isNull()))
    print("childs: " + str(plug.numChildren()))


def attr_name(attr_obj):
    """ gets the name of the attribute from the provided MObject """
    attr_fn = om.MFnAttribute(attr_obj)
    name = attr_fn.name()
    if attr_fn.isArray():
        name = name + "[]"
    try:
        parent_obj = attr_fn.parent()
        parent_name = attr_name(parent_obj)
        return parent_name + "." + name
    except RuntimeError:
        return name


def list_attr(item):
    """ list the attributes on an item (by name)"""
    o = get_mdep(item)
    dep = om.MFnDependencyNode(o)
    attrs = dep.attributeCount()
    for i in range(0, attrs):
        at = dep.attribute(i)
        print(attr_name(at))


def show(x):
    rtd = 57.2957795
    t = type(x)

    if t is om.MTransformationMatrix:
        x = x.asMatrix()
        t = type(x)
        print(str(t))

    if t is om.MMatrix:
        ret = ""
        for u in range(0, 4):
            for v in range(0, 4):
                ret += "%06.4f   " % om.MScriptUtil.getDoubleArrayItem(x[u], v)
            ret += "\n"
        return ret

    if t is om.MVector:
        return "%f %f %f" % (x.x, x.y, x.z)
    if t is om.MEulerRotation:
        return "%f %f %f" % ((x.x * rtd), (x.y * rtd), (x.z * rtd))
    if t is om.MQuaternion:
        return show(x.asEulerRotation())
    if x is None:
        return "None"
    return "Unknown type: " + str(t)
