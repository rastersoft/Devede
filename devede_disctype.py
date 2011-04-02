#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright 2006-2009 (C) Raster Software Vigo (Sergio Costas)
# Copyright 2006-2009 (C) Peter Gill - win32 parts

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

import pygtk # for testing GTK version number
pygtk.require ('2.0')
import gtk
import devede_main
import devede_dialogs
import os
import devede_other

class disctype:
	
	def __init__(self,global_vars):

		self.gladefile=global_vars["gladefile"]
		self.global_vars=global_vars
		
		self.tree=devede_other.create_tree(self,"wdisk_type",self.gladefile)
		self.window=self.tree.get_object("wdisk_type")
		self.main_window=None
		self.window.show()

	
	def on_wdisk_type_delete_event(self,widget,signal):
		""" Callback which shows the "Are you sure?" window """
	
		return self.ask_cancel()
	
	
	def on_wdisk_type_cancel_clicked(self,widget):
		""" Callback which shows the "Are you sure?" window """
	
		return self.ask_cancel()
	
	
	def ask_cancel(self):
	
		window=devede_dialogs.ask_exit(self.gladefile)
		retval=window.run()
		window=None
		print "Retorno: ",
		print retval
		if retval==-5:
			gtk.main_quit()
			return False
		return True

	
	def on_disctype_dvd(self,widget):
	
		self.global_vars["disctocreate"]="dvd"
		self.set_disk_type()

		
	def on_disctype_vcd(self,widget):
	
		self.global_vars["disctocreate"]="vcd"
		self.set_disk_type()

		
	def on_disctype_svcd(self,widget):
	
		self.global_vars["disctocreate"]="svcd"
		self.set_disk_type()

		
	def on_disctype_cvd(self,widget):
	
		self.global_vars["disctocreate"]="cvd"
		self.set_disk_type()

		
	def on_disctype_divx(self,widget):
	
		self.global_vars["disctocreate"]="divx"
		self.set_disk_type()
	
		
	def set_disk_type(self):
		
		if self.main_window==None:
			self.main_window=devede_main.main_window(self.global_vars,self.show_again)
		self.main_window.set_disc_type(True)
		self.main_window.show()
		self.window.hide()


	def show_again(self):
		
		""" Callback which is called from main window when the user wants to change the
			disk type """
		
		self.main_window.hide()	
		self.window.show()
