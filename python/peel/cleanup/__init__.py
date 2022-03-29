# Mocap Cleanup - Alastair Macleod 2016
# GPL License = http://www.gnu.org/licenses/gpl.txt 

import maya.cmds as m
import maya.mel as mel

def shelf() :

    """ Creates a peelMocapTools shelf """

    shelf_tab_name = "peelMocapTools"
    if not m.shelfLayout(shelf_tab_name, exists=True):
        shelf_tab_name = mel.eval("addNewShelfTab(\"%s\")" % shelf_tab_name)
        
    top_shelf = mel.eval("global string $gShelfTopLevel; string $x = $gShelfTopLevel")
    try:
        tool_shelf = m.shelfLayout("%s|%s" % (top_shelf, shelf_tab_name), q=True, ca=True)
        if tool_shelf is not None :
            if len(tool_shelf) > 0 : m.deleteUI(tool_shelf)
    except RuntimeError:
        pass

    kt = 'import peel.cleanup.keyTools as kt;kt.'
    mx = 'import peel.cleanup.mocap as mx;mx.'
    ms = 'import peel.cleanup.markerset as mz;mz.'
    la = 'import peel.cleanup.labeler as la;la.'
    ld = 'import peel.cleanup.loader as ld;ld.'
    ca = 'import peel.cleanup.camera as ca;ca.'
    
    buttons = [
      ["Load c3d",             mx + "loadc3d()",              "mocap_loadc3d.bmp"],
      ["Data",                 ld + "show()",                 "mocap_data.bmp"],
      ["Gui",                  la + "show()",                 "mocap_gui.bmp"],
      ["Fill",                 kt + "fill()",                 "mocap_fill.bmp"],
      ["Split Parts",          kt + "split_parts()",          "mocap_splitParts.bmp"],
      ["Swap Selected",        kt + "swap()",                 "mocap_swapSelected.bmp"],
      ["Swap All",             kt + "swap_all()",             "mocap_swapAll.bmp"],
      ["Extract Before",       kt + "extract_before()",       "mocap_extractBefore.bmp"],
      ["Extract After",        kt + "extract_after()",        "mocap_extractAfter.bmp"],
      ["Extract After Sel",    kt + "extract_selected()",     "mocap_extractSelected.bmp"],
      ["Set Current",          kt + "set_current('1')",       "mocap_setX.bmp"],
      ["Move to Current",      kt + "move_to_current('1')",   "mocap_moveToX.bmp"],
      ["Move 1 to 2",          kt + "move_first_to_second()", "mocap_moveFirstToSecond.bmp"],
      ["Key Current to match", kt + "key_current_to_match()", "mocap_keyCurrentToMatch.bmp"],
      ["Go to next gap",       kt + "goto_next_gap()",       "mocap_goToNextGap.bmp"],
      ["Toggle Active",        kt + "toggle_connect_vis()",   "mocap_eye.bmp"],
      ["Camera On",            ca + "rigidbody_cam()",        "mocap_cam_on.bmp"],
      ["Camera Off",           ca + "clear()",                "mocap_cam_off.bmp"],
    ]
    #  [ "Load web data",   "import loader\nx=loader.Loader()\nx.show()", "mocap_c3d.bmp" ],
    #  [ "Import Cameras",  "import camera\ncamera.importCameras()\n", "mocap_cam.bmp" ],
      
    for i in buttons :
      m.shelfButton(l=i[0], stp="python", c=i[1], i1=i[2], p=shelf_tab_name)


def keys():

    ''' creates some useful keyboard shortcuts (removing existing ones if they exist) '''

    kt = "import mocapCleanup.keyTools as kt;kt."
    la = "import mocapCleanup.labeler as la;la."

    cmds = [["Home",       "alt", "SetCurrent1",      "Set Current 1",     "p", kt + "setCurrent('1')"],
            ["Home",       ""   , "MoveToCurrent1",   "Move to current 1", "p", kt + "moveToCurrent('1')"],
            ["End",        "alt", "SetCurrent2",      "Set Current 2",     "p", kt + "setCurrent('2')"],
            ["End",        ""   , "MoveToCurrent2",   "Move to current 2", "p", kt + "moveToCurrent('2')"],
            ["Page_Up",    "alt", "SetCurrent3",      "Set Current 3",     "p", kt + "setCurrent('3')"],
            ["Page_Up",    ""   , "MoveToCurrent3",   "Move to current 3", "p", kt + "moveToCurrent('3')"],
            ["Page_Down",  "alt", "SetCurrent4",      "Set Current 4",     "p", kt + "setCurrent('4')"],
            ["Page_Down",  ""   , "MoveToCurrent4",   "Move to current 4", "p", kt + "moveToCurrent('4')"],
            ["8",          ""   , "ExtractSelected",  "Extract Selected",  "p", kt + "extractSelected()"],
            ["9",          ""   , "OneTwoTwo",        "One To Two",        "p", la + "onetwo()"]]
             
    for keycode, modifier, name, title, lang, cmd in cmds:
           
        if lang == "p": cmd="python(\"" + cmd + "\")"
        name = "peel" + name + "NameCommand"
        print("Setting " + keycode + " " + title + " to " + cmd)
        m.nameCommand(name, ann=title, c=cmd)
        if modifier == "alt":
            m.hotkey(keyShortcut=keycode, altModifier=True, name=name)
        else :
            m.hotkey(keyShortcut=keycode, name=name) 

