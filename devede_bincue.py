#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright 2006-2009 (C) Raster Software Vigo (Sergio Costas)
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


import signal
import os
import sys
import re
import shutil

import devede_executor

class xvcd_generator(devede_executor.executor):
	
	""" This class creates BIN/CUE images for VCD, sVCD or CVD """
	
	def __init__(self,filename,filefolder,progresbar,proglabel,structure,disctocreate):
		
		devede_executor.executor.__init__(self,filename,filefolder,progresbar)
		
		proglabel.set_text(_("Creating BIN/CUE files"))
	
		cantidad=len(structure[0])-1
		if (sys.platform!="win32") and (sys.platform!="win64"):
			lista=["vcdimager","-c",filefolder+filename+".cue","-b",filefolder+filename+".bin","-t"]
		else:
			lista=["vcdimager.exe","-c",filefolder+filename+".cue","-b",filefolder+filename+".bin","-t"]

		if disctocreate=="vcd":
			lista.append("vcd2")
		else:
			lista.append("svcd")
	
		for variable in range(cantidad):
			currentfile=self.create_filename(filefolder+filename,1,variable+1,False)
			lista.append(currentfile)
			
		self.print_error=_("Failed to create the BIN/CUE files\nMaybe you ran out of disk space")
		self.launch_program(lista,output=False)


	def end_process(self,eraser,erase_temporal_files):

		print "End process bin/cue"
		if erase_temporal_files:
			eraser.delete_mpg()
			eraser.delete_menu()
			eraser.delete_xml()


class iso_generator(devede_executor.executor):
	
	""" This class generates the ISO image for DVDs """
	
	def __init__(self,filename,filefolder,progresbar,proglabel,command):
		
		devede_executor.executor.__init__(self,filename,filefolder,progresbar)
		
		proglabel.set_text(_("Creating ISO file"))
		progresbar.set_fraction(0.0)
		progresbar.set_text("0%")
	
		volume="DVDVIDEO"
		self.print_error=_("Failed to create the ISO image\nMaybe you ran out of disk space")
		self.launch_program([command,"-dvd-video","-V",volume,"-v","-udf","-o",filefolder+filename+".iso",filefolder+filename])


	def set_progress_bar(self):
		
		punto=self.cadena.find("done, estimate")
		if (punto!=-1):
			if ((self.cadena[punto-6].isdigit()) and ((self.cadena[punto-7].isdigit()) or (self.cadena[punto-7]==" "))):
				value=self.cadena[punto-7:punto-2]
				percent2=float(value.replace(",","."))
				self.bar.set_fraction(percent2/100)
				self.bar.set_text(str(int(percent2))+"%")
			return True
		return False


	def end_process(self,eraser,erase_temporal_files):
		print "intento borrar"
		if erase_temporal_files:
			eraser.delete_directory()
