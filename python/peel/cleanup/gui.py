# Mocap Cleanup - Alastair Macleod 2016
# GPL License = http://www.gnu.org/licenses/gpl.txt 

from Qt import QtGui, QtCore, QtWidgets
import maya.cmds as m
from maya import OpenMayaUI as omui
from shiboken2 import wrapInstance

def mainWindow():

    omui.MQtUtil.mainWindow()
    ptr = omui.MQtUtil.mainWindow()

    widget = wrapInstance(long(ptr), QtWidgets.QWidget)

    #for obj in QtWidgets.qApp.topLevelWidgets():
    #    if obj.objectName() == 'MayaWindow':
    #        return obj

    #return None


def table_item(value, data=None, edit=False):

    item = QtWidgets.QTableWidgetItem(value)
    if not edit:
        item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
    if data is not None:
        item.setData(QtCore.Qt.UserRole, data)

    return item

def changes() :
    """ checks to see if there are any changes, prompts the user if
        there is.  returns true if it is ok to proceed """

    if not m.file(mf=True, q=True) : return True

    msg = "You have unsaved changes... continue?"
    ret =  m.confirmDialog(m=msg, b=['Yes', 'No'])
    return ret == 'Yes' 

def wait(value) :
    m.waitCursor(state=value)


def int_item(item, default=0):
    if item is None:
        return default

    try:
        return int(item.text())
    except ValueError:
        return default

