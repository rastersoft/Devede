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
import sys
import devede_dialogs

import devede_executor

if (sys.platform=="win32") or (sys.platform=="win64"):
	import webbrowser

class show_help(devede_executor.executor):
	
	def __init__(self,gladefile,installpath,filename):
		
		devede_executor.executor.__init__(self)
		self.printout=False
		
		if (sys.platform=="win32") or (sys.platform=="win64"):
			webbrowser.open_new(os.path.join(installpath, filename))
			return

		self.printout=False

		launch_list=[[True,"yelp"],[False,"epiphany"],[False,"konqueror"],[False,"firefox","-new-window"],[False,"opera","-newwindow"]]

		file=os.path.join(installpath,"html",filename)	
		
		for program in launch_list:
			if program[0]:
				program.append("file://"+file)
			else:
				program.append(file)
			retval=self.launch_program(program[1:],80,False)
			if retval!=None:
				break
			
		if retval==None:
			msg=devede_dialogs.show_error(gladefile,_("Can't open the help files."))
		