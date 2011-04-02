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
import devede_dialogs

class title_properties:
	
	def __init__(self,gladefile,structure,title):
		
		self.structure=structure
		self.title=title
		
		self.tree=devede_other.create_tree(self,"wtitle_properties_dialog",gladefile,True)
		self.window=self.tree.get_object("wtitle_properties_dialog")
		w=self.tree.get_object("title_name")
		w.set_text(structure[title][0]["nombre"])
		w.grab_focus()
		action=structure[title][0]["jumpto"]
		if action=="menu":
			w=self.tree.get_object("title_jmenu")
		elif action=="first":
			w=self.tree.get_object("title_jfirst")
		elif action=="prev":
			w=self.tree.get_object("title_jprev")
		elif action=="loop":
			w=self.tree.get_object("title_jthis")
		elif action=="next":
			w=self.tree.get_object("title_jnext")
		elif action=="last":
			w=self.tree.get_object("title_jlast")
		w.set_active(True)
		
		self.window.show()
		retval=self.window.run()
		print "Salgo de propiedades "+str(retval)
		self.window.hide()
		
		if retval==-5:
			self.update_title()
			
		self.window.destroy()
		self.window=None

	def on_title_name_activate(self,values):
		
		self.window.response(-5)


	def update_title(self):
		
		w=self.tree.get_object("title_name")
		self.structure[self.title][0]["nombre"]=w.get_text()
		
		w=self.tree.get_object("title_jmenu")
		if w.get_active():
			self.structure[self.title][0]["jumpto"]="menu"
		w=self.tree.get_object("title_jfirst")
		if w.get_active():
			self.structure[self.title][0]["jumpto"]="first"
		w=self.tree.get_object("title_jprev")
		if w.get_active():
			self.structure[self.title][0]["jumpto"]="prev"
		w=self.tree.get_object("title_jthis")
		if w.get_active():
			self.structure[self.title][0]["jumpto"]="loop"
		w=self.tree.get_object("title_jnext")
		if w.get_active():
			self.structure[self.title][0]["jumpto"]="next"
		w=self.tree.get_object("title_jlast")
		if w.get_active():
			self.structure[self.title][0]["jumpto"]="last"
