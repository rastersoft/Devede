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


import signal
import os
import sys
import re
import shutil

import devede_executor

class dvd_generator(devede_executor.executor):
	
	def __init__(self,filename,filefolder,progresbar,proglabel):
		
		devede_executor.executor.__init__(self,filename,filefolder,progresbar)
		proglabel.set_text(_("Creating DVD tree structure"))
		if (sys.platform=="win32") or (sys.platform=="win64"):
			command="dvdauthor.exe"
		else:
			command="dvdauthor"

		self.print_error=_("Failed to create the DVD tree\nMaybe you ran out of disk space")
		self.launch_program([command,"-x",filefolder+filename+".xml"])
		

	def set_progress_bar(self):
		
		if (sys.platform=="win32") or (sys.platform=="win64"):
			# This seems to be about all that can be done with dvdauthor on windows
			self.bar.pulse()
			return True
		
		if self.cadena.find("INFO: Video")!=-1:
			self.bar.pulse()
			return True
		else:
			position=self.cadena.find("STAT: VOBU ")
			if position!=-1:
				self.bar.pulse()
				self.bar.set_text("VOBU "+self.cadena[position+11:self.cadena.find(" ",position+11)])
				return True
			else:
				position=self.cadena.find("STAT: fixing VOBU at ")
				if (position!=-1):
					position2=self.cadena.find("%",position+21)
					if (position2!=-1):
						cadena=self.cadena[position2-2:position2]
						self.bar.set_text(cadena+"%")
						self.bar.set_fraction((float(cadena))/100.0)
						self.read_chars=200
						return True
		return False


	def end_process(self,eraser,erase_temporal_files):

		if erase_temporal_files:
			eraser.delete_mpg()
			eraser.delete_menu()
			eraser.delete_xml()
