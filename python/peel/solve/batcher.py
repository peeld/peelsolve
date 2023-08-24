from PySide2 import QtWidgets, QtCore

import maya.cmds as m
from maya import OpenMayaUI as omui
from shiboken2 import wrapInstance
import os
import math
from maya import mel


class FilePathWidget(QtWidgets.QWidget):
    path_changed = QtCore.Signal(str)

    def __init__(self, name, settings, default="", parent=None):
        super(FilePathWidget, self).__init__(parent)

        self.name = name
        self.settings = settings

        self.file_path = QtWidgets.QLineEdit()
        self.file_path.setText(settings.value(name + "Path", default))
        self.file_path.editingFinished.connect(self.save_path)
        self.button = QtWidgets.QPushButton("...")
        self.button.pressed.connect(self.browse)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.file_path)
        layout.addWidget(self.button)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)

    def save_path(self):
        path = self.file_path.text()
        self.settings.setValue(self.name + "Path", path)
        self.path_changed.emit(path)

    def browse(self):
        ret = QtWidgets.QFileDialog.getExistingDirectory(self, self.name, self.text())
        if ret:
            self.file_path.setText(ret)
            self.save_path()
            self.path_changed.emit(ret)

    def text(self):
        return self.file_path.text()

    def set_text(self, value):
        self.file_path.setText(value)


class Gui(QtWidgets.QDialog):
    def __init__(self):
        omui.MQtUtil.mainWindow()
        ptr = omui.MQtUtil.mainWindow()
        window = wrapInstance(int(ptr), QtWidgets.QWidget)
        super().__init__(window)

        self.setWindowTitle("Peel Solve Batcher")

        self.settings = QtCore.QSettings("PeelSolve", "Batcher")

        # Splitter
        self.widget_left = QtWidgets.QWidget()
        self.widget_right = QtWidgets.QWidget()
        splitter = QtWidgets.QSplitter()
        splitter.addWidget(self.widget_left)
        splitter.addWidget(self.widget_right)

        ###################
        # Left

        layout_left = QtWidgets.QVBoxLayout()

        layout_left.addWidget(QtWidgets.QLabel("Templates"))

        # Template Dir
        self.template_dir = FilePathWidget("TemplateDir", self.settings)
        self.template_dir.path_changed.connect(self.populate_templates)
        layout_left.addWidget(self.template_dir)

        self.templates = QtWidgets.QListWidget()
        layout_left.addWidget(self.templates)

        left_buttons = QtWidgets.QHBoxLayout()
        left_buttons.addStretch(1)

        self.refresh_templates = QtWidgets.QPushButton("Refresh")
        self.refresh_templates.released.connect(self.populate_templates)
        left_buttons.addWidget(self.refresh_templates)
        left_buttons.addStretch(1)

        self.new_template_button = QtWidgets.QPushButton("+")
        self.new_template_button.released.connect(self.new_template)
        left_buttons.addWidget(self.new_template_button)
        left_buttons.addStretch(1)

        self.load_template_button = QtWidgets.QPushButton("Open")
        self.load_template_button.released.connect(self.load_template)
        left_buttons.addWidget(self.load_template_button)
        left_buttons.addStretch(1)

        layout_left.addItem(left_buttons)

        self.widget_left.setLayout(layout_left)

        #################
        # Right

        layout_right = QtWidgets.QVBoxLayout()

        layout_right.addWidget(QtWidgets.QLabel("Data"))

        # C3D Dir
        self.c3d_dir = FilePathWidget("C3dDir", self.settings)
        self.c3d_dir.path_changed.connect(self.populate_c3d)
        layout_right.addWidget(self.c3d_dir)

        self.c3d_files = QtWidgets.QListWidget()
        self.c3d_files.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        layout_right.addWidget(self.c3d_files)

        right_buttons = QtWidgets.QHBoxLayout()
        right_buttons.addStretch(1)

        self.refresh_c3d = QtWidgets.QPushButton("Refresh")
        self.refresh_c3d.released.connect(self.populate_c3d)
        right_buttons.addWidget(self.refresh_c3d)
        right_buttons.addStretch(1)

        self.load_c3d_button = QtWidgets.QPushButton("Import")
        self.load_c3d_button.released.connect(self.load_c3d)
        right_buttons.addWidget(self.load_c3d_button)
        right_buttons.addStretch(1)

        layout_right.addItem(right_buttons)

        self.widget_right.setLayout(layout_right)

        # Main Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(splitter)

        # OutDir
        self.out_dir = FilePathWidget("OutDir", self.settings)
        layout.addWidget(self.out_dir)

        # Log
        self.log = QtWidgets.QPlainTextEdit()
        layout.addWidget(self.log)

        # Tools
        tool_layout = QtWidgets.QHBoxLayout()

        self.go_button = QtWidgets.QPushButton("Start")
        self.go_button.released.connect(self.go)
        tool_layout.addWidget(self.go_button, 1)

        tool_layout.addStretch(1)

        self.progress = QtWidgets.QProgressBar()
        tool_layout.addWidget(self.progress, 2)

        tool_layout.addStretch(1)
        layout.addItem(tool_layout)

        self.setLayout(layout)

        self.populate_templates()
        self.populate_c3d()

    def new_template(self):
        if not m.objExists("peelSolveOptions"):
            QtWidgets.QMessageBox.warning(self, "Error", "Could not find a solve setup")
            return

        if m.file(mf=True, q=True):
            QtWidgets.QMessageBox.warning(self, "Error", "Please save the scene first")
            return

        name, ret = QtWidgets.QInputDialog.getText(self, "New Template", "Name")
        if not ret:
            return

        current_file = m.file(q=True, sn=True)
        ext = ".mb"
        if current_file:
            ext = os.path.splitext(current_file)[1]

        template_path = os.path.join(self.template_dir.text(), name + ext)
        if os.path.isfile(template_path):
            mode = QtWidgets.QMessageBox.Information
            ops = QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            msg = "Template Exists - overwrite?"
            ret = QtWidgets.QMessageBox(mode, "Template", msg, ops).exec_()
            if ret != QtWidgets.QMessageBox.Yes:
                return

        m.file(rename=template_path)
        m.file(save=True)

        m.file(current_file, o=True)

        self.populate_templates()

    def populate_templates(self):
        self.templates.clear()
        if not os.path.isdir(self.template_dir.text()):
            return
        for i in os.listdir(self.template_dir.text()):
            if i.startswith("."):
                continue
            ext = os.path.splitext(i)[1]
            if ext.lower() in [".ma", ".mb"]:
                self.templates.addItem(i)

    def populate_c3d(self):
        self.c3d_files.clear()
        if not os.path.isdir(self.c3d_dir.text()):
            return
        for i in os.listdir(self.c3d_dir.text()):
            if i.startswith("."):
                continue
            ext = os.path.splitext(i)[1]
            if ext.lower() == ".c3d":
                self.c3d_files.addItem(i)

    def import_c3d(self, file_path, merge=True, convert_axis=True):

        if merge:
            root = m.ls(type="peelOpticalRoot")
            if not root:
                print("Could not find optical root")
                return False

            m.select(m.listRelatives(root[0], p=True))

        ops = "merge=%d;convert=%d;" % (int(merge), int(convert_axis))

        print("Importing " + file_path)
        print("Options: " + ops)

        try:
            m.file(file_path, i=True, type="peelC3D", options=ops)
            return True
        except Exception as e:
            print(str(e))
            m.warning("Could not import c3d file... is the plugin loaded? " + str(e))
            return False

    def load_template(self):
        template = self.templates.selectedItems()
        if not template:
            return

        template = os.path.join(self.template_dir.text(), template[0].text())

        if m.file(mf=True, q=True):
            msg = "You have unsaved changes... continue?"
            ret = m.confirmDialog(m=msg, b=['Yes', 'No'])
            if ret != 'Yes':
                return

        m.file(template, o=True, f=True, prompt=False)

    def load_c3d(self):
        c3d = self.c3d_files.selectedItems()
        if not c3d:
            return

        c3d_file = os.path.join(self.c3d_dir.text(), c3d[0].text())
        self.import_c3d(c3d_file, merge=False)

    def set_range(self):

        minval = None
        maxval = None

        for marker_shape in m.ls(type="peelSquareLocator"):
            marker = m.listRelatives(marker_shape, parent=True)[0]
            kz = m.keyframe(marker, q=True)
            if not kz:
                continue

            low = math.floor(min(kz))
            high = math.ceil(max(kz))

            if minval is None or low < minval:
                minval = low

            if maxval is None or high > maxval:
                maxval = high

        if minval is None:
            print("No keys found")
            return False

        m.playbackOptions(min=minval, max=maxval)
        return True

    def clean_scene(self):
        m.delete(m.ls(type="peelSolveOptions", l=True))

        for i in m.ls(type="peelOpticalRoot", l=True):
            m.delete(m.listRelatives(i, parent=True, f=True)[0])

        for i in m.ls(type="peelLocator", l=True):
            m.delete(m.listRelatives(i, parent=True, f=True)[0])

    def go(self):

        out_dir = self.out_dir.text()
        if not out_dir:
            self.out_dir.browse()
            out_dir = self.out_dir.text()
            if not out_dir:
                return

        solved_dir = os.path.join(out_dir, "solved")
        if not os.path.isdir(solved_dir):
            os.mkdir(solved_dir)

        fbx_dir = os.path.join(out_dir, "fbx")
        if not os.path.isdir(fbx_dir):
            os.mkdir(fbx_dir)

        for c3d in self.c3d_files.selectedItems():

            self.load_template()

            current_file = m.file(q=True, sn=True)
            ext = os.path.splitext(current_file)[1]

            # Import c3d
            c3d_file = os.path.join(self.c3d_dir.text(), c3d.text())
            self.import_c3d(c3d_file, merge=True)

            # Set frame range
            self.set_range()

            # Solve it.
            mel.eval("peelSolve2Run(1)")

            # Save maya file
            name = os.path.splitext(c3d.text())[0]
            out_solved = os.path.join(solved_dir, name + ext)
            m.file(rename=out_solved)
            m.file(save=True)

            # Save fbx
            self.clean_scene()
            out_fbx = os.path.join(fbx_dir, name + ".fbx")
            m.file(out_fbx, force=True, type="FBX export", ea=True)

            m.file(f=True, new=True)


INSTANCE = None
def show():
    global INSTANCE
    INSTANCE = Gui()
    INSTANCE.show()
    return INSTANCE

if __name__ == "__main__":
    show()
