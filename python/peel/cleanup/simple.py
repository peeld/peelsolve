# Mocap Cleanup - Alastair Macleod 2016
# GPL License = http://www.gnu.org/licenses/gpl.txt 

import maya.cmds as m

# Import your c3d or trc data in to maya using peelsolve
# use these commands to change the color of the markers, draw lines between them
# and toggle their visiblity when inactive.
# PeelSolve can be downloaded from: http://mocap.ca/peelsolve/download.html
# You will get a warning that the software is for eval use only, but it will
# display the mocap data ok, only the mocap solver is limited in the eval version.

''' Legacy Code '''

def NaturalPointSetup(prefix = "") :

    markerList = [ 
        'Chest_1', 'Chest_2', 'Chest_3', 'Chest_4', 
        'Head_1', 'Head_2', 'Head_3', 
        'Hip_1', 'Hip_2', 'Hip_3', 'Hip_4', 
        'LFoot_1', 'LFoot_2', 'LFoot_3', 
        'LHand_1', 'LHand_2', 'LHand_3', 
        'LShin_1', 'LShin_2', 
        'LShoulder_1', 'LShoulder_2', 
        'LThigh_1', 'LThigh_2', 'LToe_1', 
        'LUArm_1', 'LUArm_2', 
        'RFoot_1', 'RFoot_2', 'RFoot_3', 
        'RHand_1', 'RHand_2', 'RHand_3', 
        'RShin_1', 'RShin_2', 
        'RShoulder_1', 'RShoulder_2', 
        'RThigh_1', 'RThigh_2', 'RToe_1', 
        'RUArm_1', 'RUArm_2' ] 

    conns = [
          [ "LFoot_2", "LFoot_1", "LFoot_3", "LFoot_2", "LToe_1" ],
          [ "RFoot_2", "RFoot_1", "RFoot_3", "RFoot_2", "RToe_1" ],
          [ "Hip_1", "Hip_2", "Hip_4", "Hip_3", "Hip_1" ],
          [ "LHand_1", "LHand_2", "LHand_3", "LHand_1" ],
          [ "RHand_1", "RHand_2", "RHand_3", "RHand_1" ],
          [ "Head_1",  "Head_2",  "Head_3",  "Head_1"  ],
          [ "Chest_4", "Chest_3", "LShoulder_2", "Chest_2", "RShoulder_2", "Chest_4"],
          [ "RShoulder_1", "Chest_1", "LShoulder_1", "RShoulder_1" ],
          [ "RShin_2",  "RThigh_1", "RThigh_2", "RShin_2" ],
          [ "LShin_2",  "LThigh_1", "LThigh_2", "LShin_2" ],
          [ "LUArm_1",  "LUArm_2",  "LShoulder_2", "LUArm_1" ],
          [ "RUArm_1",  "RUArm_2",  "RShoulder_2", "RUArm_1" ],
          [ "LUArm_1" , "LHand_2" ],
          [ "RUArm_1" , "RHand_2" ],
          [ "RShin_2" , "RShin_1", "RFoot_3" ],
          [ "LShin_2" , "LShin_1", "LFoot_3" ],
          [ "Chest_3",  "Hip_3",  "Hip_4", "Chest_4" ],
          [ "LThigh_1", "Hip_1",  "Hip_2", "RThigh_1" ],
          [ "Chest_1", "Chest_3", "Chest_4", "Chest_1" ],
          [ "LShoulder_1", "LShoulder_2" ],
          [ "RShoulder_1", "RShoulder_2" ],
          [ "Chest_1", "Hip_1", "Hip_2", "Chest_1" ]
        ]

    #draw lines between the locators
    drawLines(conns, prefix)  

    # toggle visibility of the locators when they are not active
    toggleVis() 

    # change the color of the markers
    colorMarkers(markerList, prefix)


def toggleVis(markerList = None, prefix = "") :
    
    if markerList is None :
        all = m.ls(type="peelSquareLocator")
        markerList = []
        for i in all :
            markerList.append( m.listRelatives(i, p=True)[0] )
    
    node0 = prefix + markerList[0]
    if not m.objExists(node0) :
        print("Could not find: " + prefix + markerList[0])
        return
    attr0 = node0 + ".active"
    if not m.objExists(attr0) :
        print("Could not find attribute: " + prefix + markerList[0] + ".active")
        return
        
    conn0 = m.listConnections(node0 + ".visibility", s=True, p=True, d=False)
    if conn0 is not None and attr0 in conn0 : 
        state = True  
    else :
        state = False
    
    for i in markerList :
        node = prefix + i
        attr = node + ".active"
        if state :
            try :
                m.disconnectAttr(attr, node + ".visibility")
                m.setAttr(node + ".visibility", 1)
            except RuntimeError :
                pass
        else :
            try :
                m.connectAttr(attr, node + ".visibility")     
            except RuntimeError :
                pass
        

def colorMarkers(markerList, prefix = "", color = 17) :

    for i in markerList:
        m.setAttr("%s%sShape.overrideEnabled" % (prefix, i), 1);
        m.setAttr("%s%sShape.overrideColor"   % (prefix, i), color);


def drawLines(conns, prefix = "") :

    # uncomment the next two lines if you want to delete all lines first
        #lines = m_cmds.ls(type="PeelLine")
        #if len(lines) > 0 : m_cmds.delete(lines)

        i = 0

        hip1 = prefix + "Hip_1"
        if not m.objExists( hip1 ) :
                print("Could not find: " + hip1)
                return

        topNode = m.listRelatives(hip1, p=True)[0]

        group = topNode + "|LINES"
        if not m.objExists(group) : m.group(em=True, name="LINES", parent=topNode)

        for clist in conns:
            loc = m.createNode("PeelLine", p=group)
            for marker in clist :
                m.connectAttr( "%s%s.translate" % (prefix, marker), "%s.points[%d]" % (loc, i))
                i = i + 1

        
