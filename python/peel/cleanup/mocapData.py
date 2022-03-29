# Mocap Cleanup - Alastair Macleod 2016
# GPL License = http://www.gnu.org/licenses/gpl.txt 

import os
import re
import json
import struct
import traceback

from peel.cleanup.Qt import QtCore

from peel.cleanup import c3dParser

"""
Mocap Data Module

This module contains classes representing instances of motion capture data

 * File - Base Class 
 *   C3DFile - Instance of a c3d file
 *   MayaFile - Instance of a maya file (ma/mb)
 * Character - Motion Capture data gets solved on to a character
 * Session - Files are grouped by session
 * Data - QObject that holds a list of sessions, list of character and characterGroups
 * Parser - QObject base class for data parsers that generate Data

"""


def get_version(file_name):
    """ Separates the file_name into three parts : the name itself, version number and the extension.
    Valid examples:  Name followed by a hyphen or underscore, optional v then 3 numbers and extension:
        name_001.ext
        any-characters-002.ext
        file_name-v002.ext

    :param file_name: Name of the Maya Ascii or Binary file, ideally in format Filename_01.ma or Filename_v01.ma
    :type file_name: str
    :return (name, version, extension): the three parts of the file name.
    :rtype False or (str, str or None str), : tuple """

    ext = os.path.splitext(file_name)
    if ext[1].lower() not in ['.ma', '.mb']:
        return False  # Proceed if Maya file. Else return false.

    name = ext[0]
    version = None

    ver = re.match(r"(.*)[-_]v?([0-9]+)", ext[0])
    if ver:
        name = ver.group(1)
        version = ver.group(2)

    return name, version, ext[1]


class File(object):
    """ Base class for a mocap file with a session_dir, task, name and extension."""

    def __init__(self, session_path, task, file_name, extension):
        """
        Copies the data from the parameters into class variables.
        :param session_path: Location of the session folder on the local drive
        :type session_path: str
        :param task:            # ?? is task the same as take? Yes, checked it. What is the diff btn file_name and task?
        :type task: str
        :param file_name: Name of the file
        :type file_name: str
        :param extension: File type
        :type extension: str
        """
        self.session_dir = session_path
        self.task = task
        self.name = file_name
        self.extension = extension

    def get_name(self):
        """ Returns the file name without the extension
        :return (os.path.splitext(self.name)[0]) : Name of the file
        :rtype (os.path.splitext(self.name)[0]) : str """
        return os.path.splitext(self.name)[0]

    def path(self):
        """
        Returns the full path of the file.
        :return (os.path.join(self.session_dir, self.task, self.name + self.extension)): full path of the file
        :rtype (os.path.join(self.session_dir, self.task, self.name + self.extension)): path object
        """
        return os.path.join(self.session_dir, self.task, self.name + self.extension)

    def exists(self):
        """ Checks if a file exists at the specified path.
        :return os.path.isfile(self.path()): True if the file exists, false otherwise.
        :rtype os.path.isfile(self.path()): bool"""
        return os.path.isfile(self.path())

    def data_type(self):
        return None  # ?? Is it because it is in the stub? What about (raise NotImplementedError?) revisit. yes raise...


class C3DFile(File):
    """ A C3d file that exists on disk somewhere. """

    def __init__(self, is_local, session_dir, task, file_name, extension):
        """ Copies the parameter values into class variables. Calls methods to load the file and read the header data.
        :param is_local: probably indicates whether the C3D file is stored locally or on th web  #?? not used yet.
        :type is_local: bool
        :param session_dir: Path to the folder containing the session files.
        :type session_dir: str   # ?? probably
        :param task:            # ?? is task the same as take? Yes, checked it. What is the diff btn file_name and task?
        :type task: str
        :param file_name: Name of the file
        :type file_name: str
        :param extension: File type
        :type extension: str """
        super(C3DFile, self).__init__(session_dir, task, file_name, extension)
        self.is_local = is_local
        self.frame_range = None
        self.note = None
        self.c3d_file = None

        self.info = {}

        if self.exists():
            self.c3d_file = c3dParser.load(self.path())
            self.frame_range = (self.c3d_file.frame1, self.c3d_file.frameN)

    def __str__(self):
        """ Converts object to string
        return ("C3d File: " + self.get_name()): returns the name of the c3d file with descriptive text
        rtype ("C3d File: " + self.get_name()): str"""
        return "C3d File: " + self.get_name()

    def data_type(self):
        """ Returns the datatype of the file. This class only handles c3d files. Therefore, returns c3d.
        :return ("c3d"): type of file being handles
        :rtype: str"""
        return "c3d"

    def data_rate(self):
        if self.c3d_file is None:
            return 0
        return self.c3d_file.frame_rate

    def points(self):
        """ Accesses the point data from the c3d file, and returns it.
        :return self.c3d_file.points: point data from the c3d file. None, if file not found.
        :rtype: """  # ?? what does "self.c3d_file.points" look like? revisit. just int value number of piints
        if self.c3d_file is None:
            return None
        return self.c3d_file.points

    def range(self):
        """ Accesses the c3d file, and returns the in and out frames.
        :return self.c3d_file.frame1, self.c3d_file.frameN : first and last frame numbers of the range.
        :rtype: tuple"""
        if self.c3d_file is None:
            return None, None
        return self.c3d_file.frame1, self.c3d_file.frameN


class MayaFile(File):
    """ A ma or mb file that exists on disk somewhere."""

    @staticmethod
    def FromC3d(c3d, task=None, version=None):
        """ Returns a mb or ma file if one exists, otherwise returns mb
        :param c3d: The c3d file
        :type c3d: file
        :param task: ?? not sure
        :type task: ?? not sure
        :param version: Version number of the file.
        :type version: int"""
        if task is None: task = c3d.task

        return MayaFile(c3d.session_dir, task, c3d.name, version, '.mb')

    # the version has to be stored as a string so the full path can be rebuilt
    # full path is session_path \ task \ name + version + extension

    def __init__(self, session_path, task, name, version, extension=".mb"):
        super(MayaFile, self).__init__(session_path, task, name, extension)

        if version is True:
            print("True")
            v = 1
            self.set_version(v)
            while self.exists():
                print("exists: " + str(self.path()))
                v += 1
                self.set_version(v)
        elif version is None:
            v = 1
            self.set_version(v)
            while self.exists():
                v += 1
                self.set_version(v)
            v = v - 1
            self.set_version(v)
        elif version is False:
            self.version = None
        elif isinstance(version, int):
            # self.name = self.name + "_"
            self.version = "%03d" % version
        else:
            self.version = version

    def exists(self):
        ext = self.extension
        self.extension = ".ma"
        test1 = os.path.isfile(self.path())
        self.extension = ".mb"
        test2 = os.path.isfile(self.path())
        self.extension = ext
        return test1 or test2

    def set_version(self, v):
        self.version = "%03d" % v

    def get_version(self):
        if self.version is None: return None
        return int(self.version)

    def data_type(self):
        return "maya"

    def __str__(self):
        return "MayaFile: " + str(self.name) + " Version: " + str(self.get_version())

    def get_name(self):
        if self.version is None: return self.name
        name = self.name
        if not name.endswith("_"):
            name += "_"
        return name + self.version

    def path(self):
        return os.path.join(self.session_dir, self.task, self.get_name() + self.extension)


class Character:
    """ Character """

    def __init__(self, id, name, file, thumb=None, actor=None, group=None):
        self.id = id
        self.name = name
        self.file = file
        self.thumb = thumb
        self.actor = actor
        self.group = group


class Session:
    """ Represents a mocap session directory with subdirectores for each task: raw, cleaning, solving
        tasks['raw'] is a dict of C3D File Objects 
        addTask( title ) will return a list which items for that task can be added to
    """

    def __init__(self, title, id):
        self.title = title
        self.id = id
        self.tasks = {}

    def empty(self):
        self.tasks = {}

    def addTask(self, title):
        if title in self.tasks:
            return self.tasks[title]
        task = []
        self.tasks[title] = task
        return task

    def addMocap(self, item):
        if 'raw' not in self.tasks:
            self.tasks['raw'] = []
        self.tasks['raw'].append(item)

    def __str__(self):
        ret = "#" + str(self.id) + "  "
        ret = ret + self.title + " "
        for t in self.tasks:
            ret += "%s: %d  " % (t, len(self.tasks[t]))
        return ret

    def getTask(self, name):
        if name not in self.tasks: return None
        return self.tasks[name]


class Data(QtCore.QObject):

    def __init__(self):
        super(Data, self).__init__()
        self.sessions = []  # array of Session objects
        self.characters = []  # array of Character objects
        self.characterGroups = []

    def getSessions(self):
        return map(lambda v: v.title, self.sessions)

    def getCharacters(self):
        return map(lambda v: v.name, self.characters)

    def __str__(self):
        return 'Sessions: %d   Characters: %d' % (len(self.sessions), len(self.characters))


class Parser(QtCore.QObject):
    """ Parser base class (QObject) with message attribute """

    message = QtCore.Signal(str)
    error = QtCore.Signal(str)
    progress = QtCore.Signal(int, int, int, str)

    def __init__(self, base_dir):
        super(Parser, self).__init__()
        self.base_dir = base_dir
        self.data = None
        self.rangeData = None
        self.notesData = None

    def logMessage(self, value, color=0):
        if color == 1:
            self.message.emit('<B><FONT COLOR="#4455EE">' + value + '</FONT></B>');
        else:
            self.message.emit(value)

    def logError(self, value):
        self.error.emit(value)

    def logProgress(self, stage, current, max, message):
        self.progress.emit(stage, current, max, message)

    def parse(self, mkdir=False):

        """ Reads a local data to populate the interface.  The basedir should have subdirectories for each session.  
            Each session should have subdirectories for 'c3d' (raw), 'cleaning' and 'solving'.  Session directories
            that do not have task directories with valid files in them will not be added to the list.

            Data is saved in the data.sessions list as Session objects.

        """

        self.data = Data()

        self.logMessage("Loading from directory: " + str(self.base_dir))

        sessionId = 0

        try:
            if self.base_dir is None or not os.path.isdir(self.base_dir):
                print("Not a directory: " + str(self.base_dir))
                return

        except Exception as e:
            self.logError(e)
            print("Error " + str(e))
            print("While looking for directory: " + str(self.base_dir))

        items = os.listdir(self.base_dir)
        # add Session objects to self.data
        for cc, sessionName in enumerate(items):

            self.logProgress(0, cc, len(items), sessionName)

            # create a new Session object to hold the data and add it to data.sessions list
            # give it a number to maintain compat with web data

            c3ddir = os.path.join(self.base_dir, sessionName, 'c3d')
            rawdir = os.path.join(self.base_dir, sessionName, 'raw')

            if os.path.isdir(c3ddir) or os.path.isdir(rawdir):

                self.data.sessions.append(Session(sessionName, sessionId))

                sessionId = sessionId + 1

            else:
                print("Not a session directory: " + str(c3ddir))
                print("Expected this directory to contain a directory called 'c3d' or 'raw':")
                print("    " + os.path.join(self.base_dir, sessionName))

        self.logProgress(1, 0, 0, '')

    def getSessions(self):
        items = [(i.title, i.id) for i in self.data.sessions]
        return sorted(items, key=lambda v: v[0], reverse=True)

    def get_session(self, title=None, id=None):
        if title is None and id is None: raise ValueError("Specify title or id");

        for session_obj in self.data.sessions:
            if id is not None and session_obj.id == id: return session_obj
            if title is not None and session_obj.title == title: return session_obj

        return None

    def loadJson(self, session, filename):

        datfile = os.path.join(self.base_dir, session, filename)

        if not os.path.isfile(datfile): return None

        fp = open(datfile)

        if not fp: return None

        data = json.load(fp)
        fp.close()
        return data

    def parseSession(self, sessionObj, mkdir):

        # for each session directory under the root

        self.logMessage("Parsing: " + os.path.join(self.base_dir, sessionObj.title))

        sessionObj.empty()

        self.rangeData = self.loadJson(sessionObj.title, "range-data.json")
        self.notesData = self.loadJson(sessionObj.title, "notes-data.json")

        try:
            count = self.parseTasks(sessionObj)
        except Exception as e:
            traceback.print_exc()
            self.logError(sessionObj.title + "  " + str(e))
            print(str(sessionObj), str(e))
            return

        if count > 0:
            self.logMessage(str(sessionObj.title), color=1)
            self.logMessage("Raw files: " + str(count))

    def parseTasks(self, session_obj):

        """ search the session directory for task directories and add them to the session object """

        session_path = os.path.join(self.base_dir, session_obj.title)
        if not os.path.isdir(session_path): return

        count = 0

        print("-" * 100)
        print("Checking session directory: " + session_path + "\c3d")

        stage = 1

        # search data type dir (c3d/raw/cleaning/solving)
        for taskName in os.listdir(session_path):

            task_path = os.path.join(session_path, taskName)

            if not os.path.isdir(task_path):
                continue

            if taskName.lower() in ['c3d', 'raw']:

                stage += 1

                # c3d files

                task = session_obj.addTask("raw")

                c3d_items = os.listdir(task_path)
                for cc, c3dFile in enumerate(c3d_items):
                    self.logProgress(stage, cc, len(c3d_items), c3dFile)

                    c3d_full_path = os.path.join(task_path, c3dFile)
                    if not os.path.isfile(c3d_full_path): continue
                    file_base, ext = os.path.splitext(c3dFile)
                    if ext.lower() != '.c3d': continue
                    c3d_obj = C3DFile(True, session_path, taskName, file_base, ext)

                    # range data from json file
                    if self.rangeData is not None and file_base in self.rangeData:
                        c3d_obj.frame_range = self.rangeData[file_base]

                    # notes from json
                    if self.notesData is not None and file_base in self.notesData:
                        c3d_obj.note = self.notesData[file_base]

                    task.append(c3d_obj)

                    count += 1

                stage += 1

            elif taskName.lower() == 'templates' or taskName.lower() == 'template':

                print("> Found template directory: ", task_path)

                task = session_obj.addTask("template")

                template_items = os.listdir(task_path)
                for cc, templateFile in enumerate(template_items):

                    self.logProgress(stage, cc, len(template_items), templateFile)

                    verdata = get_version(templateFile)
                    if not verdata:
                        continue

                    task.append(MayaFile(session_path, taskName, *verdata))

                stage += 1

            if taskName.lower() in ['cleaning', 'solving']:
                # else :

                print("> Found " + taskName + " directory: ", task_path)

                task = session_obj.addTask(taskName)
                taskItems = os.listdir(task_path)

                for cc, fileName in enumerate(taskItems):

                    self.logProgress(stage, cc, len(taskItems), fileName)

                    fullPath = os.path.join(task_path, fileName)
                    if not os.path.isfile(fullPath): continue  # skip non-files

                    verdata = get_version(fileName)
                    if not verdata:
                        continue
                    task.append(MayaFile(session_path, task, *verdata))
                    count += 1

                stage += 1

        self.logProgress(5, 0, 0, '')

        return count
