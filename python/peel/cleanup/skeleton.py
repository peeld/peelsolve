# Mocap Cleanup - Alastair Macleod 2016
# GPL License = http://www.gnu.org/licenses/gpl.txt 

import maya.cmds as m



def create() :

    ''' Create a default skeleton using Mobu names '''

    joints = [
     [ "Hips",           None,           [ 0,   90,   0 ],  [ 0, 0, -90 ] ],
     [ "LeftUpLeg",     "Hips",          [ 4.7,  8.5, 0 ],  [ 0, 0,   0 ] ],
     [ "LeftLeg",       "LeftUpLeg",     [ 40,   0,   0 ],  [ 0, 0,   0 ] ],
     [ "LeftFoot",      "LeftLeg",       [ 37,   0,   0 ],  [ 0, -60, 0 ] ],
     [ "LeftToeBase",   "LeftFoot",      [ 14,   0,   0 ],  [ 0, 0,   0 ] ],
     [ "RightUpLeg",    "Hips",          [ 4.7, -8.5, 0 ],  [ 0, 0,   0 ] ],
     [ "RightLeg",      "RightUpLeg",    [ 40,   0,   0 ],  [ 0, 0,   0 ] ],
     [ "RightFoot",     "RightLeg",      [ 37,   0,   0 ],  [ 0, -60, 0 ] ],
     [ "RightToeBase",  "RightFoot",     [ 14,   0,   0 ],  [ 0, 0,   0 ] ],
     [ "Spine",         "Hips",          [ -6,   0,   0 ],  [ 0, 180, 0 ] ],
     [ "Spine1",        "Spine",         [ 11,   0,   0 ],  [ 0, 0,   0 ] ],
     [ "Spine2",        "Spine1",        [ 11,   0,   0 ],  [ 0, 0,   0 ] ],
     [ "RightShoulder", "Spine2",        [ 15.7,-6.5, 0 ],  [ 0, 0, -90 ] ],
     [ "RightArm",      "RightShoulder", [ 9.5,  0,   0 ],  [ 0, 0,   0 ] ],
     [ "RightForeArm",  "RightArm",      [ 25,   0,   0 ],  [ 0, 0,   0 ] ],
     [ "RightHand",     "RightForeArm",  [ 24,   0,   0 ],  [ 0, 0,   0 ] ],
     [ "LeftShoulder",  "Spine2",        [ 15.7, 6.5, 0 ],  [ 0, 0,  90 ] ],
     [ "LeftArm",       "LeftShoulder",  [ 9.5,  0,   0 ],  [ 0, 0,   0 ] ],
     [ "LeftForeArm",   "LeftArm",       [ 25,   0,   0 ],  [ 0, 0,   0 ] ],
     [ "LeftHand",      "LeftForeArm",   [ 24,   0,   0 ],  [ 0, 0,   0 ] ],
     [ "Neck",          "Spine2",        [ 14,   0,   0 ],  [ 0, 0,   0 ] ],
     [ "Head",          "Neck",          [ 18,   0,   0 ],  [ 0, 0,   0 ] ],
     
    ]


     
    m.select(cl=True)
    dict = {}

    for j in joints:
      if j[1] != None : 
          if j[1] in dict :
              m.select(dict[j[1]])
          else :
              print("Not defind: ", j[1])
      jnt = m.joint(name=j[0], p=(0, 90, 0))
      dict[j[0]] = jnt
      tr = j[2]
      ro = j[3]
      print(jnt)
      m.setAttr(jnt + ".translate",  tr[0], tr[1], tr[2])
      m.setAttr(jnt + ".jointOrient",  ro[0], ro[1], ro[2])
