# Mocap Cleanup - Alastair Macleod 2016
# GPL License = http://www.gnu.org/licenses/gpl.txt 

import maya.cmds as m
from peel.cleanup import gui, c3dParser
import os
import os.path

''' This module is responsible for making things happen, like loading/saving files etc.
    The the data class (mocapData) should not have any maya.cmds in it so it can remain
    portable.  The Gui classes (e.g Loader) should deal with gui managements, and when
    an action needs taken the actual path, etc should be resolved and passed here. '''


def fileAction(item, mode):

    print("File Action: " + mode)
    print(item.path())
    
    if mode != 'save' and not item.exists() : 
        m.confirmDialog(m="Item does not exist")
        return False

    if mode == 'open' and gui.changes() is False : return False

    if mode == 'save':
        if item.exists() :
            print("File exists: " +  item.path())
            raise RuntimeError("Oops!")
            
        try:
            path, ext = os.path.split( item.path() )
            if not os.path.isdir( path ) : os.mkdir( path )

            m.file( rename=item.path() )
            m.file( save=True )   

            return True
            
        except Exception as e:
            m.warning(e)
            return False

    if item.data_type() == 'c3d':
        if mode == 'open':
            m.file(f=True, new=True)

        info = c3dParser.load(item.path())
        convert_axis = info.convert_axis()
        return import_c3d(item.path(), convert_axis=convert_axis)
 
    if item.data_type() == 'maya':
        if mode == 'open':
            m.file(item.path(), o=True, f=True, prompt=False)
        else:
            m.file(item.path(), i=True, f=True)
        return True
        
    return False


def import_c3d(file_path, merge=False, convert_axis=False):

    """ Import a c3d file of type peelC3D.  If merge is true th ethen c3d merge option will be true """

    ops = "merge=%d;convert=%d;" % (int(merge), int(convert_axis))
    
    print("Importing " + file_path)
    print("Options: " + ops)

    try :
        m.file(file_path, i=True, type="peelC3D", options=ops)
        return True
    except Exception as e :
        print(str(e))
        m.warning("Could not import c3d file... is the plugin loaded? " + str(e))
        return False

    #for mrk in m_cmds.ls(type="peelSquareLocator") :
    #    if m_cmds.objExists( mrk + ".displayMode") :
    #        m_cmds.setAttr( mrk + ".displayMode", 3 )
