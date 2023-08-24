# Mocap Cleanup - Alastair Macleod 2016
# GPL License = http://www.gnu.org/licenses/gpl.txt 


import maya.cmds as m
import maya.OpenMaya as om


INTERVAL = None


def setSceneRate( fps = None ) :

    if fps is None :
        g = guess()
        if g is None :
            m.warning("Could not find rate")
            return
            
        print("Interval: ", g)
        fps = framesPerSecond( g )
        
    if   abs( fps - 15) < 0.5  : m.currentUnit( time = 'game')
    elif abs( fps - 24) < 0.5  : m.currentUnit( time = 'film')
    elif abs( fps - 25) < 0.5  : m.currentUnit( time = 'pal')
    elif abs( fps - 30) < 0.5  : m.currentUnit( time = 'ntsc')
    elif abs( fps - 48) < 0.5  : m.currentUnit( time = 'show')
    elif abs( fps - 50) < 0.5  : m.currentUnit( time = 'palf')
    elif abs( fps - 60) < 0.5  : m.currentUnit( time = 'ntscf')
    elif abs( fps - 120) < 0.5 : m.currentUnit( time = '120fps' )
    else :
        m.warning("Could not determine frame rate from: ", str(fps))
        
    
def mayaUnit() :
    return om.MTime( 1, om.MTime.kSeconds).asUnits( om.MTime.uiUnit() )

def framesPerSecond( interval ) :

    ''' Converts an interval to frames per second at current maya units.  This can be used to
        determine what fps the mocap data was recorded at, given the interval between the frames 

        For example if the current maya settings is set to "Film" (24fps), then an interval
        of 1 would return 24.  If the interval was 0.2 then this would return 120.  
    '''
    
    if interval is None or abs(interval) < 0.001 :
        raise ValueError("Invalid data rate: " + str(interval) + " - common values are 1 or 0.2)")

    return  1/ interval *  mayaUnit()


def keysPerFrame( dataRate ) :
    ''' returns spacing of data keys within a maya frame. 
    e.g. if the maya units are film/24fps and the c3d data rate is
    120fps, this will return 0.2 ( 24.0/120.0 ) '''
    if dataRate is None or abs(dataRate) < 0.01 :
        raise ValueError("Invalid data rate: " + str(dataRate) + " - common values are 48.0, 120.0 or 240.0 )")
    return  om.MTime( 1/ dataRate, om.MTime.kSeconds).asUnits( om.MTime.uiUnit() )



def get(node) :

    ''' get the interval for the data.  First is will try to use nodeRate to get the interval attribute
        that was created when the c3d was imported.  If that does not succeed, the keys will be sampled
        to determine the data rate using guess() 

        If the C3dRate attribte is not available the user will be prompted to confirm the data rate and
        this rate will be saved as a global INTERVAL attribute

    '''

    interval = nodeRate(node)

    if interval is not None : return interval

    guessed = guess()
    if guessed is None or guessed < 0.0001 :
        m.warning("Could not determine interval for: " + str(node) )
        return None

    fps = framesPerSecond( guessed )

    if m.confirmDialog(m="No datarate set for: " + node + " Set as: " + str(fps), b=['Yes', 'No']) == "Yes" :

        m.addAttr( node, ln='C3dRate', at='float')
        m.setAttr( node + '.C3dRate', fps )
        return guessed

    return None


def guess(nodes = None) :
    ''' returns a guess for the current framerate of the data, as a fraction of a frame.
        The keys are sampled for the intervals and the most common interval is returned '''

    deltas = {}

    if type(nodes) in [ str, unicode ] : nodes = [nodes]

    if nodes is None : nodes = m.ls(type = "peelSquareLocator")

    for mkr in nodes :

        if m.nodeType(mkr) == "peelSquareLocator" :
            mkr = m.listRelatives(mkr, p=True, f=True)[0]
            
            if m.objExists(mkr + ".C3dRate") : 
                val = m.getAttr( mkr + ".C3dRate" )
                if val > 0 : return keysPerFrame(val)

        if not m.objExists (mkr + ".tx") : continue

        keys = m.keyframe( mkr + ".tx", q=True )
        if keys is None : continue

        keys = sorted(keys)

        for i in range(1, len(keys)) :
            diff = round( keys[i] - keys[i-1], 4)
            if diff not in deltas :
                deltas[diff] = 1
            else :
                deltas[diff] = deltas[diff] + 1

    if len(deltas) == 0 : return None

    x = sorted( deltas, key = lambda v : deltas[v] )

    return x[-1]

def channelRate( chan ) :

    ''' return the interval of a particular channel (node.attr).  nodeRate() is used first, then guess() '''

    # if type(chan) not in [ str, unicode ] : raise ValueError( "Invalid channel: " + str( chan ) )
    if '.' not in chan : raise ValueError( "Value is not a channel: " + str(chan))

    node, attr = chan.split('.')

    nr = nodeRate( node )

    if nr is not None :
        return nr

    return guess( [node] )



def nodeRate( node ) :

    ''' returns the value of node.C3dRate, which is usually created by the peel c3d importer '''

    if m.objExists( node + ".C3dRate" ) :
        return keysPerFrame( m.getAttr( node + ".C3dRate" ) )

    return None

    
         

def setRateInput(nodes=None) :

    ''' set the node.C3dRate attribute for the nodes.  User is prompted for a value '''

    ret = m.promptDialog( m="Data Rate:", text="120", b='Set')
    if ret  != "Set" : return

    svalue = m.promptDialog( q=True, text=True )
    fvalue = float(svalue)

    if fvalue <= 0 : 
        m.warning("Invalid value" + str( svalue ) )
    
    if nodes is None: nodes = m.ls(type='peelSquareLocator')

    c = 0
    for node in nodes:

        if not m.objExists( node + ".C3dRate" ) :
            m.addAttr( node, ln='C3dRate', at='float' )
        m.setAttr( node + ".C3dRate", fvalue)
        c += 1

    print("%d nodes set" % c)
