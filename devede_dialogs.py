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

import pygtk # for testing GTK version number
pygtk.require ('2.0')
import gtk
import devede_other

class show_error:
	
	def __init__(self,gladefile,message):
		
		""" Shows a window with an error """
		
		self.newtree=devede_other.create_tree(self,"werror_dialog",gladefile,False)
		label=self.newtree.get_object("label_error_dialog")
		label.set_text(message)
		window=self.newtree.get_object("werror_dialog")
		window.show()
		window.run()
		window.hide()
		window.destroy()
		window=None


class show_warning:
	
	def __init__(self,gladefile,message):
		
		""" Shows a window with an error """
		
		self.newtree=devede_other.create_tree(self,"wwarning_dialog",gladefile,False)
		label=self.newtree.get_object("wwarning_dialog_text")
		label.set_text(message)
		window=self.newtree.get_object("wwarning_dialog")
		window.show()
		window.run()
		window.hide()
		window.destroy()
		window=None


class ask_exit:
	
	def __init__(self,gladefile):
	
		self.newtree=devede_other.create_tree(self,"wcancel_dialog",gladefile,False)
		self.window=self.newtree.get_object("wcancel_dialog")
		
	def run(self):
		self.window.show()
		retval=self.window.run()
		self.window.hide()
		self.window.destroy()
		self.window=None
		return retval


class ask_overwrite_onload:
	
	def __init__(self,gladefile):
	
		self.newtree=devede_other.create_tree(self,"wloosecurrent",gladefile,False)
		self.window=self.newtree.get_object("wloosecurrent")
		
	def run(self):
		self.window.show()
		retval=self.window.run()
		self.window.hide()
		self.window.destroy()
		self.window=None
		return retval


class ask_delete_title:
	
	def __init__(self,titlename,gladefile):
		
		self.newtree=devede_other.create_tree(self,"wdel_title_dialog",gladefile,False)
		self.window=self.newtree.get_object("wdel_title_dialog")
		label=self.newtree.get_object("what_title")
		label.set_text(titlename)
	
	def run(self):
		self.window.show()
		retval=self.window.run()
		self.window.hide()
		self.window.destroy()
		self.window=None
		return retval


class ask_delete_chapter:
	
	def __init__(self,titlename,gladefile):
		
		self.newtree=devede_other.create_tree(self,"wdel_chapter_dialog",gladefile,False)
		self.window=self.newtree.get_object("wdel_chapter_dialog")
		label=self.newtree.get_object("labelchapter")
		label.set_text(titlename)
	
	def run(self):
		self.window.show()
		retval=self.window.run()
		self.window.hide()
		self.window.destroy()
		self.window=None
		return retval


class ask_erase_all:
	
	def __init__(self,gladefile):
		
		self.newtree=devede_other.create_tree(self,"werase_dialog",gladefile,False)
		self.window=self.newtree.get_object("werase_dialog")

	def run(self):
		self.window.show()
		retval=self.window.run()
		self.window.hide()
		self.window.destroy()
		self.window=None
		return retval


class show_about:

	def __init__(self,gladefile):

		""" Shows the About dialog """
	
		self.newtree=devede_other.create_tree(self,"aboutdialog1",gladefile,False)
		window=self.newtree.get_object("aboutdialog1")
		window.show()
		window.run()
		window.hide()
		window.destroy()
		window=None
