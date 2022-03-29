# Mocap Cleanup - Alastair Macleod 2016
# GPL License = http://www.gnu.org/licenses/gpl.txt 

from peel.cleanup import markerset, keyTools, assign, datarate, gui, localsettings
from peel.util import curve
from peel.cleanup.Qt import QtWidgets, QtCore, QtGui
import maya.cmds as m
from functools import partial
import os.path

""" Labeler tool to select and assign markers.  Uses PySide.QtWidgets/QtCore """

INSTANCE = None

SQUARE = 1
CROSS = 2
CIRCLECROSS = 3
CIRCLE = 4

options = [(SQUARE, 'Square'), (CROSS, 'Cross'), (CIRCLECROSS, 'Circle/Cross'), (CIRCLE, 'Circle')]


def startTool():
    if INSTANCE is None: return
    INSTANCE.toolActive = True
    m.select(cl=True)


def selectEvent():
    # user has selected something in assign mode
    # if they have one thing selected in the scene and in the ui, do an assignment
    if INSTANCE is None: return
    INSTANCE.toolActive = False

    src = m.ls(sl=True)
    if src is None or len(src) != 1: return
    dst = INSTANCE.getSelected()
    if dst is None or len(dst) != 1: return

    INSTANCE.doAssign(src[0], dst[0])
    INSTANCE.moveOn(dst[0])


def show(force=False):
    """ Show the tool gui (uses INSTANCE global var) """

    global INSTANCE

    if force and INSTANCE:
        INSTANCE.close()
        INSTANCE = None

    if not INSTANCE:
        INSTANCE = Gui()

    INSTANCE.show()
    INSTANCE.raise_()
    INSTANCE.activateWindow()

    return INSTANCE


def onetwo():
    global INSTANCE
    if not INSTANCE: return
    INSTANCE.onetwo()


def query():
    global INSTANCE
    if not INSTANCE: return
    INSTANCE.query()


def colorButton(color, callBack):
    c = QtWidgets.QToolButton()
    pm = QtGui.QPixmap(32, 32)
    rgb = m.colorIndex(color, q=True)
    pm.fill(QtGui.QColor(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)))
    c.setIcon(QtGui.QIcon(pm))
    c.pressed.connect(callBack)
    c.setMinimumSize(QtCore.QSize(16, 16))
    c.setStyleSheet("margin: 0px")
    return c


class Gui(QtWidgets.QDialog):
    """ Gui for labelling markers """

    def __init__(self):

        parent = gui.mainWindow()

        # stay on top added for maya2014 osx
        super(Gui, self).__init__(parent, QtCore.Qt.WindowStaysOnTopHint)

        self.toolActive = False

        # self.setWindowFlags( self.windowFlags() )

        # self.setWindowFlags(QtCore.Qt.Window)

        self.setWindowTitle('Markerset Tool')
        self.resize(500, 600)

        self.markers = None
        self.markerset = None
        self.prefix = None
        self.customSets = {}

        self.mainlayout = QtWidgets.QVBoxLayout()
        self.hlayout = QtWidgets.QHBoxLayout()
        self.menuBar = QtWidgets.QMenuBar()
        self.toolbar = QtWidgets.QToolBar()
        self.setStyleSheet(
            "QToolButton {  background-color: #222; padding: 3px; margin: 3px; border: 1px solid gray; } ");

        self.mainlayout.setMenuBar(self.menuBar)

        # markerset combo

        self.formLayout = QtWidgets.QFormLayout()
        self.markersetSelector = QtWidgets.QComboBox(self)
        self.markersetSelector.currentIndexChanged.connect(self.markersetSelect)
        self.formLayout.addRow("Markerset", self.markersetSelector)

        # markerset prefix table
        self.prefixSelector = QtWidgets.QTableWidget(self)
        self.prefixSelector.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection);
        self.prefixSelector.itemChanged.connect(self.prefixItemChange)
        self.prefixSelector.currentCellChanged.connect(self.prefixSelected)
        self.prefixSelector.setColumnCount(2)
        self.prefixSelector.setColumnWidth(0, 200)
        self.prefixSelector.setColumnWidth(1, 30)
        self.prefixSelector.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.formLayout.addRow(self.prefixSelector)

        # display mode combo
        self.displaySelector = QtWidgets.QComboBox(self)
        self.displaySelector.currentIndexChanged.connect(self.setDisplayMode)
        self.displaySelector.addItems(['--select--', 'square', 'circle', 'cross', 'circle/cross'])
        self.formLayout.addRow("Display Markers", self.displaySelector)

        # display mode-selected
        self.displaySelector2 = QtWidgets.QComboBox(self)
        self.displaySelector2.currentIndexChanged.connect(self.setSelectedMode)
        self.displaySelector2.addItems(['--select--', 'square', 'circle', 'cross', 'circle/cross'])
        self.formLayout.addRow("Display Selected", self.displaySelector2)

        # source range mode
        self.sourceRangeSelector = QtWidgets.QComboBox(self)
        self.sourceRangeSelector.addItems(['gap', 'fill', 'segment', 'spike', 'all', 'selected'])
        self.formLayout.addRow("Source Range", self.sourceRangeSelector)

        # replace mode 
        self.replaceModeSelector = QtWidgets.QComboBox(self)
        self.replaceModeSelector.addItems(['extract', 'swap', 'overwrite'])
        self.formLayout.addRow("Replace Mode", self.replaceModeSelector)

        # buttons
        buttonLayout = QtWidgets.QHBoxLayout()

        refreshButton = QtWidgets.QToolButton(self)
        refreshButton.setText("Refresh")
        refreshButton.clicked.connect(self.markersetSelect)

        oneTwoButton = QtWidgets.QToolButton(self)
        oneTwoButton.setText("1->2")
        oneTwoButton.clicked.connect(self.onetwo)

        queryButton = QtWidgets.QToolButton(self)
        queryButton.setText("?")
        queryButton.clicked.connect(self.query)
        queryButton.setToolTip("select affected keys")

        highlightButton = QtWidgets.QToolButton(self)
        highlightButton.setText("^")
        highlightButton.clicked.connect(self.highlight)
        highlightButton.setToolTip("Highlight selected")

        toolButton = QtWidgets.QToolButton(self)
        toolButton.setText("*")
        toolButton.clicked.connect(self.tool)
        toolButton.setToolTip("Assignment Tool")

        buttonLayout.addWidget(refreshButton)
        buttonLayout.addWidget(oneTwoButton)
        buttonLayout.addWidget(queryButton)
        buttonLayout.addWidget(highlightButton)
        buttonLayout.addWidget(toolButton)
        # buttonWidget  = QtWidgets.QWidget()
        # buttonWidget.setLayout(buttonLayout)

        self.formLayout.addRow(buttonLayout)

        # colors
        self.colorWidget = QtWidgets.QWidget(self)
        self.colorLayout = QtWidgets.QHBoxLayout(self.colorWidget)
        for c in [14, 15, 22, 27, 28, 29, 30, 31]:
            self.colorLayout.addWidget(colorButton(c, partial(self.cb_color, c)))
        self.colorWidget.setLayout(self.colorLayout)
        self.formLayout.addRow(self.colorWidget)

        # progress
        self.progressBar = QtWidgets.QProgressBar(self)
        self.progressBar.setVisible(False)
        self.formLayout.addRow(self.progressBar)

        self.progressLabel = QtWidgets.QLabel(self)
        self.progressLabel.setVisible(False)
        self.formLayout.addWidget(self.progressLabel)
        self.progressLabel.setSizePolicy(
            QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))

        # marker select list
        self.markerList = QtWidgets.QTableWidget(1, 4, self)
        self.markerList.itemClicked.connect(self.cb_select)
        self.markerList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        # marker assign list
        # self.assignList = QtWidgets.QListWidget(self)
        # self.assignList.itemClicked.connect( self.cb_change )

        # markerset menu
        markersetMenu = QtWidgets.QMenu("Markerset", parent=self)
        self.menuBar.addMenu(markersetMenu)

        for text, func in [
            ('Load', self.cb_load),
            ('Save', self.cb_save),
            ('From Selection', self.cb_fromSelection),
            ('Set Markerset Directory', self.cb_setMarkersetDir),
            ('Refesh', self.loadMarkersets),
            ('Save Markerset', self.cb_save)
        ]:
            action = QtWidgets.QAction(text, self)
            action.triggered.connect(func)
            markersetMenu.addAction(action)

        # marker menu
        markerMenu = QtWidgets.QMenu("Markers", parent=self)
        self.menuBar.addMenu(markerMenu)

        for text, func in [
            ('Draw Line', self.cb_drawLine),
            ('Clear Lines', self.cb_clearMarkerLines),
            ('Select Empty', self.cb_selectEmpty),
            ('Select Unlabelled', self.cb_selectUnlabelled),
            ('Set Data Rate', self.cb_setDataRate),
        ]:
            action = QtWidgets.QAction(text, self)
            action.triggered.connect(func)
            markerMenu.addAction(action)

        # toolbar

        for text, func in [
            ('sel', self.cb_selectMarkers),
            ('sel-all', self.cb_selectAll),
            ('lines', self.cb_drawLines),
            ('active', self.cb_setActive),
            ('display', self.cb_display),
        ]:
            action = QtWidgets.QAction(text, self)
            action.triggered.connect(func)
            self.toolbar.addAction(action)

        # layout
        self.hlayout.addWidget(self.markerList, 1)
        self.hlayout.addLayout(self.formLayout, 0)

        self.mainlayout.addWidget(self.toolbar, 0)
        self.mainlayout.addLayout(self.hlayout, 1)

        # self.mainWidget = QtGui.QWidget()
        # self.mainWidget.setLayout( self.mainlayout )
        # self.setCentralWidget(self.mainWidget)

        self.setLayout(self.mainlayout)
        # self.setWindowFlags( self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint )
        # self.setWindowFlags( self.windowFlags() & ~QtCore.Qt.WindowStaysOnBottomHint )

        self.loadMarkersets()

        # guess the markerset by finding the set with the most matching markers

        results = []
        for i, setName in enumerate(markerset.markersets.keys()):
            mset = markerset.markersets[setName]
            for prefix in mset.prefixes():
                found, missing = mset.test(prefix)
                results.append((i, prefix, len(found)))

        if len(results) > 0:
            maxval = max(results, key=lambda v: v[2])[0]
            self.markersetSelector.setCurrentIndex(maxval + 1)

        self.markersetSelect()

        startCommand = "import " + localsettings.module + ".labeler as l;l.startTool()"
        finishCommand = "import " + localsettings.module + ".labeler as l;l.selectEvent()"
        self.context = m.scriptCtx(t='test', ts='python("' + startCommand + '")',
                                   tf='python("' + finishCommand + '")', tct='dot', lc=True, tss=1)

        # self.scriptJob = m_cmds.scriptJob( e = [ "timeChanged", self.draw ] )
        # self.destroyed.connect( lambda : m_cmds.scriptJob( k = self.scriptJob ) )

    def tool(self):
        m.setToolTo(self.context)

    def scriptJob(self):
        pass

    def cb_setDataRate(self):
        datarate.setRateInput()

    def progressRange(self, maxval):
        self.progressBar.setMaximum(maxval)

    def progressValue(self, value, text=None):
        x = value < self.progressBar.maximum() - 1
        self.progressBar.setVisible(x)
        self.progressLabel.setVisible(text is not None and x)
        self.progressBar.setValue(value)
        if text is not None:
            self.progressLabel.setText(text)

    def getMode(self, value):
        if value == 1: return 1
        if value == 2: return 4
        if value == 3: return 2
        if value == 4: return 3
        return None

    def setSelectedMode(self, value):

        mode = self.getMode(value)
        if mode is None: return

        for i in m.ls(sl=True, l=True):
            if m.nodeType(i) == "peelSquareLocator":
                m.setAttr(i + ".displayMode", mode)
            elif m.nodeType(i) == "transform":
                cld = m.listRelatives(i, type="peelSquareLocator", fullPath=True)
                if cld is not None and len(cld) > 0:
                    m.setAttr(cld[0] + ".displayMode", mode)

    def setDisplayMode(self, value):
        if self.markerset is None: return
        prefix = self.currentPrefix()
        mode = self.getMode(value)
        if mode is not None: self.markerset.setDisplayMode(prefix, mode)

    def currentPrefix(self):

        row = self.prefixSelector.currentRow()
        if row == -1: return None
        item = self.prefixSelector.item(row, 0)
        if item is None: return None
        return item.data(QtCore.Qt.DisplayRole)

    def updatePrefixes(self):

        """ update the prefix table with names and display checkboxes """

        currentPrefix = self.currentPrefix()

        self.prefixSelector.clear()

        if self.markerset is None:
            return

        prefixes = self.markerset.prefixes()
        self.prefixSelector.blockSignals(True)
        self.prefixSelector.setRowCount(len(prefixes))

        self.prefixSelector.setHorizontalHeaderLabels(["Prefix", "vis"])

        index = None
        for i, prefix in enumerate(prefixes):

            self.prefixSelector.setRowHeight(i, 24)

            self.prefixSelector.setItem(i, 0, QtWidgets.QTableWidgetItem(prefix))

            cb1 = QtWidgets.QTableWidgetItem()
            cb1.setCheckState(QtCore.Qt.Unchecked)

            d = set()
            for mkr in self.markerset.markers(prefix):
                scene_marker = m.ls(mkr, type='transform', l=True)
                if scene_marker is None or len(scene_marker) == 0:
                    continue

                if len(scene_marker) > 1:
                    m.warning("More than one marker named: " + mkr + ", using: " + scene_marker[0])

                val = m.getAttr(scene_marker[0] + ".v")
                d.add(val)

            if len(d) == 1:
                if list(d)[0]:
                    cb1.setCheckState(QtCore.Qt.Checked)
                else:
                    cb1.setCheckState(QtCore.Qt.Unchecked)
            else:
                cb1.setCheckState(QtCore.Qt.PartiallyChecked)

            self.prefixSelector.setItem(i, 1, cb1)

            if prefix == currentPrefix: index = i

        if index is not None:
            self.prefixSelector.setCurrentCell(index, 0)

        self.prefixSelector.blockSignals(False)

        self.prefixSelected()

    def prefixSelected(self):

        """ The prefix has changed.
            Called by a table click event or by the markerset combo changed. """

        self.prefix = self.currentPrefix()
        self.draw()

    def prefixItemChange(self, item):

        prefix = self.prefixSelector.item(item.row(), 0).data(QtCore.Qt.DisplayRole)

        state = item.checkState() is QtCore.Qt.Checked

        if item.column() == 1:
            # visibility

            for i in self.markerset.markers(prefix):
                try:
                    keyTools.toggle_connect_vis([i], force=False)
                    m.setAttr(i + ".v", state)
                    con = m.listConnections(i + ".t", s=False, d=True, sh=True)
                    if con is not None:
                        for i in con:
                            m.setAttr(i + ".v", state)
                except RuntimeError as e:
                    m.warning(str(i) + "  " + str(e))

    def markersetSelect(self, x=None):

        """ user has chosen a markerset - populate the prefix selector and call prefixSelected() """

        self.markerset = None
        sel = self.markersetSelector.currentText()
        if len(sel) > 0 and sel != '--select--':

            if sel in self.customSets:
                self.markerset = self.customSets[sel]
            elif sel in markerset.markersets:
                self.markerset = markerset.markersets[sel]
            else:
                m.warning("Could not determine markerset: " + str(sel))

        # clear the markers table
        self.markerList.clearContents()
        self.markerList.setRowCount(0)

        # update the prefix list
        self.updatePrefixes()

    def highlight(self):
        self.markerList.clearSelection()
        sel = m.ls(sl=True)
        for r in range(self.markerList.rowCount()):
            item = self.markerList.item(r, 0)
            marker = item.data(QtCore.Qt.UserRole)
            if marker in sel:
                item.setSelected(True)

    def moveOn(self, ref):

        # move to the next inactive marker in the list

        print("---" + str(ref))

        flag = False
        for r in range(self.markerList.rowCount()):
            item = self.markerList.item(r, 0)
            marker = item.data(QtCore.Qt.UserRole)
            if flag:
                if m.getAttr(marker + ".active") == 0:
                    self.markerList.selectRow(r)
                    return
            elif marker == ref:
                flag = True

        self.markerList.clearSelection()

    def draw(self, refresh=False):

        """ populate self.markerList and assignList (QListWidet) """

        sel = [i.text() for i in self.markerList.selectedItems()]

        self.markerList.clearContents()
        self.markerList.setRowCount(0)

        if self.markerset is None or len(self.markerset.markers()) == 0: return

        for i, marker in enumerate(self.markerset.markers()):
            pmarker = marker if self.prefix is None else self.prefix + marker
            exists = m.objExists(pmarker) and m.nodeType(pmarker) == 'transform'
            active = False
            if exists:
                if m.objExists(pmarker + ".active"):
                    active = m.getAttr(pmarker + ".active")

            item = gui.table_item(marker)
            item.setData(QtCore.Qt.UserRole, pmarker)

            if not exists:
                item.setForeground(QtGui.QBrush(QtCore.Qt.black))
            elif not active:
                item.setForeground(QtGui.QBrush(QtCore.Qt.red))

            self.markerList.insertRow(i)
            self.markerList.setItem(i, 0, item)
            self.markerList.setRowHeight(i, 14)

            if marker in sel: self.markerList.selectRow(i)

    def cb_fromSelection(self):

        """ create a new markerset from the selected markers """

        sel = m.ls(sl=True)
        if len(sel) == 0:
            m.error("Nothing selected")
            return

        ret = m.promptDialog(m="name", title="New Markerset", b=['ok', 'cancel'], cb='cancel', db='ok')
        if ret != 'ok': return

        name = m.promptDialog(q=True, text=True)

        self.raise_()
        self.activateWindow()

        mobj = markerset.fromSelection()
        self.customSets[name] = mobj
        self.markerset = mobj
        self.addMarkerset(name, mobj)
        self.markersetSelect()

    def getSelected(self, prefixed=True):
        """ returns a mocapData.Character object """
        sel = self.markerList.selectedItems()
        if sel is None: return None
        if prefixed:
            return [i.data(QtCore.Qt.UserRole) for i in sel]
        else:
            return [i.data(QtCore.Qt.DisplayRole) for i in sel]

    def cb_select(self, item):

        """ the marker select list has been clicked on, select the markers """

        if not self.toolActive:

            items = self.getSelected()
            if items is None or len(items) == 0: return

            m.select(cl=True)
            for item in items:
                fixed = keyTools.fix_name(item)
                if m.objExists(fixed): m.select(fixed, add=True)

    def cb_change(self, item):

        """ the marker assign list has been clicked on, handle using assign """

        if self.prefix is None or item is None: return

        value = self.prefix + item.text()

        sel = m.ls(sl=True)
        if sel is None or len(sel) == 0:
            m.warning("Nothing selected to assign")
            return
        elif len(sel) != 1:
            m.warning("More than one thing selected")
            return

        if sel[0] == value: return  # can't assign to self

        self.doAssign(sel[0], value)

    def onetwo(self):
        sel = m.ls(sl=True)

        if sel is None or len(sel) != 2:
            m.error("Select two items")

        self.doAssign(sel[0], sel[1])

    def query(self):

        sel = m.ls(sl=True)
        if sel is None or len(sel) == 0: m.error("Nothing selected")

        rangemode = self.sourceRangeSelector.currentText()  # none, fill, segment, spike, all, selected
        if rangemode == 'gap':
            if len(sel) < 2:
                print("Need to markers to find the gap")
                return
            s = curve.currentSegmentOrGap(sel[1], datarate.nodeRate(sel[1]))
            if s is None or s[0] != 'gap':
                print("Skipping: " + str(sel[1]) + " (not currently in a gap)")
                return

            sourceIn, sourceOut = s[1]
        else:
            sourceIn, sourceOut = assign.getSourceRange(sel[0], rangemode)
        m.selectKey(sel[0], t=(sourceIn, sourceOut))

    def doAssign(self, source, dest):

        rangemode = self.sourceRangeSelector.currentText()  # none, fill, segment, spike, all, selected
        replacemode = self.replaceModeSelector.currentText()  # extract, swap, overwrite

        # if the node does not exist, just rename the source to being the target
        if not m.objExists(dest):
            print("Rename " + str(source) + " for " + str(dest))
            m.rename(source, dest)
            self.draw(refresh=True)
            m.dgdirty(a=True)
            return

        if rangemode == 'fill':
            print("Fill: " + source + " for: " + dest)
            cmd = "from " + localsettings.module + " import keyTools as kt;"
            cmd += 'kt.fill("%s", "%s")' % (dest, source)
            m.evalDeferred(cmd)
            # keyTools.fill( dest, source )

            cmd = "from " + localsettings.module + " import labeler;"
            cmd += "labeler.INSTANCE.draw();"
            cmd += "import maya.cmds as m_cmds; m_cmds.dgdirty(a=True)"
            m.evalDeferred(cmd)
            return

        # must be eval-ed for undo to work..

        cmd = "from " + localsettings.module + " import assign;"
        cmd += "assign.assign( '%s', '%s', '%s', '%s');" % (source, dest, rangemode, replacemode)
        print(cmd)
        m.evalDeferred(cmd)

        if self.toolActive:
            cmd = 'import maya.cmds as m_cmds; m_cmds.setToolTo("' + self.context + '")'
            m.evalDeferred(cmd)

        cmd = "from " + localsettings.module + " import labeler;"
        cmd += "labeler.INSTANCE.draw()"
        m.evalDeferred(cmd)

        # self.setActiveKeys([value, sel[0]])
        # self.draw(refresh=True)

    def setActiveKeys(self, items):
        self.progressRange(len(items))
        for i in range(len(items)):
            self.progressValue(i, items[i])
            keyTools.set_active_keys(items[i])

    def loadMarkersets(self):
        # load the markersets from the directory
        markerset.load_all(markerset.markers_dir())
        self.markersetSelector.clear()
        self.markersetSelector.addItems(['--select--'] + markerset.markersets.keys())

    def cb_drawLines(self, x=None):
        if None in [self.markerset, self.prefix]:
            m.warning("No markerset or prefix")
            return

        print("drawing lines for " + str(self.prefix))
        self.markerset.drawLines(self.prefix)

    def cb_color(self, colorIndex):
        if None in [self.markerset, self.prefix]: return
        self.markerset.setColor(self.prefix, colorIndex)

    def cb_selectMarkers(self, x=None):
        """ callback to select markers """
        if None in [self.markerset, self.prefix]: return
        self.markerset.select(self.prefix)

    def cb_selectAll(self, x=None):
        m.select(cl=True)
        markers = m.ls(type='peelSquareLocator', l=True)
        if markers is None: return
        for i in markers:
            parent = m.listRelatives(i, p=True, f=True)[0]
            m.select(parent, add=True)

    def cb_clearMarkerLines(self, x=None):
        if None in [self.markerset, self.prefix]: return
        # this will clear all lines  and the group
        self.markerset.drawLines(self.prefix, clear=True)
        # this will clear all lines
        markerset.clearMarkerLines()

    def cb_setActive(self, x=None):
        self.setActiveKeys(m.ls(sl=True))

    def cb_display(self, x=None):

        # set all markers to being connect-vis
        keyTools.toggle_connect_vis(force=True)

        # for every marker in every prefix
        for prefix in self.markerset.prefixes():
            # set markerset markers to not being connect vis
            markers = self.markerset.markers(prefix)
            keyTools.connect_vis(markers, False)

    def cb_selectEmpty(self, x=None):
        keyTools.select_empty()

    def cb_selectUnlabelled(self, x=None):
        """ select markers not associcated with a current (selected) markersets """
        # this routine assumes all characters in the scene have the same markerset... what about props?
        if self.markerset is None: return
        current = []
        m.select(clear=True)

        # get all the markers in the markerset
        nodes = self.markerset.markers()

        locs = m.ls(type="peelSquareLocator", l=True)
        selme = []
        for i in locs:
            ps = m.listRelatives(i, parent=True)[0]
            pl = m.listRelatives(i, parent=True, f=True)[0]
            # dont prefix x in this loop so multiple prefixes are supported
            data = [x for x in nodes if pl.endswith(x)]
            if len(data) == 0: selme.append(pl)

        m.select(selme)

    def cb_lineColor(self, color=None, y=None):

        """ set the color for the lines (all lines in the scene) """

        lines = m.ls(type="PeelLine")
        if lines is None: return
        for line in lines:
            if color == -1:
                m.setAttr(line + ".overrideEnabled", 0)
            else:
                m.setAttr(line + ".overrideEnabled", 1)
                m.setAttr(line + ".overrideColor", color)

    def cb_drawLine(self):

        # see markerset.MarkersetBas.drawLines()

        sel = m.ls(sl=True, type='transform')
        if len(sel) < 2: return

        topNode = m.listRelatives(sel[0], p=True)[0]
        group = topNode + "|LINES"

        if not m.objExists(group):
            group = m.group(em=True, name="LINES", parent=topNode)
            m.setAttr(group + ".template", 1)

        loc = m.createNode("PeelLine", p=group, name=sel[0])
        for i in range(len(sel)):
            m.connectAttr(sel[i] + ".translate", loc + ".points[%d]" % i)

    def cb_setMarkersetDir(self):
        ret = QtWidgets.QFileDialog.getExistingDirectory(self, "Markerset Directory")
        if ret is None or len(ret) == 0: return
        m.optionVar(sv=("peelMarkersDirectory", ret))

    def cb_save(self):

        name = self.markersetSelector.currentText()
        f = name + ".markerset"
        dir = markerset.markers_dir()
        if dir is not None: f = os.path.join(dir, f)
        ret = QtWidgets.QFileDialog.getSaveFileName(self, "Save Markerset", f)
        if len(ret[0]) > 0:
            if os.path.isfile(ret[0]):
                cd = m.confirmDialog(m="File exists, overwrite?", b=['yes', 'no'])
                if cd != 'yes': return
            print("saving markerset as: " + str(ret[0]))
            self.markerset.save(name, ret[0])

    def cb_load(self):
        dir = markerset.markers_dir()
        ret = QtWidgets.QFileDialog.getOpenFileName(self, "Save Markerset", dir)
        if len(ret[0]) == 0: return

        mobj = markerset.Markerset()
        name = mobj.load(ret[0])

        self.customSets[name] = mobj
        self.markerset = mobj

        self.addMarkerset(name, mobj)
        self.markersetSelect()

    def addMarkerset(self, name, mobj):

        """ adds a markerset to the list and to markerset.markersets """

        id = self.markersetSelector.findText(name)
        if id == -1:
            self.markersetSelector.addItem(name)
            self.markersetSelector.setCurrentIndex(self.markersetSelector.count() - 1)
        else:
            self.markersetSelector.setCurrentIndex(id)

        if self.markersetSelector.findText(name) == -1:
            self.markersetSelector.addItem(name)

        self.markersetSelector.setCurrentIndex(self.markersetSelector.findText(name))
