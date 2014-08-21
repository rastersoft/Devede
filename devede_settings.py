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
        
        if (self.multicore.get_active()):
            self.hyper.set_sensitive(True)
        else:
            self.hyper.set_sensitive(False)
    
    def set_model_from_list (self, cb, items, selected):
        """Setup a ComboBox or ComboBoxEntry based on a list of strings."""
        model = gtk.ListStore(str)
        pos=-1
        c=0
        for i in items:
            model.append([i])
            if (i==selected):
                pos=c
            c+=1
        cb.set_model(model)
        cell = gtk.CellRendererText()
        cb.pack_start(cell, True)
        cb.add_attribute(cell, 'text', 0)
        if (pos!=-1):
            cb.set_active(pos)

    def __init__(self,gladefile,structure,global_vars):
        
        self.gladefile=gladefile
        self.structure=structure
        self.global_vars=global_vars
        
        self.tree=devede_other.create_tree(self,"settings",self.gladefile,False)
        self.tree.connect_signals(self)
        wsettings=self.tree.get_object("wsettings_dialog")
        
        self.videos_combo=self.tree.get_object("combobox_videos")
        self.menus_combo=self.tree.get_object("combobox_menus")
        
        self.set_model_from_list(self.videos_combo,global_vars["encoders"],global_vars["encoder_video"])
        self.set_model_from_list(self.menus_combo,global_vars["encoders"],global_vars["encoder_menu"])
        
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
        self.ac3_fix.set_sensitive(True)
        self.ac3_fix.set_active(self.global_vars["AC3_fix"])
        
        self.ac3_fix_ffmpeg=self.tree.get_object("AC3_fix_ffmpeg")
        self.ac3_fix_ffmpeg.set_sensitive(True)
        self.ac3_fix_ffmpeg.set_active(self.global_vars["AC3_fix_ffmpeg"])
        
        self.ac3_fix_avconv=self.tree.get_object("AC3_fix_avconv")
        self.ac3_fix_avconv.set_sensitive(True)
        self.ac3_fix_avconv.set_active(self.global_vars["AC3_fix_avconv"])
        
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
        
        self.global_vars["encoder_video"]=self.global_vars["encoders"][self.videos_combo.get_active()]
        self.global_vars["encoder_menu"]=self.global_vars["encoders"][self.menus_combo.get_active()]
            
        self.global_vars["AC3_fix"]=self.ac3_fix.get_active()
        self.global_vars["AC3_fix_ffmpeg"]=self.ac3_fix_ffmpeg.get_active()
        self.global_vars["AC3_fix_avconv"]=self.ac3_fix_avconv.get_active()
                
        path=self.tree.get_object("temporary_files")
        self.global_vars["temp_folder"]=path.get_filename()
        print "Path: "+str(self.global_vars["temp_folder"])
        
        wsettings.destroy()
        return
