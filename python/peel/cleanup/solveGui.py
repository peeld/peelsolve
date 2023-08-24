from PySide2 import QtWidgets, QtCore, QtGui
from peel.cleanup import solve, markerset, gui


INSTANCE = None

def show(force=False):
    ''' Show the tool gui (uses INSTANCE global var) '''

    global INSTANCE

    if force and INSTANCE:
        INSTANCE.close()
        INSTANCE = None

    if not INSTANCE:
        INSTANCE = Gui()

    INSTANCE.show()
    INSTANCE.raise_()
    INSTANCE.activateWindow()


class Gui(QtWidgets.QDialog):
    ''' Gui for labelling markers '''

    def __init__(self):
        parent = gui.mainWindow()
        super(Gui, self).__init__(parent)

        self.data = None

        self.setWindowTitle('Solve Tool')

        self.mainLayout = QtGui.QVBoxLayout()

        # topbar

        self.topbar = QtGui.QFormLayout()

        # marker prefix
        self.marker_prefix_combo = QtGui.QComboBox()
        self.marker_prefix_combo.addItems( ['--none--'] +  list(markerset.prefixes()) )
        self.marker_prefix_combo.currentIndexChanged.connect(self.populate)
        self.topbar.add_row("Marker Prefix: ", self.marker_prefix_combo)

        # root prefix
        self.root_combo = QtGui.QComboBox()
        self.root_combo.addItems( solve.roots() )
        self.root_combo.currentIndexChanged.connect(self.populate)
        self.topbar.add_row("Root: ", self.root_combo)

        self.mainLayout.addItem(self.topbar)

        # tree
        self.tree = QtGui.QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(['Source',
                                   'Parent',
                                   'Tr',
                                   'Ro'])
        self.tree.setColumnWidth(0, 150)
        self.tree.setColumnWidth(1, 150)
        self.tree.setColumnWidth(2, 40)
        self.tree.setColumnWidth(3, 40)
        self.mainLayout.addWidget(self.tree)

        ############
        # Low Bar
        self.lowbar = QtGui.QHBoxLayout()

        # load
        self.loadButton = QtGui.QPushButton("Load")
        self.loadButton.pressed.connect(self.load)
        self.lowbar.addWidget(self.loadButton,0)

        # save
        self.saveButton = QtGui.QPushButton("Save")
        self.saveButton.pressed.connect(self.save)
        self.lowbar.addWidget(self.saveButton,0)

        # connect
        self.connectButton = QtGui.QPushButton("Connect")
        self.connectButton.pressed.connect(self.connect_markers)
        self.lowbar.addWidget(self.connectButton,0)


        self.lowbar.addStretch(1)

        self.mainLayout.addItem(self.lowbar)

        self.setLayout(self.mainLayout)

        self.resize(450,600)

        self.populate()

    def load(self):
        self.data = solve.load()
        self.populate()


    def save(self):
        if self.data is not None:
            solve.save(template_data=self.data)

    def connect_markers(self):
        if self.data is not None:
            solve.connect_data(self.data)


    def populate(self):

        self.tree.clear()

        root = self.root_combo.currentText()
        ns = None

        if root is not None:
            if '|' in root :
                root = root[ root.rfind('|')+1 : ]

            if ':' in root :
                ns = root [ : root.find(':')+1 ]

        print(root, ns)

        prefix=None
        if self.marker_prefix_combo.currentIndex() > 0 :
            prefix = self.marker_prefix_combo.currentText()

        if root is not None:

            self.data = solve.data(root, strip_marker=prefix, strip_joint=ns)

            if 'active' in self.data :
                for active in self.data['active'] :

                    tWeight = active['tWeight']
                    rWeight = active['rWeight']
                    parent  = active['parent']
                    source  = active['source']

                    row = [source, parent, str(tWeight), str(rWeight) ]

                    item = QtGui.QTreeWidgetItem(row)
                    self.tree.addTopLevelItem(item)


