# Mocap Cleanup - Alastair Macleod 2016
# GPL License = http://www.gnu.org/licenses/gpl.txt 

from peel.cleanup import markerset as ms
from peel.cleanup import key_tools as kt
from peel.cleanup import datarate
import maya.cmds as m


def run():
    """ run the steps on a freshly imported c3d to prep it for cleaning """

    print("---- BUILD CLEANING ---")

    datarate.setSceneRate()

    # set default to circle/cross
    ms.display_mode_all(3)

    # set all markers to having visibility connected to active
    kt.toggle_connect_vis(force=True)

    # for each marker in the markerset, set some default display stuff
    col = 14
    for pfx in ms.prefixes():

        set_name = ms.guess(pfx)  # returns string
        if set_name is None:
            m.warning("No markerset for preix " + str(prefix))
            continue

        print("Prefix: %s    Markerset: %s" % (pfx, set_name))

        mobj = ms.markersets[set_name]

        # turn off connect-vis for labeled markers
        for mkr in mobj.markers():
            if m.objExists(pfx + mkr):
                kt.toggle_connect_vis([pfx + mkr], force=False)

                # set the color
        mobj.set_color(pfx, col)
        col += 1

        # draw th lines
        mobj.draw_lines(pfx)
