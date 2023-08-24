# Mocap Cleanup - Alastair Macleod 2016
# GPL License = http://www.gnu.org/licenses/gpl.txt


import maya.cmds as m
import maya.mel as mel
import os.path
import os
import markerset

''' Legacy code '''


def loadc3d():
    basicFilter = "*.c3d"
    c3dFiles = m.fileDialog2(fileFilter=basicFilter, dialogStyle=2, fm=1)
    if c3dFiles is None or len(c3dFiles) == 0: return
    c3dOps = ";scale=1;debug=0;stdloc=0;flopx=0;flopy=0;flopz=0;merge=0;prefix=;timecode=0;nodrop=0;zero=0;renameroot=0;convert=1"
    m.file(c3dFiles[0], i=True, type="peelC3D", ra=True, options=c3dOps, pr=True)


def cleanScene():
    for i in m.ls(type="peelSquareLocator", l=True):
        p = m.listRelatives(i, f=True, p=True)
        m.delete(p)

    for i in m.ls(type="peelLocator", l=True):
        p = m.listRelatives(i, f=True, p=True)
        m.delete(p)

    if m.objExists("peelSolveOptions"): m.delete("peelSolveOptions")


def dude():
    for i in [
        ["RB_Chest", "LowPolyMan_Torso"],
        ["RB_Hips", "LowPolyMan_Pelvis"],
        ["RB_LThigh", "LowPolyMan_Lowerleg_L"],
        ["RB_RThigh", "LowPolyMan_Lowerleg_R"],
        ["RB_LFoot", "LowPolyMan_Foot_L"],
        ["RB_RFoot", "LowPolyMan_Foot_R"]]:
        print(i)


def rb():
    marker_prefix = "Jervin_15_March_2013_"

    for i in [["RB_RFoot", ["RShin2", "RFoot2", "RFoot1", "RFoot3", "RToes1"]],
              ["RB_LFoot", ["LShin2", "LFoot2", "LFoot1", "LFoot3", "LToes1"]],
              ["RB_RThigh", ["RThigh2", "RThigh1", "RShin1"]],
              ["RB_LThigh", ["LThigh2", "LThigh1", "LShin1"]],
              ["RB_Hips", ["Hip1", "Hip2", "Hip3", "Hip4"]],
              ["RB_Chest", ["Chest1", "Chest2", "Chest3"]],
              ["RB_Head", ["Head1", "Head2", "Head3"]],
              ["RB_RHand", ["RHand1", "RHand2", "RHand3"]],
              ["RB_LHand", ["LHand1", "LHand2", "LHand3"]],
              ["RB_RUArm", ["RUArm1", "RUArm2", "RUArm3"]],
              ["RB_LUArm", ["LUArm1", "LUArm2", "LUArm3"]]]:
        m.select(cl=True)
        for j in i[1]:
            m.select(marker_prefix + j, add=True)
            rb = mel.eval("peelSolve2RigidBody()")
            print(rb)
            m.rename(rb, i[0])


# boneset can be "mcs" or "fbx"
# markerset can be "motive",  "mocapclub" or "arena"

class Rig:

    def __init__(self, boneset=None, markerset=None, marker_prefix="", skel_prefix=""):
        self.boneset = boneset
        self.markerset = markerset
        self.marker_prefix = marker_prefix
        self.skel_prefix = skel_prefix

    def testBoneset(self):
        boneSet = self.getBoneset(self.boneset)
        c = 0
        boneList = []
        for i in boneSet['connections']:
            boneList.append("%s%s" % (self.skel_prefix, i[0]))

        for i in boneSet['dof0']:
            boneList.append("%s%s" % (self.skel_prefix, i))

        for i in boneSet['dof1']:
            boneList.append("%s%s" % (self.skel_prefix, i))

        for i in boneSet['stiff']:
            boneList.append("%s%s" % (self.skel_prefix, i[0]))

        boneList.append("%s%s" % (self.skel_prefix, boneSet['root']))

        for bone in set(boneList):

            if not m.objExists(bone):
                print(bone)
                c = c + 1
        return c

    def getBoneset(self, setName, markers=None):

        if markers is None: markers = self.getMarkerset("blank")
        if setName == "mcs":
            ret = {}

            ret['dof0'] = ["bicep_roll_right", "bicep_roll_left",
                           "forearm_roll_right", "forearm_roll_left",
                           "clavicle_right", "clavicle_left",
                           "neck", "spine2", "spine1"]

            ret['dof1'] = ["elbow_right", "elbow_left", "knee_right", "knee_left"]

            ret['stiff'] = [["Spine1", 3], ["Spine2", 3], ["Spine3", 3], ["Neck", 3]]

            ret['root'] = "pelvis"

            ret['connections'] = [
                ["pelvis", markers['hips']],
                ["spine3", markers['chest']],
                ["head", markers['head']],
                ["shoulder_right", markers['shoulder_r']],
                ["shoulder_left", markers['shoulder_l']],
                ["elbow_right", markers['elbow_r']],
                ["elbow_left", markers['elbow_l']],
                ["wrist_right", markers['hand_r']],
                ["wrist_left", markers['hand_l']],
                ["hip_right", markers['thigh_r']],
                ["hip_left", markers['thigh_l']],
                ["knee_right", markers['knee_r']],
                ["knee_left", markers['knee_l']],
                ["ankle_right", markers['foot_r']],
                ["ankle_left", markers['foot_l']],
                ["toe_right", markers['toe_r']],
                ["toe_left", markers['toe_l']]]

            return ret

        if setName == "fbx":
            ret = {}
            ret['dof0'] = ["Spine"]
            ret['dof1'] = ["RightForeArm", "LeftForeArm", "RightLeg", "LeftLeg", "RightToeBase", "LeftToeBase"]
            ret['stiff'] = [["Spine1", 3], ["Neck", 4]]
            ret['root'] = "Hips"
            ret['connections'] = [
                ["Hips", markers['hips']],
                ["Spine2", markers['chest']],
                ["Head", markers['head']],
                ["RightShoulder", markers['clav_r']],
                ["LeftShoulder", markers['clav_l']],
                ["RightArm", markers['shoulder_r']],
                ["LeftArm", markers['shoulder_l']],
                ["RightForeArm", markers['elbow_r']],
                ["LeftForeArm", markers['elbow_l']],
                ["RightHand", markers['hand_r']],
                ["LeftHand", markers['hand_l']],
                ["RightUpLeg", markers['thigh_r']],
                ["LeftUpLeg", markers['thigh_l']],
                ["RightLeg", markers['knee_r']],
                ["LeftLeg", markers['knee_l']],
                ["RightFoot", markers['foot_r']],
                ["LeftFoot", markers['foot_l']],
                ["RightToeBase", markers['toe_r']],
                ["LeftToeBase", markers['toe_l']]]
            return ret

        raise RuntimeError("Invalid Bone Set")

    def connect(self, test=False):

        count = self.testMarkerset()
        if count != 0:
            print("Invalid Markerset")
            return

        count = self.testBoneset()
        if count != 0:
            print("Invalid Boneset")
            return

        markers = self.getMarkerset(self.markerset)
        bones = self.getBoneset(self.boneset, markers)

        if test:
            print("Tests ok")
            return

        for i in bones['stiff']:
            node = "%s%s" % (self.skel_prefix, i[0])
            if not m.objExists("%s.rotStiff" % node):
                m.addAttr(node, k=True, ln="rotStiff", at="double")
            m.setAttr("%s.rotStiff" % node, i[1])

        for i in bones['dof0']:
            m.setAttr(self.skel_prefix + i + ".rotateX", lock=True)
            m.setAttr(self.skel_prefix + i + ".rotateY", lock=True)
            m.setAttr(self.skel_prefix + i + ".rotateZ", lock=True)

        for i in bones['dof1']:
            m.setAttr(self.skel_prefix + i + ".rotateZ", lock=True)
            if self.boneset == "fbx":
                m.setAttr(self.skel_prefix + i + ".rotateX", lock=True)
            else:
                m.setAttr(self.skel_prefix + i + ".rotateY", lock=True)

        if not m.objExists("peelSolveOptions"): m.createNode("peelSolveOptions", n="peelSolveOptions");

        for i in bones['connections']:
            if i[1] is None: continue
            for j in i[1]:
                loc = mel.eval("peelSolve2CreateLineLocator(\"%s%s\", \"%s%s\");" % (
                self.marker_prefix, j, self.skel_prefix, i[0]))
                mel.eval("peelSolve2CreateTransform({\"%s\"}, 1);" % loc[0])
                m.connectAttr(self.marker_prefix + j + ".worldMatrix[0]", loc[0] + ".peelTarget")
            m.connectAttr(loc[0] + ".translationWeight", loc[1] + ".tWeight")
            m.connectAttr(loc[0] + ".rotationWeight", loc[1] + ".rWeight")

        m.setAttr("peelSolveOptions.rootNodes", 1, bones['root'], type='stringArray')

    # rootNode = x = mocap.Rig(marker_prefix="Skeleton3_", markerset="motive", boneset="fbx")
    # m_cmds.setAttr("peelSolveOptions.rootNodes", 1, rootNode, type='stringArray' )

    def drawMarkerLines(self):
        # lines = m_cmds.ls(type="PeelLine")
        # if len(lines) > 0 : m_cmds.delete(lines)

        conns = [
            ["LFoot_2", "LFoot_1", "LFoot_3", "LFoot_2", "LToe_1"],
            ["RFoot_2", "RFoot_1", "RFoot_3", "RFoot_2", "RToe_1"],
            ["Hip_1", "Hip_2", "Hip_4", "Hip_3", "Hip_1"],
            ["LHand_1", "LHand_2", "LHand_3", "LHand_1"],
            ["RHand_1", "RHand_2", "RHand_3", "RHand_1"],
            ["Head_1", "Head_2", "Head_3", "Head_1"],
            ["Chest_4", "Chest_3", "LShoulder_2", "Chest_2", "RShoulder_2", "Chest_4"],
            ["RShoulder_1", "Chest_1", "LShoulder_1", "RShoulder_1"],
            ["RShin_2", "RThigh_1", "RThigh_2", "RShin_2"],
            ["LShin_2", "LThigh_1", "LThigh_2", "LShin_2"],
            ["LUArm_1", "LUArm_2", "LShoulder_2", "LUArm_1"],
            ["RUArm_1", "RUArm_2", "RShoulder_2", "RUArm_1"],
            ["LUArm_1", "LHand_2"],
            ["RUArm_1", "RHand_2"],
            ["RShin_2", "RShin_1", "RFoot_3"],
            ["LShin_2", "LShin_1", "LFoot_3"],
            ["Chest_3", "Hip_3", "Hip_4", "Chest_4"],
            ["LThigh_1", "Hip_1", "Hip_2", "RThigh_1"],
            ["Chest_1", "Chest_3", "Chest_4", "Chest_1"],
            ["LShoulder_1", "LShoulder_2"],
            ["RShoulder_1", "RShoulder_2"],
            ["Chest_1", "Hip_1", "Hip_2", "Chest_1"]
        ]

        i = 0

        hip1 = self.marker_prefix + "Hip_1"
        if not m.objExists(hip1):
            print("Could not find: " + hip1)
            return

        topNode = m.listRelatives(hip1, p=True)[0]

        group = topNode + "|LINES"
        if not m.objExists(group): m.group(em=True, name="LINES", parent=topNode)

        for clist in conns:
            loc = m.createNode("PeelLine", p=group)
            for marker in clist:
                m.connectAttr("%s%s.translate" % (self.marker_prefix, marker), "%s.points[%d]" % (loc, i))
                i = i + 1

        for i in ["Head_3", "LShoulder_1"]:
            m.setAttr("%s%sShape.overrideEnabled" % (self.marker_prefix, i), 1);
            m.setAttr("%s%sShape.overrideColor" % (self.marker_prefix, i), 8)


def gui_getRig():
    marker_prefix = m.textFieldButtonGrp("peelMocapMarkerPrefix", q=True, tx=True)
    markerset = m.optionMenuGrp("peelMocapMarkerset", q=True, v=True)
    bone_prefix = m.textFieldButtonGrp("peelMocapBonePrefix", q=True, tx=True)
    boneset = m.optionMenuGrp("peelMocapBoneset", q=True, v=True)
    return Rig(boneset=boneset, skel_prefix=bone_prefix, markerset=markerset, marker_prefix=marker_prefix)


def gui_verify():
    rig = gui_getRig()
    missingMarkers = rig.testMarkerset()
    if missingMarkers == 0:
        m.textFieldGrp("peelMocapMarkerStatus", e=True, tx="Valid")
    else:
        m.textFieldGrp("peelMocapMarkerStatus", e=True, tx="Missing Markers: %d" % missingMarkers)
    markers = rig.uniqueMarkerList()
    for i in markers:
        m.textScrollList("peelMocapTSL", e=True, append=i)
    m.textScrollList("peelMocapTSL", e=True, lf=(4, "obliqueLabelFont"))


def gui_draw_lines(x):
    rig = gui_getRig()
    rig.drawMarkerLines()


def gui_createSolverTest(x):
    rig = gui_getRig()
    rig.connect(True)


def gui_createSolver(x):
    rig = gui_getRig()
    rig.connect(False)


def gui_select(x):
    rig = gui_getRig()
    markers = rig.uniqueMarkerList()
    m.select(cl=True)
    for i in markers:
        mkr = "%s%s" % (rig.marker_prefix, i)
        if m.objExists(mkr):
            m.select(mkr, add=True)
        else:
            print(mkr)


def gui_verifyBones():
    rig = gui_getRig()
    missingBones = rig.testBoneset()
    if missingBones == 0:
        m.textFieldGrp("peelMocapBoneStatus", e=True, tx="Valid")
    else:
        m.textFieldGrp("peelMocapBoneStatus", e=True, tx="Missing Bones: %d" % missingBones)


def gui():
    import maya.cmds as m
    if m.window("peelMocap", ex=True): m.deleteUI("peelMocap")
    win = m.window("peelMocap", width=400, height=400)
    form = m.formLayout()
    c1 = m.columnLayout()
    m.optionMenuGrp("peelMocapMarkerset", l="Markerset:")
    m.menuItem("motive")
    m.menuItem("mocapclub")
    m.textFieldButtonGrp("peelMocapMarkerPrefix", l="Marker Prefix:", bl="Verify", bc=gui_verify)
    m.textFieldGrp("peelMocapMarkerStatus", en=False, l="")
    m.textScrollList("peelMocapTSL")
    m.button(l="Select Markers", c=gui_select)
    m.button(l="Draw Lines", c=gui_draw_lines)
    m.button(l="Test Solver", c=gui_createSolverTest)
    m.button(l="Create Solver", c=gui_createSolver)

    m.setParent(form)
    c2 = m.columnLayout()
    m.optionMenuGrp("peelMocapBoneset", l="Boneset:")
    m.menuItem("fbx")
    m.textFieldButtonGrp("peelMocapBonePrefix", l="Bone Prefix:", bl="Verify", bc=gui_verifyBones)
    m.textFieldGrp("peelMocapBoneStatus", en=False, l="")

    m.formLayout(form, e=True, attachForm=[(c1, "top", 1), (c1, "left", 1), (c1, "bottom", 1),
                                           (c2, "top", 1), (c2, "right", 1), (c2, "bottom", 1)],
                 attachControl=[(c1, "right", 1, c2)])

    m.showWindow(win)
