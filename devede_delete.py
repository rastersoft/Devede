#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright 2006-2007 (C) Raster Software Vigo (Sergio Costas)
# Copyright 2006-2007 (C) Peter Gill - win32 parts

# This file is part of DeVeDe
#
# DeVeDe is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# DeVeDe is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import os
import shutil
import glob

class delete_files:

	""" This class allows to delete temporary files and directories """
	
	def __init__(self,filename,filefolder):
		
		self.filename=filename
		self.filefolder=filefolder
		self.filepath=os.path.join(filefolder,filename)
		print "Path para borrar: "+str(self.filepath)


	def delete_all(self):
		
		self.delete_avi()
		self.delete_bin_cue()
		self.delete_directory()
		self.delete_iso()
		self.delete_menu_temp()
		self.delete_menu()
		self.delete_mpg()
		self.delete_log()
		self.delete_sub_xml()
		self.delete_xml()
		self.delete_main_dir()


	def delete_mpg(self):

		print "Deleting "+self.filename+"_??_??.mpg"
		try:
			listfiles=glob.glob(self.filepath+"_[0-9][0-9]_[0-9][0-9]"+".mpg")
			for afile in listfiles:
				print "Trying to delete "+afile
				try:
					os.remove(afile)
				except OSError:
					print str(afile.strip())+" not found to remove"
		except OSError:
			print self.filepath+"._??_??.mpg not found"
	
	
	def delete_log(self):

		print "Deleting "+self.filename+".log"
		try:
			os.remove(self.filename+".log")
		except OSError:
			print self.filepath+".log not found"
	
	
	def delete_avi(self):

		try:
			listfiles=glob.glob(self.filepath+"_01_[0-9][0-9]"+".avi")
			for afile in listfiles:
				try:
					os.remove(afile)
				except OSError:
					print str(afile.strip())+" not found to remove"
		except OSError:
			print self.filepath+"._01_??.avi not found"
			
	
	def delete_xml(self):
		
		try:
			os.remove(self.filepath+".xml")
			listfiles=glob.glob(self.filepath+"_menu_[0-9]"+".xml")
			for afile in listfiles:
				try:
					os.remove(afile)
				except OSError:
					print str(afile.strip())+" not found to remove"
		except OSError:
			print self.filepath+".xml not found"


	def delete_menu_temp(self):
	
		print "delete menu temp"
		try:
			listfiles=glob.glob(self.filepath+"_menu[0-9]"+"_bg.png")
			for afile in listfiles:
				try:
					os.remove(afile)
				except OSError:
					print str(afile.strip())+" not found to remove"
		except OSError:
			print "Can't delete "+self.filepath+"_menu?_bg.png"

		try:
			listfiles=glob.glob(self.filepath+"_menu[0-9]"+"_bg_active_out.png")
			for afile in listfiles:
				try:
					os.remove(afile)
				except OSError:
					print str(afile.strip())+" not found to remove"
		except OSError:
			print "Can't delete "+self.filepath+"_menu?_bg_active_out.png"

		try:
			listfiles=glob.glob(self.filepath+"_menu[0-9]"+"_bg_inactive_out.png")
			for afile in listfiles:
				try:
					os.remove(afile)
				except OSError:
					print str(afile.strip())+" not found to remove"
		except OSError:
			print "Can't delete "+self.filepath+"_menu?_bg_inactive_out.png"
			
		try:
			listfiles=glob.glob(self.filepath+"_menu[0-9]"+"_bg_select_out.png")
			for afile in listfiles:
				try:
					os.remove(afile)
				except OSError:
					print str(afile.strip())+" not found to remove"
		except OSError:
			print "Can't delete "+self.filepath+"_menu?_bg_select_out.png"

		try:
			listfiles=glob.glob(self.filepath+"_menu_[0-9]"+".mpg")
			for afile in listfiles:
				try:
					os.remove(afile)
				except OSError:
					print str(afile.strip())+" not found to remove"
		except OSError:
			print "Can't delete "+self.filepath+"_menu_?.mpg"


	def delete_menu(self):
		
		print "delete menu"
		
		try:
			listfiles=glob.glob(self.filepath+"_menu2_[0-9]"+".mpg")
			for afile in listfiles:
				try:
					os.remove(afile)
				except OSError:
					print str(afile.strip())+" not found to remove"
		except OSError:
			print "Can't delete "+self.filepath+"_menu2_?.mpg"


	def delete_sub_xml(self,xtrasub=""):

		try:
			os.remove(self.filepath+"_sub.xml")
		except OSError:
			print self.filepath+".xml not found"
		if xtrasub!="":
			try:
				os.remove(xtrasub)
			except OSError:
				print str(xtrasub)+" not found"
		
	
	def delete_iso(self):
		
		try:
			os.remove(self.filepath+".iso")
		except OSError:
			print self.filepath+".iso not found"


	def delete_bin_cue(self):
		
		try:
			os.remove(self.filepath+".cue")
		except OSError:
			print self.filepath+".cue not found"
			
		try:
			os.remove(self.filepath+".bin")
		except OSError:
			print self.filepath+".bin not found"


	def delete_directory(self):

		try:
			shutil.rmtree(self.filepath)
		except OSError:
			print self.filepath+os.sep+" not found"
			
	def delete_main_dir(self):

		print "Borro principal"
		return

		try:
			shutil.rmtree(self.filepath)
		except OSError:
			print self.filepath+os.sep+" not found"
