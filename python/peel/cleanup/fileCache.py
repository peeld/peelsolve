# Mocap Cleanup - Alastair Macleod 2016
# GPL License = http://www.gnu.org/licenses/gpl.txt 

import maya.cmds as m
import maya.mel as mel
import os.path
import os
import tempfile
import httplib
import sys
from functools import partial

class FileCache :

	''' Copies files from the network locally and keeps a cache of their url->temp files '''

	files = {}

	def download(self, url) :
		'''
		download a file from the server to a temp file
		@return the path to the local temp file
		'''

		conn = httplib.HTTPConnection('mocap.ca')
		print("reading from: %s" % url)
		conn.request("GET", url)
		x = conn.getresponse()
		if x.status != 200 :
			m.confirmDialog(m="Error getting data from server: %i %s\nUrl: %s " % (x.status, x.reason, url))
			return

		temp_path = tempfile.mktemp()
		print("copying to temp file: %s" % temp_path)
		fp = open(temp_path, "wb");

		fp.write(x.read())
		fp.close()
		conn.close()

		return temp_path

	def cacheFile(self, url) :

		''' return the local path to the file if it exists, or download it '''

		if url in self.files and os.path.isfile(self.files[url]) :
			return self.files[url]

		f = self.download(url)
		self.files[url] = f
		return f

	def importUrl(self, url, dataType = None) :

		'''
		cache a url, then try to import it in to maya
		@param dataType mb, ma, obj, c3d or zip file containing an obj
		'''

		temp_path = self.cacheFile(url)
		if temp_path is None : return

		if dataType is None :
			# datatype not specified, guess based on file extension
			(base, dataType) = os.path.splitext(url)
			if dataType == '' :
				m.confirmDialog(m="Invalid url error");
				return

			dataType = dataType[1:]

		if dataType.lower() == "c3d"  :
			importc3d(temp_path)
			groupname = os.path.split(temp_path)[1]
			filename  = os.path.split(url)[1]
			if m.objExists(groupname) : m.rename(groupname, filename)

		elif dataType.lower() == "zip" :
			import zipfile

			tempdir = tempfile.mkdtemp()
			zfile = zipfile.ZipFile(temp_path)
			files = []

			for name in zfile.namelist() :
				temp_file = os.path.join(tempdir, name)
				fout = open(temp_file, "w")
				fout.write(zfile.read(name))
				fout.close()
				files.append(temp_file)
			     
			for i in files :
				loc = i.rfind(".")
				dt = i[loc:]
				if dt == ".obj" :
					ret = m.file(i, i=True, type="OBJ", rnn=True)

			return

		elif dataType.lower() == "mb" :
			m.file(temp_path, i=True,type="mayaBinary")

		elif dataType.lower() == "ma" :
			m.file(temp_path, i=True, type="mayaAscii")

		elif dataType.lower() == "obj" :
			m.file(temp_path, i=True, type="OBJ")

		else :
			m.confirmDialog(m="Invalid/unsupported file type error: %s" % dataType)
			return


win = "peelSelector"

