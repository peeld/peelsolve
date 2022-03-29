import maya.cmds as m
import os
import os.path
import re


def load_plugin():
    """ Loads the PeelSolve and fbx plugins """

    m.loadPlugin("fbxmaya")

    if 'peelsolve' in ''.join(m.pluginInfo(q=True, ls=True)).lower():
        return

    ext = None
    my_os = m.about(os=True)
    if my_os == "mac":
        ext = "bundle"
    if my_os == "win" or my_os == "win64":
        ext = "mll"

    if not ext:
        raise RuntimeError("Could not determine OS: "+ str(my_os))

    version = m.about(v=True)
    latest = None
    for i in os.getenv("MAYA_PLUG_IN_PATH").split(";"):
        if not os.path.isdir(i):
            continue
        for j in os.listdir(i):
            ret = re.match("peel[sS]olve_([0-9]+)_([0-9]+)." + ext, j)
            if ret:
                if ret.group(2) == version:
                    peel_version = int(ret.group(1))
                    if latest is None or latest[0] < peel_version:
                        latest = (peel_version, os.path.join(i, j))

    if latest is None:
        m.error("Could not find a valid plugin")
        return

    print("Loading: " + latest[1])
    m.loadPlugin(latest[1])


