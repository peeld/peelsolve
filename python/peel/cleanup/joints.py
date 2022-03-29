# Mocap Cleanup - Alastair Macleod 2016
# GPL License = http://www.gnu.org/licenses/gpl.txt 


HIPS      = 10
CHEST     = 20
SPINE1    = 21
SPINE2    = 22
SPINE3    = 23
NECK      = 30
HEAD      = 31
CLAVL     = 40
CLAVR     = 41
SHOULDERL = 51
SHOULDERR = 52
ARMROLLL  = 53
ARMROLLR  = 54
ELBOWL    = 60
ELBOWR    = 61
FOREROLLL = 62
FOREROLLR = 63
HANDL     = 70
HANDR     = 71
HIPL      = 80
HIPR      = 81
LEGROLLL  = 82
LEGROLLR  = 83
KNEEL     = 90
KNEER     = 91
SHNROLLL  = 92
SHNROLLR  = 93
FOOTL     = 100
FOOTR     = 101
TOEL      = 110
TOER      = 111



fbx = {
    HIPS   :'Hips' ,
    SPINE1 :'Spine' ,
    SPINE2 :'Spine1' ,
    CHEST  :'Spine2' ,
    HEAD   :'Head' ,
    NECK   :'Neck' ,
    CLAVR  :'RightShoulder' ,
    CLAVL  :'LeftShoulder' ,
    SHOULDERR :'RightArm' ,
    SHOULDERL :'LeftArm' ,
    ARMROLLR  :'RightArmRoll' ,
    ARMROLLL  :'LeftArmRoll' ,
    ELBOWR    :'RightForeArm' ,
    ELBOWL    :'LeftForeArm' ,
    FOREROLLL :'LeftForeArmRoll' ,
    FOREROLLR :'RightForeArmRoll' ,
    HANDR  :'RightHand' ,
    HANDL  :'LeftHand' ,
    HIPR   :'RightUpLeg' ,
    HIPL   :'LeftUpLeg' ,
    LEGROLLL:'LeftUpLegRoll',
    LEGROLLR:'RightUpLegRoll',
    SHNROLLL:'LeftLegRoll',
    SHNROLLR:'RightLegRoll',
    KNEER  :'RightLeg' ,
    KNEEL  :'LeftLeg' ,
    FOOTR  :'RightFoot' ,
    FOOTL  :'LeftFoot' ,
    TOER   :'RightToeBase' ,
    TOEL   : 'LeftToeBase' }

import maya.cmds as m

def prefixes( jointSet = fbx ) :
    ''' return a list of valid prefixes for the joints (all joints must exist) '''
    result = None
    for jointName in fbx.values() :
        items = m.ls('*:' + jointName)
        prefixes = [  v[ : -len(jointName) ] for v in items ]
        if result is None :
            result = set( prefixes )
        else :
            result = result & set( prefixes )

    return list(result)

        

