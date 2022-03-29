import maya.cmds as m
import maya.mel as mel


def create() :

    sel = m.ls(sl=True)
    rbn = mel.eval('peelSolve2RigidBody()')
 
    # find the common parent   
    ret = set()
    for n in sel:
        p = m.listRelatives(n, p=True)
        if p is None : continue
        ret.add(p[0])

    if len(ret) == 1:
        parent = list(ret)[0]
    else :
        parent = None

    cons = []
    locs = []

    # for each marker
    for i in range (len(sel)) :

        input = m.listConnections( rbn + ".input[%d]" % i )[0] 
        local = m.listConnections( rbn + ".local[%d]" % i )[0] 

        # create locators and constrain to local rigidbody markers
        loc = m.spaceLocator( name=sel[i] + '_temp' )[0]
        if parent :
            loc = m.parent( loc, parent ) [0]
        cons.append(  m.pointConstraint( local, loc )[0] )
        locs.append( loc )

        # link active to weight
        src = input + ".active"
        dst = local + ".weight"
        if m.objExists(src) :
            m.connectAttr( src, dst )

    # bake
    try :
        m.refresh(suspend=True)
        start = m.playbackOptions(q=True, min=True)
        end = m.playbackOptions(q=True, max=True)
        m.bakeResults(locs, sm=True, t=(start,end), sb=1, dic=True, pok=True, sac=False, at=('tx', 'ty', 'tz') )

    finally :
        m.refresh(suspend=False)

    m.delete( cons )
        


