# Mocap Cleanup - Alastair Macleod 2016
# GPL License = http://www.gnu.org/licenses/gpl.txt

import os.path
import os
import json
import math
from functools import partial

from peel.cleanup.Qt import QtWidgets, QtCore, QtWidgets
import maya.cmds as m_cmds
from peel.cleanup import buildCleaning, buildSolving, gui, fileCache, mocapData, actions, markerset
from peel.util import roots
import peel

dockable = True


class EmptyClass(object):
    pass


try:
    from maya.app.general.mayaMixin import MayaQWidgetDockableMixin as BaseWidget

    baseclass1 = BaseWidget
    baseclass2 = QtWidgets.QWidget

except:
    baseclass1 = QtWidgets.QDialog
    baseclass2 = EmptyClass
    dockable = False


INSTANCE = None


def show(force=False):
    """ Shows the loader. Uses INSTANCE as a global variable. """

    global INSTANCE
    if not INSTANCE or force:
        INSTANCE = Loader()

    global dockable

    peel.load_plugin()

    if dockable:
        INSTANCE.show(dockable=True)
    else:
        INSTANCE.show()


class Loader(baseclass1, baseclass2):
    """ Reads an index from a parser class, and displays a loader gui. """

    def get_message(self, value):
        """ Adds the value of the argument passed in, to the log message
        :param value: the message that is to be displayed in the log
        :type value: str """
        self.log.append(value)

    def get_error(self, value):
        """ Adds the value of the argument passed in, to the error_log message
        :param value: the message that is to be displayed in the log
        :type value: str """
        self.error_log.append(value)

    def get_progress(self, stage, current, max_val, message):
        """ Sets the current progress value for the progress window.
        stage = 0 implies it's at the beginning, so it sets the progress window title, and gives it a max value.
        stage = 5 implies the end of progress, so it terminates the window.
        :param stage: stage of progress
        :type stage: int
        :param current: current progress amount in the stage
        :type current:
        :param max_val: max progress in each stage
        :type max_val: int
        :param message: status message
        type message: str"""

        if stage == 0 and current == 0:
            m_cmds.progressWindow(title="Loading")  # max = 100 by default.

        if stage == 5:
            m_cmds.progressWindow(endProgress=True)
            return

        if max_val == 0:
            return

        value = stage * 25 + 25 * current / max_val
        # Percentage of ( Stage + progress in current stage )
        # Percentage of (  Stage(1,2,3..so on).. plus whatever is the current progress as a fraction of the max_val  )

        m_cmds.progressWindow(e=True, status=message, progress=value)

    def __init__(self, parser=None):
        """Sets the window title, sets up the parser, initializes the UI elements, loads the marker set, loads data,
         and populates the rig menu.
         :param parser: Unless specified by the calling application, it is an object of Parser class in mocapData
         :type parser: object of Parser"""

        # wrap to maya
        super(Loader, self).__init__(parent=gui.mainWindow())

        self.setWindowTitle("Mocap Loader")

        self.parser = parser

        if self.parser is None:
            # get the current base_dir (set by the menu option)
            if m_cmds.optionVar(exists='peelLoaderDirectory'):
                base_dir = m_cmds.optionVar(q='peelLoaderDirectory')
                self.parser = mocapData.Parser(base_dir)
            else:
                self.parser = None

        if self.parser:
            self.parser.message.connect(self.get_message)
            self.parser.error.connect(self.get_error)
            self.parser.progress.connect(self.get_progress)

        markerset.load_all()

        if len(markerset.markersets) == 0:
            m_cmds.warning("No marker sets loaded.")

        self.cache = fileCache.FileCache()
        self.pathPrefix = "/2"

        # dont move this next line to further down - it needs to be here for some reason
        main_layout = QtWidgets.QVBoxLayout(self)

        ##########
        # topBar

        # session combo
        self.selector = QtWidgets.QComboBox(self)
        self.selector.currentIndexChanged.connect(self.update_lists)

        # fps combo
        self.fps_selector = QtWidgets.QComboBox(self)
        for i in ['24', '30', '60']:
            self.fps_selector.addItem(i)

        # reload button
        self.reload_button = QtWidgets.QPushButton("Reload", self)
        self.reload_button.clicked.connect(self.cb_reload)

        # rename as cleaning checkbox
        self.cleaning_combobox = QtWidgets.QCheckBox("Cleaning", self)

        self.topbar_layout = QtWidgets.QHBoxLayout(self)
        self.topbar_layout.addWidget(self.selector, 1)
        self.topbar_layout.addWidget(self.fps_selector, 0)
        self.topbar_layout.addWidget(self.reload_button, 0)
        self.topbar_layout.addWidget(self.cleaning_combobox, 0)
        self.topbar_layout.addSpacerItem(QtWidgets.QSpacerItem(0, 0))

        # task combo
        self.task_selector_combobox = QtWidgets.QComboBox(self)
        for i in ['raw', 'cleaning', 'solving']:
            self.task_selector_combobox.addItem(i)
        self.task_selector_combobox.currentIndexChanged.connect(self.task_change)

        # buttons
        self.load_button = QtWidgets.QPushButton("Load", self)
        self.load_button.clicked.connect(self.load_file)

        self.build_cleaning_button = QtWidgets.QPushButton("Build Cleaning", self)
        self.build_cleaning_button.clicked.connect(self.build_clean)

        self.load_template_button = QtWidgets.QPushButton("Import Latest Template(s)", self)
        self.load_template_button.clicked.connect(self.load_solve_template)

        self.build_solving_button = QtWidgets.QPushButton("Build Solving", self)
        self.build_solving_button.clicked.connect(self.build_solve)

        self.browse_button = QtWidgets.QPushButton("Browse", self)
        self.browse_button.clicked.connect(self.browse)

        # mid bar
        self.midbar_layout = QtWidgets.QHBoxLayout(self)
        self.midbar_layout.addWidget(self.task_selector_combobox, 0)

        self.midbar_layout.addWidget(self.load_button, 0)
        self.midbar_layout.addWidget(self.build_cleaning_button, 0)
        self.midbar_layout.addWidget(self.build_solving_button, 0)
        self.midbar_layout.addWidget(self.load_template_button, 0)
        self.midbar_layout.addWidget(self.browse_button, 0)
        self.midbar_layout.insertStretch(-1, 1)

        # Main Columns
        self.hsplitter = QtWidgets.QSplitter(self)
        # parent title click command dbl click command
        self.mocap_table = self.make_table(self.hsplitter, "Mocap", self.preview_mocap, self.load_mocap)
        self.character_list = self.make_col(self.hsplitter, "Character", self.preview_character, self.load_character)

        self.mocap_table.setHorizontalHeaderLabels(["Take", "C", "S", "Frms", "Rate", "In", "Out", "Subjects", "Notes"])
        self.mocap_table.cellChanged.connect(self.cell_change)

        self.hsplitter.setSizes([600, 200])

        # Lower section - buttons and Log Window
        self.log = QtWidgets.QTextEdit(self)
        self.log.setReadOnly(True)

        self.error_log = QtWidgets.QTextEdit(self)
        self.error_log.setReadOnly(True)

        log_layout = QtWidgets.QHBoxLayout(self)
        log_layout.addWidget(self.log)
        log_layout.addWidget(self.error_log)

        self.lower_widget = QtWidgets.QWidget(self)
        self.lower_layout = QtWidgets.QVBoxLayout(self)
        self.lower_layout.addLayout(self.midbar_layout)
        self.lower_layout.addLayout(log_layout)
        self.lower_widget.setLayout(self.lower_layout)

        # Options Menu
        menu_bar = QtWidgets.QMenuBar()
        menu = menu_bar.addMenu('Options')

        recent_menu = QtWidgets.QMenu("Recent")

        menu_items = [("Set Directory", self.set_dir_action),
                      ("Save Template", self.save_template),
                      ("Recent", None),
                      ("Set Rig Directory", self.set_rig),
                      ("Re-scan", self.populate_session_combobox),
                      ("Set Root Scale ", self.set_root_scale)]

        #
        for title, func in menu_items:

            if title is "Recent":
                op = "peelMocapLoaderRecent"
                if m_cmds.optionVar(exists=op):
                    menu.addMenu(recent_menu)
                    val = m_cmds.optionVar(q=op)
                    if not isinstance(val, list):
                        val = [val]
                    for i in val:
                        sub_action = QtWidgets.QAction(i, self)
                        sub_action.triggered.connect(partial(self.set_dir, i))
                        recent_menu.addAction(sub_action)
            else:
                action = QtWidgets.QAction(title, self)
                action.triggered.connect(func)
                menu.addAction(action)

        # Rig Menu
        self.rig_menu = menu_bar.addMenu('Rigs')

        # Main layout
        # Put the main columns and log in a splitter
        self.vsplitter = QtWidgets.QSplitter(self)
        self.vsplitter.setOrientation(QtCore.Qt.Vertical)
        self.vsplitter.addWidget(self.hsplitter)
        self.vsplitter.addWidget(self.lower_widget)
        self.vsplitter.setSizes([400, 100])

        # Draw the main layout
        main_layout.addLayout(self.topbar_layout, 0)
        main_layout.addWidget(self.vsplitter, 1)
        main_layout.addWidget(menu_bar)
        main_layout.setMenuBar(menu_bar)
        self.setLayout(main_layout)

        self.resize(1000, 500)

        # Populate
        self.task_change()
        self.populate_session_combobox()
        self.populate_rig_menu()

    def cb_reload(self):
        """ Calls the methods that: change the load button names based on the task; load the data;
         and populate the rig menu """
        self.task_change()
        self.populate_session_combobox()
        self.populate_rig_menu()

    def populate_rig_menu(self):
        """ If the variable 'peelRigDirectory' exists, adds its items to the rig menu, and sets up signal-slot
         connections for each of them. """

        base = os.path.split(__file__)[0]
        module_rigs = os.path.abspath(os.path.join(base, "..", "..", "..", "rig"))
        if os.path.isdir(module_rigs):
            for rig_name in os.listdir(module_rigs):
                rig_dir = os.path.join(module_rigs, rig_name)
                for rig_file in os.listdir(rig_dir):
                    action = QtWidgets.QAction(rig_file, self)
                    action.triggered.connect(partial(self.load_rig, rig_dir, rig_file))
                    self.rig_menu.addAction(action)

        if not m_cmds.optionVar(exists='peelRigDirectory'):
            return

        rig_dir = m_cmds.optionVar(q='peelRigDirectory')

        for i in os.listdir(rig_dir):
            print(i)
            action = QtWidgets.QAction(i, self)
            action.triggered.connect(partial(self.load_rig, rig_dir, i))
            self.rig_menu.addAction(action)

    def load_rig(self, rig_path, rig_file):
        """ Imports the rig file as a reference.
        :param rig_path: path of the folder that contains the rig file.
        :type rig_path: str
        :param rig_file: name of the rig file
        :type rig_file: str """
        rig_path = os.path.join(rig_path, rig_file)
        print("Importing: " + str(rig_path))
        ns, ret = QtWidgets.QInputDialog.getText(self, "Name", "Name:", QtWidgets.QLineEdit.Normal, "char1")
        if ret and ns:
            m_cmds.file(rig_path, i=True, preserveReferences=True, namespace=ns)
        else:
            m_cmds.file(rig_path, i=True, preserveReferences=True)

    def set_rig(self):
        """ Prompts the user to set the rig directory, and sets the 'peelRigDirectory' path. """

        ret = QtWidgets.QFileDialog.getExistingDirectory(self, "Rigs Directory")
        if ret is None or len(ret) == 0:
            return

        self.log.append("Setting rig to: " + ret)
        m_cmds.optionVar(stringValue=("peelRigDirectory", ret))
        self.populate_rig_menu()

    def cell_change(self, row, col):
        """ If any changes occur in the contents of the mocap table, this method is called. If the changes are in the
         "in", "out" or "notes" columns, it updates the json file.
          :param row: row index of the changed cell in the mocap table
          :type row: int
          :param col: row index of the changed cell in the mocap table
          :type col: int """

        if col not in [4, 5, 7]:
            return

        this_session = self.get_session()

        ranges = {}
        notes = {}

        for row in range(self.mocap_table.rowCount()):     # Why update all the rows? It's called for every cell change.
            # Get the Qt items

            name = self.mocap_table.item(row, 5).text()
            in_val = gui.int_item(self.mocap_table.item(row, 5))
            out_val = gui.int_item(self.mocap_table.item(row, 6))
            note = self.mocap_table.item(row, 8)

            if note is not None:
                note = note.text()

            print("in-val and out-val values on line 395:", in_val, out_val)

            if in_val is None or out_val is not None:
                ranges[name] = (in_val, out_val)
                #in_out.frame_range = (in_val, out_val)

            if note is not None:
                notes[name] = note

        self.write_json(this_session.title, "range-data.json", ranges)
        self.write_json(this_session.title, "notes-data.json", notes)

    def write_json(self, session, file_name, data):
        """ Stores the data in a json file under the given file name.
        File path pattern : BaseDirectory/SessionName/FileName
        :param session: Session name
        :type session: str
        :param file_name: Name of the json file that is to be written to
        :type file_name: str
        :param data: data to be written to file
        :type data: str """
        dat_file = os.path.join(self.parser.base_dir, session, file_name)
        print("dat_file")
        fp = open(dat_file, "w")  # Opens file to write. Creates the file if it does not exist. 'w':replace :: 'a':add
        if not fp:
            print("Could not write to file: ", dat_file)
            return

        print("Writing ranges to: ", dat_file)
        print("Data being written: ", data)
        json.dump(data, fp)
        fp.close()

    def task_change(self, x=None):  # can use *args or *kwargs or "_". But then you'd have to call with an argument.
        """ Change the load button text to reflect the current task selected in  the dropdown"""

        sel = self.task_selector_combobox.currentText()
        if sel == 'raw':
            self.load_button.setText("Open Raw")
        if sel == 'cleaning':
            self.load_button.setText("Load Cleaning")
        if sel == 'solving':
            self.load_button.setText("Load Solve")

    def set_dir_action(self, _):  # '_' means that the parameter will be received but not used.
        self.set_dir()

    def set_dir(self, value=None):
        """ Prompts the user to set the base directory, creates a new parser object. Adds path to the recent list.
        if value == None, asks user to locate the base directory. If located, creates parser object. Else, returns.
        if value != None, does value contain a valid folder path? If yes, creates parser object. Else, displays error
        :param value: Contains the path that is to be set as the directory.
        :type value: path """
        if value is None:
            ret = QtWidgets.QFileDialog.getExistingDirectory(self, "Base Directory")
            if ret is None or len(ret) == 0:
                return
        else:
            if not os.path.isdir(value):
                m_cmds.error("Cannot find directory: " + value)
            ret = value

        self.log.append("Setting directory to: " + ret)
        m_cmds.optionVar(stringValue=("peelLoaderDirectory", ret))
        self.parser = mocapData.Parser(ret)
        self.populate_session_combobox()

        # Add to recent
        op = "peelMocapLoaderRecent"
        if not m_cmds.optionVar(exists=op):  # if variable 'peelMocapLoaderRecent' doesn't already exist
            m_cmds.optionVar(
                stringValue=(op, ret))  # loads directory path into new variable called 'peelMocapLoaderRecent'
        else:
            recent = m_cmds.optionVar(q=op)
            if not isinstance(recent, list):  # if recent is not already of type 'list', makes it a list.
                recent = [recent]
            if ret not in recent:
                m_cmds.optionVar(stringValueAppend=(op, ret))  # adds the path to the recent list. Limits to newest 10.
                if m_cmds.optionVar(arraySize=op) > 10:
                    m_cmds.optionVar(removeFromArray=(op, 0))

    def browse(self):
        """ Finds the selected file in the local path, and opens it with a suitable application"""
        sel = self.get_selected()  # get_selected returns a list of selected mocap file items.
        if sel is None or len(sel) == 0:
            return

        # opens the first item in list:
        p, f = os.path.split(sel[0].path())
        print(sel[0].path().replace("/", r"\\"))
        print(p)
        print(f)

        import subprocess
        subprocess.Popen(r'explorer /select,' + sel[0].path().replace("/", "\\"))

        # QtWidgets.QDesktopServices.openUrl(QtCore.QUrl("file://" + p))  # when URL scheme is "file", opens the
        # file in suitable application instead of the web browser. Opens a pop-up window, allowing the user to select
        # the file from the specified folder.

    ######################
    # Create Gui bits

    def make_table(self, parent, title, click_command, double_click_command):
        """ Creates the left hand mocap table
        :param parent: the Qt element that is to hold the table widget.
        :type  parent: could be a splitter or any Qt object that can hold the table
        :param title: title of the mocap data table
        :type title: str
        :param click_command: the method that should be executed on single click
        :type click_command: method
        :param double_click_command: the method that should be executed on double click
        :type double_click_command:  method
        :return table_widget: Qt Table Widget holding the mocap data
        :rtype table_widget: QTableWidget"""

        widget = QtWidgets.QWidget(parent)
        table_widget = QtWidgets.QTableWidget(1, 9, widget)
        for i, wid in enumerate([200, 22, 22, 45, 45, 45, 45, 250, 250]):
            table_widget.setColumnWidth(i, wid)
        table_widget.setRowHeight(0, 22)
        table_widget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)  # setSelectionBehavior property
        # holds whether selections are done in terms of single items, rows or columns
        layout = QtWidgets.QVBoxLayout(widget)
        table_widget.itemDoubleClicked.connect(double_click_command)
        table_widget.itemClicked.connect(click_command)
        layout.addWidget(QtWidgets.QLabel(title, widget), 0)
        layout.addWidget(table_widget, 1)
        widget.setLayout(layout)
        parent.addWidget(widget)

        return table_widget

    def make_col(self, parent, title, click_command, double_click_command):
        """ Creates one of the main columns with a title and QListWidget.
        :param parent: the Qt element that is to hold the table widget.
        :type  parent: could be a splitter or any Qt object that can hold the table
        :param title: title of the mocap data table
        :type title: str
        :param click_command: the method that should be executed on single click
        :type click_command: method
        :param double_click_command: the method that should be executed on double click
        :type double_click_command:  method
        :return list_widget: a QListWidget object that contains a list of widgets, each of which
        """

        widget = QtWidgets.QWidget(parent)
        list_widget = QtWidgets.QListWidget(widget)
        layout = QtWidgets.QVBoxLayout(widget)
        list_widget.itemDoubleClicked.connect(double_click_command)
        list_widget.itemClicked.connect(click_command)
        layout.addWidget(QtWidgets.QLabel(title, widget))  # Adding label, parenting it to widget. Not sure how & why.
        layout.addWidget(list_widget)
        layout.setStretch(0, 0)
        layout.setStretch(1, 1)
        widget.setLayout(layout)
        parent.addWidget(widget)

        return list_widget

    ###################
    # Populate

    def populate_session_combobox(self):
        """ Gets data from the parser class, and populates the combobox """

        if self.parser is None:
            return

        self.log.append("Populating...")

        try:
            gui.wait(True)
            # get the data from the parser class
            self.parser.parse()
        finally:
            gui.wait(False)

        # clear and populate the session combo
        self.selector.blockSignals(True)

        sel = self.selector.currentText()
        self.selector.clear()

        for title, index in self.parser.getSessions():
            self.selector.addItem(title, index)  # add new entry(entries) to the selector combobox

        if sel:
            found = self.selector.findData(sel, QtCore.Qt.DisplayRole)
            if found >= 0:
                self.selector.setCurrentIndex(found)  # adding new entries to the combobox probably clears
                #  the current selection. So, set the current selection back to its earlier value.
        self.selector.blockSignals(False)

        # populate
        self.update_lists()

    def get_session(self):
        """ Returns the session info of the current selection in the session dropdown(combobox).
        :return session_obj : An object containing the session name and session id. If parser none, returns none.
        :rtype session_obj : session object or None"""
        if self.parser is None:
            return None
        return self.parser.get_session(title=self.selector.currentText())

    def update_lists(self, _=None):
        """ Updates the mocap table, reference list and character list, based on the selected session.
        Updates self.mocap_table, self.reference_list and self.character_list based on the current
        tasks - uses data from self.data.sessions[self.selector.currentIndex()] (mocapData.Session) """

        # clear current contents
        self.mocap_table.clearContents()
        self.mocap_table.setRowCount(0)
        # self.reference_list.clear()
        self.character_list.clear()

        if self.parser is None:
            return

        if len(self.parser.data.sessions) == 0:
            return

        # mocapData.Session object:
        this_session = self.get_session()

        try:
            gui.wait(True)
            self.parser.parseSession(this_session, True)

            # task dropdown
            task = self.task_selector_combobox.currentText()

            # populate the mocap table
            row = 0
            if 'raw' in this_session.tasks:  # what is 'raw'? unprocessed mocap data (c3d) file.
                sorted_items = sorted(this_session.tasks['raw'], key=lambda v: v.get_name())
                for item in sorted_items:
                    # each mocapData.C3DFile
                    self.add_row(row, item)
                    row += 1

            if 'template' in this_session.tasks:
                sorted_list = sorted(this_session.tasks['template'], key=lambda v: v.get_name())
                for char_item in sorted_list:
                    qt_item = QtWidgets.QListWidgetItem(char_item.get_name())
                    qt_item.setData(QtCore.Qt.UserRole, char_item)
                    self.character_list.addItem(qt_item)

        finally:
            gui.wait(False)

    def add_row(self, row_number, item):
        """ Adds a single row to the mocap table.
         :param row_number: Index number of the row to be added in the mocap table.
         :type row_number: int
        :param item: C3DFile object, containing data pertaining to the c3d file.
        :type item: object of class C3DFile """

        rate = item.data_rate()
        rate_scale = float(self.fps_selector.currentText()) / rate

        self.mocap_table.blockSignals(True)  # don't emit a frame range change event to cause a save

        try:
            self.mocap_table.insertRow(row_number)
            self.mocap_table.setRowHeight(row_number, 20)

            # column 0 : title
            title = gui.table_item(item.get_name(), item)
            self.mocap_table.setItem(row_number, 0, title)

            # column 1: cleaning
            mb = mocapData.MayaFile.FromC3d(item, task='cleaning')
            if mb.exists():
                self.mocap_table.setItem(row_number, 1, gui.table_item(str(mb.get_version())))

            # column 2: solving
            mb = mocapData.MayaFile.FromC3d(item, task='solving')
            if mb.exists():
                self.mocap_table.setItem(row_number, 2, gui.table_item(str(mb.get_version())))

            # column 3: number of frames in range
            start, end = item.range()
            if start is not None and end is not None:
                length = (end - start) * rate_scale
                self.mocap_table.setItem(row_number, 3, gui.table_item(str(length)))
            else:
                self.mocap_table.setItem(row_number, 3, gui.table_item('Error'))

            # column 4: data rate
            self.mocap_table.setItem(row_number, 4, gui.table_item(str(rate)))

            # columns 5, 6: in-frame, out-frame
            if item.frame_range is not None:
                in_frame, out_frame = item.frame_range
                if in_frame is not None:
                    in_val = int(math.floor(in_frame * rate_scale))
                    self.mocap_table.setItem(row_number, 5, gui.table_item(str(in_val), edit=True))
                if out_frame is not None:
                    out_val = int(math.ceil(out_frame * rate_scale))
                    self.mocap_table.setItem(row_number, 6, gui.table_item(str(out_val), edit=True))
            else:
                print("No range for:" + item.get_name())

            # column 7: subjects
            if 'SUBJECTS' in item.c3d_file.data:
                subjects = item.c3d_file.data['SUBJECTS']
                if 'LABEL_PREFIXES' in subjects:
                    prefixes = [word.rstrip() for word in subjects['LABEL_PREFIXES']]
                    self.mocap_table.setItem(row_number, 7, gui.table_item(','.join(prefixes)))

            # column 8: notes
            if item.note:
                self.mocap_table.setItem(row_number, 8, gui.table_item(str(item.note)))

        finally:
            self.mocap_table.blockSignals(False)

    ###############
    #  GET

    def get_selected_character(self):
        """ Returns the selected character.
        :return item.data(QtCore.Qt.UserRole): Returns the ..?
        :rtype: mocapData.Character object """

        item = self.character_list.currentItem()
        if item is None:
            return None
        return item.data(QtCore.Qt.UserRole)

    def get_selected_mocap(self):

        return_list = []

        for row_index in self.mocap_table.selectionModel().selectedRows():
            item = row_index.data(QtCore.Qt.UserRole)
            row = row_index.row()
            in_val = gui.int_item(self.mocap_table.item(row, 5), None)
            out_val = gui.int_item(self.mocap_table.item(row, 6), None)
            return_list.append((item, in_val, out_val))

        return return_list

    def get_selected(self):
        """ Returns a list of data items for the selected rows in the mocap list.
        :return return_list: list of selected rows
        :rtype return_list: list """

        return_list = []
        sel = self.mocap_table.selectionModel().selectedRows()

        if len(sel) > 0:
            # a mocap item is selected
            for rowIndex in sel:
                item = rowIndex.data(QtCore.Qt.UserRole)
                return_list.append(item)
            return return_list

        sel = self.character_list.selectionModel().selectedRows()
        if len(sel) > 0:
            # a template is selected
            for rowIndex in sel:
                item = rowIndex.data(QtCore.Qt.UserRole)
                return_list.append(item)
            return return_list

    def preview_mocap(self, x=None):
        """  Prints  the paths to the C3D file and the cleaning file (if it exists). """
        self.task_change()
        self.character_list.clearSelection()
        # item = x.data(QtCore.Qt.UserRole)            # maybe if needed in the future
        for item in self.get_selected():
            cleaning = mocapData.MayaFile.FromC3d(item, 'cleaning', None)
            print("C3D:      " + item.path())
            print("Cleaning: " + cleaning.path() + " Exists: " + str(cleaning.exists()))

    def preview_character(self, x=None):
        self.mocap_table.clearSelection()
        self.load_button.setText("Load Template")

    def load_character(self, x=None):
        """ Imports the character file"""

        item = self.get_selected_character()
        self.load_template(item)

    ###################
    # File Actions

    def load_file(self):
        """ Called when the user presses the load button. It opens the file corresponding to the selected item. """

        sel = self.get_selected()
        if sel is None or len(sel) == 0:
            return

        for item in sel:
            if item.data_type() == "maya":
                # open the template
                actions.fileAction(item, "open")
                return

        this_task = self.task_selector_combobox.currentText()
        if this_task == 'raw':
            actions.fileAction(sel[0], "open")
        else:
            mb = mocapData.MayaFile.FromC3d(sel[0], task=this_task)
            actions.fileAction(mb, "open")

    def build_clean_item(self, item):
        """ Builds the cleaning, using the run method in buildCleaning.py
        Then, calls the fileAction method from actions.py to save the file.
        :param item: C3DFile object, containing data pertaining to the c3d file.
        :type item: object of class C3DFile
        :return mb: cleaned file returned from the MayaFile class in mocapData.py
        :rtype mb: maya binary file """

        if not item.exists():
            raise RuntimeError("File does not exist: " + item.path())

        if item.data_type() != 'c3d':
            raise RuntimeError("Not a c3d file: " + item.path())

        self.log.append("Building cleaning: " + str(item.get_name()))

        # load the c3d
        m_cmds.file(force=True, new=True)
        if not actions.fileAction(item, mode='import'):
            return None

        # run the build steps
        buildCleaning.run()

        self.set_range(item)

        mb = mocapData.MayaFile.FromC3d(item, 'cleaning', True)
        if actions.fileAction(mb, mode="save"):
            return mb

        self.log.append("Error saving cleaning scene: " + str(item.get_name()))
        return None

    def build_clean(self):
        """ Al's note: callback for 'build cleaning' button
        Builds the clean for the selected item. """

        if not gui.changes():
            return

        items = self.get_selected()

        if items is None:
            m_cmds.error("Nothing selected")
            return

        for sel in items:
            self.build_clean_item(sel)

        self.update_lists()

    def set_range(self, item):
        """
        Sets the min and max values in the playback setting, based on the start and end frame numbers the
        user has set in the table
        :param item: C3DFile object, containing data pertaining to the c3d file.
        :type item: object of class C3DFile"""

        print("Setting frame range")

        if item.frame_range is not None:
            start_frame, end_frame = item.frame_range

            print(start_frame, end_frame)

            if start_frame is not None:
                try:
                    int_value = int(start_frame)
                    self.log.append("Setting start to : " + str(int_value))
                    m_cmds.playbackOptions(min=int_value)
                except ValueError:
                    self.error_log.append("Invalid start: " + str(start_frame))

            if end_frame is not None:
                try:
                    int_value = int(end_frame)
                    self.log.append("Setting end to : " + str(int_value))
                    m_cmds.playbackOptions(max=int_value)
                except ValueError:
                    self.error_log.append("Invalid end: " + str(end_frame))
        else:
            self.error_log.append("No range for : " + item.name)

    def build_solve(self):
        """
        Checks for gui changes. If yes, for each selected item in the mocap table:
          - checks if the cleaning file already exists. If yes, opens it.
            Else, uses build_clean_item method to create one.
          - Next, loads the solve template, sets the framerate based on user selection,
            sets the markers to square, runs the solve, saves the file, and displays the
            destination to the user.
          - Finally, calls the update_lists method to update the data displayed to the
            user in the Loader window.
        """

        # check for scene changes and prompt
        if not gui.changes():
            return

        # get select table item
        sel = self.get_selected_mocap()
        if sel is None:
            return

        # for each item selected in the take list
        for item, in_val, out_val in sel:
            self.log.append("Building solve: " + str(item) + " " + str(in_val) + " " + str(out_val))
            print("=" * 100)
            print("Building solve: " + str(item) + " " + str(in_val) + " " + str(out_val))

            m_cmds.file(force=True, new=True)  # Force action to take place : new file

            # check to see if a cleaning file exists - we will load the template in to that
            clean_item = mocapData.MayaFile.FromC3d(item, 'cleaning', None)
            if not clean_item.exists():
                # create a cleaning file as there isn't one
                clean_item = self.build_clean_item(item)
                if clean_item is None:
                    self.error_log.append("Could not process: " + item.get_name())
                    continue
            else:
                # open the existing cleaning file
                if not actions.fileAction(clean_item, "open"):
                    self.error_log.append("Could not open file: " + item.get_name())
                    continue

            # new solve file object
            solve_item = mocapData.MayaFile.FromC3d(item, 'solving', True)  # c3d=item, task='solving, version=None.

            # load the solve template
            # solve template should be solved but have no animation. will have one frame (eg: t-pose).
            print("loading the solve template")
            if not self.load_solve_template():
                self.error_log.append("No solve templates for trial: " + item.get_name())
                self.error_log.append("the templates should saved in a 'template' directory for the session")
                for prefix in markerset.prefixes():
                    self.error_log.append("e.g. : " + os.path.join(self.parser.base_dir, "templates", prefix + "001.ma"))

                continue

            if self.fps_selector.currentText() == '24':
                self.log.append("Setting rate to 24fps")
                m_cmds.currentUnit(time='film')

            elif self.fps_selector.currentText() == '30':
                self.log.append("Setting rate to 30fps")
                m_cmds.currentUnit(time='ntsc')

            elif self.fps_selector.currentText() == '60':
                self.log.append("Setting rate to 60fps")
                m_cmds.currentUnit(time='ntscf')

            # Set frame in/out
            if in_val is not None:
                m_cmds.playbackOptions(min=int(in_val))

            if out_val is not None:
                m_cmds.playbackOptions(max=int(out_val))

            # set the markers to being square
            buildSolving.setSquare()

            self.log.append("Solving")
            print("Solving")
            # run solve
            buildSolving.runSolve()

            self.log.append("Saving as: " + solve_item.path())
            base, name = os.path.split(solve_item.path())
            if not os.path.isdir(base):
                os.mkdir(base)  # creates a directory at 'base' path.
            m_cmds.file(rename=solve_item.path())
            m_cmds.file(save=True)

        self.update_lists()

    def load_mocap(self, x=None, mode='import'):
        """ called by user double clicking on an item in the mocap column.  The item that
        is loaded is determined by the current task field.  
        * see mocapData.Session.tasks[ taskName ] -> [ mocapData.C3DFile, ... ]
        * mocapData.C3DFile is subclass of mocapData.File
        Add support for additional file types here."""

        if x.column() != 0:
            return
        item = x.data(QtCore.Qt.UserRole)
        actions.fileAction(item, mode)

    def save_template(self):
        session = self.get_session()
        session_path = os.path.join(self.parser.base_dir, session.title)
        prefixes = list(markerset.prefixes())
        if len(prefixes) == 0 :
            self.error_log.append("Could not find marker prefix")
            return
        if len(prefixes) != 1:
            self.error_log.append("More than one prefix")
            return

        if not m_cmds.objExists("peelSolveOptions"):
            self.error_log.append("Could not find a solve setup")
            return

        prefix = prefixes[0].strip("_")
        mf = mocapData.MayaFile(session_path, "template", prefix, True)

        m_cmds.select(roots.ls())
        m_cmds.select("peelSolveOptions", add=True)
        m_cmds.file(mf.path(), es=True, typ="mayaBinary")
        self.update_lists()

    def load_solve_template(self):
        """ Using the marker prefix in the scene, loads the latest solve template
        via session.task['template']
        :return bool: True if successful. False if no prefixes or templates are found for the markerset.
        :rtype bool: boolean"""

        # Session is mocapData.session object
        session = self.get_session()
        session_path = os.path.join(self.parser.base_dir, session.title)
        prefixes = list(markerset.prefixes())

        if prefixes is None or len(prefixes) == 0:
            m_cmds.warning("No prefixes found for markerset " + str(session))
            return False

        prefix = prefixes[0].strip("_")
        mf = mocapData.MayaFile(session_path, "template", prefix, None)

        if not mf.exists():
            self.log.append("No matching solve templates were found for prefix:")
            self.log.append("   " + ', '.join(prefixes))
            return

        print("Loading template: " + str(mf.path()))
        m_cmds.file(mf.path(), i=True, prompt=False)

        # connect the markers
        self.log.append("Connecting Markers")
        buildSolving.connect()

        # set the scale on the optical root
        for prefix in prefixes:
            print("Prefix: " + str(prefix))
            err = buildSolving.apply_scale(prefix)
            for i in err:
                self.error_log.append(i)

        roots.consolidate_roots()

        return True

    def load_template(self, file_item):
        """ Imports the file, and connects the peelTargets to their sources. In case of error, appends to the log.
        Consolidates roots after loading the template.
        :param file_item: the file that contains the character to be solved. ?? Not sure.
        :type file_item: mocapData.Character object"""

        m_cmds.file(file_item.path(), i=True, prompt=False)       # import file
        buildSolving.connect()

        for prefix in markerset.prefixes():
            err = buildSolving.apply_scale(prefix)
            for i in err:
                self.error_log.append(i)

        roots.consolidate_roots()

    def set_root_scale(self):
        """Finds the roots in the scene (as set up by the user), and adds a scale attribute to each of them"""
        ''' Menu callback '''

        for root in roots.ls():

            attr = root + ".mocapScale"
            val = m_cmds.getAttr(attr) if m_cmds.objExists(attr) else 1.0
            ret = m_cmds.promptDialog(m="Scale for: " + str(root), text=str(val))
            if ret != 'Confirm':
                print(ret)
                continue

            text = m_cmds.promptDialog(q=True, text=True)
            try:
                float_value = float(text)
            except ValueError:
                m_cmds.warning("Invalid Value: " + str(text))
                continue

            print("Setting scale attribute on: ", attr, "to", str(float_value))
            if not m_cmds.objExists(attr):
                m_cmds.addAttr(root, sn='ms', ln='mocapScale', at='float')
                m_cmds.setAttr(attr, keyable=True)
            m_cmds.setAttr(attr, float_value)


