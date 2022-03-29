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
import math
import copy


class vec(object):
    """ A really simple vector object used to help calculate midpoints """

    def __init__(self, *arg):

        if len(arg) == 1 and isinstance(arg[0], list):
            self.data = arg[0]
        elif len(arg) == 1 and isinstance(arg[0], tuple):
            self.data = list(arg[0])
        else:
            self.data = list(arg)

    def __getitem__(self, i):
        return self.data[i]

    def __sub__(self, other):
        return vec(*[a - b for a, b in zip(self.data, other.data)])

    def __add__(self, other):
        return vec(*[a + b for a, b in zip(self.data, other.data)])

    def __mul__(self, other):
        if isinstance(other, int) or isinstance(other, float):
            return vec(*[a * other for a in self.data])
        else:
            return vec(*[a + b for a, b, in zip(self.data, other.data)])

    def __str__(self):
        return "vector " + str(self.data)

    def dist(self, other):
        dif = [a - b for a, b in zip(self.data, other.data)]
        return math.sqrt(sum([i * i for i in dif]))

    def rx(self, theta):
        y = self.data[1]
        z = self.data[2]

        self.data[1] = y * math.cos(theta) - z * math.sin(theta)
        self.data[2] = y * math.sin(theta) + z * math.cos(theta)

    def ry(self, theta):
        x = self.data[0]
        z = self.data[2]

        self.data[0] = x * math.cos(theta) + z * math.sin(theta)
        self.data[2] = -1 * x * math.sin(theta) + z * math.cos(theta)

    def rz(self, theta):
        x = self.data[0]
        y = self.data[1]

        self.data[0] = x * math.cos(theta) - y * math.sin(theta)
        self.data[1] = x * math.sin(theta) + y * math.cos(theta)

    def locator(self, name, parent=None):
        loc = m.spaceLocator(name=name)[0]
        if parent: loc = m.parent('|' + loc, parent)[0]
        m.setAttr(loc + '.t', *self.data)
        m.setAttr(loc + '.r', 0, 0, 0)
        return loc



class Vector(object):
    """ Vector math operations, can fetch from maya transforms (default is world space)"""
    def __init__(self, node=None, data=None, ws=True):
        self.node = node
        self.data = [0., 0., 0., 1.]

        if data is None:
            if node is not None and m.objExists(node):
                self.fetch(ws)
        else:
            self.data[0] = data[0]
            self.data[1] = data[1]
            self.data[2] = data[2]

    def fetch(self, ws=True):
        """ populate the values from scene, if ws is true uses the world space value
            using xform, otherwise gets the local translation using getAttr """

        if ws:
            x, y, z = m.xform(self.node, q=True, ws=True, t=True)
            self.data[0] = x
            self.data[1] = y
            self.data[2] = z
        else:
            self.data[0] = m.getAttr(self.node + ".tx")
            self.data[1] = m.getAttr(self.node + ".ty")
            self.data[2] = m.getAttr(self.node + ".tz")

        self.data[3] = 1.

    def apply(self, node=None, ws=True):

        if node is None:
            node = self.node

        if ws:
            m.xform(node, ws=True, t=self.data[0:3])
        else:
            m.setAttr(node + ".t", self.data[0:3])

    def __str__(self):
        return "vec: %f, %f, %f" % (self.data[0], self.data[1], self.data[2])

    def __setitem__(self, k, v):
        self.data[k] = v

    def __getitem__(self, index):
        return self.data[index]

    def dist(self, other):
        """ returns the euclidean distance between this and other """
        return sum([i*i for i in other - self])

    def __sub__(self, other):
        """ returns a new Vector with the subtraction """
        val = tuple( [ a-b for a,b in zip(self, other)])
        return Vector(data=val)

    def mag(self):
        """ returns the magnitude of this vector """
        return math.sqrt(sum([i*i for i in self.data[:3]]))

    def __radd__(self, value):
        """ += the x,y,z values """
        self.data[0] += value[0]
        self.data[1] += value[1]
        self.data[2] += value[2]

    def __add__(self, value):
        """ returns a new vector with x,y,z added """
        x = self.copy()
        x.__radd__(value)
        return x

    def __rdiv__(self, value):
        """ value can be int, flot, list, tuple or Vector. """
        if type(value) in [int, float]:
            self.data[0] /= value
            self.data[1] /= value
            self.data[2] /= value
        if type(value) in [list, tuple, Vector]:
            self.data[0] /= value[0]
            self.data[1] /= value[1]
            self.data[2] /= value[2]

    def __div__(self, value):
        x = self.copy()
        x.__rdiv__(value)
        return x

    def __iter__(self):
        return self.data.__iter__()

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return str(self.data)

    def copy(self):
        return Vector(node=self.node,
                      data=(self.data[0], self.data[1], self.data[2], self.data[3]))



class VectorList(list):

    def average(self):

        if len(self) == 0:
            return None

        out = Vector()
        for i in self:
            out += i

        return out / len(self)

def pos(node):
    return vec(*m.getAttr(node + ".t")[0])


def dist(nodea, nodeb):
    va = vec(m.xform(nodea, q=True, t=True, ws=True))
    vb = vec(m.xform(nodeb, q=True, t=True, ws=True))
    return va.dist(vb)


class rigidbody(object):

    def __init__(self, nodes):

        self.nodes = nodes
        self.pnts = [pos(i) for i in nodes]
        self.midpoint = vec(*[sum(i) / len(self.pnts) for i in zip(*self.pnts)])
        self.locals = [i - self.midpoint for i in self.pnts]

    def globals(self):

        return [i + self.midpoint for i in self.locals]

    def errors(self):

        A = self.pnts
        B = self.globals()

        return [A[i].dist(B[i]) for i in range(len(self.nodes))]

    def error(self):

        errorList = vec(self.errors())
        return math.sqrt(sum([i * i for i in errorList])) / 2

    def rotate(self, x, y, z):

        for p in self.locals:
            p.rx(x)
            p.ry(y)
            p.rz(z)

    def create(self, name, parent=None):

        mp = self.midpoint.locator(name, parent)
        for i in self.locals:
            i.locator('local', mp)
        return mp

    def copy(self, tx=None, ty=None, tz=None, rx=None, ry=None, rz=None):

        out = copy.deepcopy(self)

        for p in self.locals:
            if tx: p.data[0] += tx
            if ty: p.data[1] += ty
            if tz: p.data[2] += tz
            if rx: p.rx(rx)
            if ry: p.rx(ry)
            if rz: p.rz(rz)

        return out
