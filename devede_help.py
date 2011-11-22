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
import gtk
import devede_dialogs

import devede_executor


class show_help:
	
	def __init__(self,gladefile,installpath,filename):
		
		file="file://"+os.path.join(installpath,"html",filename)	
		
		retval = gtk.show_uri(None,file,gtk.gdk.CURRENT_TIME)
		if retval==False:
			msg=devede_dialogs.show_error(gladefile,_("Can't open the help files."))
