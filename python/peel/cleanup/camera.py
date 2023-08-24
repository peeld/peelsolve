import maya.cmds as m
import maya.mel as mel
import math

rigidbody = None
camera = None
lastCam = None
currentPanel = None
selection = None


def clear():
    global rigidbody
    global camera
    global lastCam
    global currentPanel
    global selection

    if camera and lastCam and currentPanel:
        pos = m.xform(camera, q=True, t=True, ws=True)
        ori = m.xform(camera, q=True, ro=True, ws=True)
        m.xform(lastCam, t=pos, ws=True)
        m.xform(lastCam, ro=ori, ws=True)
        m.setAttr(lastCam + ".rz", 0)

        m.modelPanel(currentPanel, cam=lastCam, e=True)
        m.select(selection)
        m.viewFit()

    for i in [rigidbody, camera]:
        if i and m.objExists(i): m.delete(i)


def rigidbody_cam():
    global rigidbody
    global camera
    global lastCam
    global currentPanel
    global selection

    selection = m.ls(sl=True)
    if len(selection) < 2:
        m.error("Please select 2 or more items")
        return

    currentPanel = m.getPanel(wf=True)

    # get the current camera 
    try:
        lastCam = m.modelPanel(currentPanel, cam=True, q=True)
        pos = m.xform(lastCam, q=True, t=True, ws=True)
        ori = m.xform(lastCam, q=True, ro=True, ws=True)
    except RuntimeError as e:
        print(str(e))
        m.error("Do you have a viewport selected?")
        return

    # create a  camera
    camera = m.camera()[0]
    m.setAttr(camera + ".t", *pos)
    m.setAttr(camera + ".r", *ori)

    m.modelPanel(currentPanel, cam=camera, e=True)

    m.select(selection)
    rb = mel.eval("peelSolve2RigidBody();")
    rigidbody = m.listConnections(rb + ".OutputTranslation")[0]
    m.setAttr(rigidbody + ".v", 0)
    m.parent(camera, rigidbody)

    p1 = m.xform(rigidbody, q=True, ws=True, t=True)
    p2 = m.xform(camera, q=True, ws=True, t=True)
    vec = [a - b for a, b in zip(p1, p2)]
    d = math.sqrt(sum([a * a for a in vec]))
    m.setAttr(camera + ".centerOfInterest", d)
