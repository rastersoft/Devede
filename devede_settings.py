#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright 2006-2011 (C) Raster Software Vigo (Sergio Costas)

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
import gobject
import os
import sys

import devede_other

class devede_settings:
    
    def on_toggled_cb(self,w):
        
        if (self.use_ffmpeg.get_active()):
            self.ac3_fix.set_sensitive(False)
        else:
            self.ac3_fix.set_sensitive(True)
        
        if (self.multicore.get_active()):
            self.hyper.set_sensitive(True)
        else:
            self.hyper.set_sensitive(False)
    
    def __init__(self,gladefile,structure,global_vars):
        
        self.gladefile=gladefile
        self.structure=structure
        self.global_vars=global_vars
        
        self.tree=devede_other.create_tree(self,"settings",self.gladefile,False)
        self.tree.connect_signals(self)
        wsettings=self.tree.get_object("wsettings_dialog")
        
        w=self.tree.get_object("erase_files")
        w.set_active(self.global_vars["erase_files"])
        
        self.hyper=self.tree.get_object("hyperthreading")
        self.multicore=self.tree.get_object("multicore")
        if (self.global_vars["multicore"]==1):
            self.multicore.set_active(False)
            self.hyper.set_active(False)
            self.hyper.set_sensitive(False)
        else:
            self.multicore.set_active(True)
            self.global_vars["multicore"]=self.global_vars["cores"]
            self.hyper.set_sensitive(True)
            self.hyper.set_active(self.global_vars["hyperthreading"])
        
        self.ac3_fix=self.tree.get_object("AC3_fix")
        self.ac3_fix.set_active(self.global_vars["AC3_fix"])

        self.use_ffmpeg=self.tree.get_object("use_ffmpeg")
        self.use_ffmpeg.set_active(self.global_vars["use_ffmpeg"])
        self.use_ffmpeg_menu=self.tree.get_object("use_ffmpeg_menu")
        self.use_ffmpeg_menu.set_active(self.global_vars["use_ffmpeg_menu"])
            
        
        print "Path: "+str(global_vars["temp_folder"])
        path=self.tree.get_object("temporary_files")
        path.set_current_folder(global_vars["temp_folder"])
        self.on_toggled_cb(None)
        
        wsettings.show()
        value=wsettings.run()
        wsettings.hide()
        
        if value!=-6:
            wsettings.destroy()
            return
        
        w=self.tree.get_object("erase_files")
        self.global_vars["erase_files"]=w.get_active()
        
        w=self.tree.get_object("multicore")
        if w.get_active():
            self.global_vars["multicore"]=self.global_vars["cores"]
            self.global_vars["hyperthreading"]=self.hyper.get_active()
        else:
            self.global_vars["multicore"]=1
            self.global_vars["hyperthreading"]=False
        
        self.global_vars["use_ffmpeg"]=self.use_ffmpeg.get_active()
        self.global_vars["use_ffmpeg_menu"]=self.use_ffmpeg_menu.get_active()
            
        self.global_vars["AC3_fix"]=self.ac3_fix.get_active()
        
        path=self.tree.get_object("temporary_files")
        self.global_vars["temp_folder"]=path.get_current_folder()
        print "Path: "+str(self.global_vars["temp_folder"])
        
        wsettings.destroy()
        return
