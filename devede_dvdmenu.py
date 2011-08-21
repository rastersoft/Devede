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
import cairo
import os

import devede_other
import devede_dialogs
import devede_xml_menu
import devede_newfiles
import devede_help


class menu_options:

	def __init__(self,gladefile,structure,global_vars,callback):
		
		self.global_vars=global_vars
		self.gladefile=gladefile
		self.structure=structure
		self.callback=callback
		
		self.tree=devede_other.create_tree(self,"wmenu_properties",self.gladefile)
		self.window=self.tree.get_object("wmenu_properties")
		
		menu_filename=global_vars["menu_bg"]
		if menu_filename==None:
			menu_filename=os.path.join(global_vars["path"],"backgrounds","default_bg.png")
		w=self.tree.get_object("menu_bg_file")
		w.set_filename(menu_filename)
		filter=gtk.FileFilter()
		filter.add_mime_type("image/*")
		filter.set_name("Pictures")
		w.add_filter(filter)
		
		self.preview_x=200
		self.preview_y=200
		self.sf_final=cairo.ImageSurface(cairo.FORMAT_ARGB32,self.preview_x,self.preview_y)
		self.preview=gtk.DrawingArea()
		self.preview.set_size_request(self.preview_x,self.preview_y)
		self.preview.connect("expose-event",self.repaint_preview)
		w.set_preview_widget(self.preview)

		self.on_menu_bg_file_update_preview(w,menu_filename)
		
		self.adding_sound=True
		w=self.tree.get_object("menu_sound")
		print "filtro"
		filter2=gtk.FileFilter()
		filter2.add_mime_type("audio/mpeg")
		filter2.add_mime_type("audio/x-wav")
		filter2.add_mime_type("application/ogg")
		filter2.add_mime_type("audio/ogg")
		filter2.set_name("Audio files")
		w.add_filter(filter2)
		print "filtrado"
		w.set_filename(global_vars["menu_sound"])
		print "Añado"
		
		w=self.tree.get_object("menufont")
		w.set_font_name(global_vars["fontname"])
		
		w=self.tree.get_object("unselected_color")
		color=global_vars["menu_font_color"]
		c1=gtk.gdk.Color(color[0],color[1],color[2])
		w.set_color(c1)
		w.set_alpha(color[3])
		
		w=self.tree.get_object("selected_color")
		color=global_vars["menu_selc_color"]
		c1=gtk.gdk.Color(color[0],color[1],color[2])
		w.set_color(c1)
		
		w=self.tree.get_object("shadow_color")
		color=global_vars["menu_shadow_color"]
		c1=gtk.gdk.Color(color[0],color[1],color[2])
		w.set_color(c1)
		w.set_alpha(color[3])
		
		w=self.tree.get_object("bg_color")
		color=global_vars["menu_bgcolor"]
		c1=gtk.gdk.Color(color[0],color[1],color[2])
		w.set_color(c1)
		w.set_alpha(color[3])
		
		if global_vars["menu_alignment"]==0:
			w=self.tree.get_object("menutop")
		elif global_vars["menu_alignment"]==1:
			w=self.tree.get_object("menubottom")
		else:
			w=self.tree.get_object("menumiddle")
		w.set_active(True)
		
		if global_vars["menu_halignment"]==0:
			w=self.tree.get_object("menuleft")
		elif global_vars["menu_halignment"]==1:
			w=self.tree.get_object("menuright")
		else:
			w=self.tree.get_object("menucenter")
		w.set_active(True)
		
		if global_vars["do_menu"]:
			w=self.tree.get_object("domenu")
		else:
			w=self.tree.get_object("notmenu")
		w.set_active(True)
		
		w=self.tree.get_object("menu_title_text")
		w.set_text(global_vars["menu_title_text"])
		
		w=self.tree.get_object("menu_title_color")
		color=global_vars["menu_title_color"]
		c1=gtk.gdk.Color(color[0],color[1],color[2])
		w.set_color(c1)
		w.set_alpha(color[3])
		
		w=self.tree.get_object("menu_title_shadow")
		color=global_vars["menu_title_shadow"]
		c1=gtk.gdk.Color(color[0],color[1],color[2])
		w.set_color(c1)
		w.set_alpha(color[3])
		
		w=self.tree.get_object("menu_title_font")
		w.set_font_name(global_vars["menu_title_fontname"])
		
		self.window.show()


	def repaint_preview(self,dwidget,evento):
		try:
			cr=dwidget.window.cairo_create()
			cr.set_source_surface(self.sf_final)
			cr.paint()
		except:
			return


	def on_menu_bg_file_update_preview(self,widget,filename2=None):
		try:
			if filename2==None:
				filename=widget.get_preview_filename()
			else:
				filename=filename2

			print "Using "+str(filename)+" as menu background"
			
			pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
			x = pixbuf.get_width()
			y = pixbuf.get_height()

			sf_base = cairo.ImageSurface(0,x,y)

			ct = cairo.Context(sf_base)
			ct2 = gtk.gdk.CairoContext(ct)

			ct2.set_source_pixbuf(pixbuf,0,0)
			ct2.paint()
			ct2.stroke()

			xbase=float(sf_base.get_width())
			ybase=float(sf_base.get_height())
			
			cr_final=cairo.Context(self.sf_final)
			cr_final.set_source_rgb(1.0,1.0,1.0)
			cr_final.paint()
			if xbase>ybase:
				divisor=xbase
			else:
				divisor=ybase
			
			cr_final.scale(float(self.preview_x)/divisor,float(self.preview_y)/divisor)
			
			cr_final.set_source_surface(sf_base)
			cr_final.paint()
			self.repaint_preview(self.preview,"")
			widget.set_preview_widget_active(True)
		except:
			widget.set_preview_widget_active(False)


	def on_menu_sound_selection_changed(self,widget):
		
		print "Entro"
		
		if self.adding_sound:
			self.adding_sound=False
			return
		
		filename=widget.get_filename()
		if (filename==None) or (filename==""):
			return
		
		test=devede_newfiles.file_get_params()
		check,channels=test.read_file_values(filename,True)
		if (check!=False) or (channels!=1):
			filename=os.path.join(self.global_vars["path"],"silence.ogg")
			widget.set_filename(filename)
			w = devede_dialogs.show_error(self.gladefile,_("The menu soundtrack seems damaged. Using the default silent soundtrack."))
			w = None
		test=None


	def on_menu_no_sound_clicked(self,widget):
		
		w=self.tree.get_object("menu_sound")
		w.set_filename(os.path.join(self.global_vars["path"],"silence.ogg"))

	def on_menu_help_clicked(self,widget):
	
		help_class=devede_help.show_help(self.gladefile,self.global_vars["help_path"],"menu.html")
		
	def on_menuprop_cancel_clicked(self,widget):
		
		self.window.hide()
		self.window.destroy()
		self.window=None


	def on_menuprop_accept_clicked(self,widget):

		self.set_new_bg(self.global_vars)
		self.window.hide()
		self.window.destroy()
		self.window=None
		
	
	def on_menu_preview_clicked(self,widget):
	
		global_vars2={}
		global_vars2["PAL"]=self.global_vars["PAL"]
		global_vars2["with_menu"]=True
		global_vars2["AC3_fix"]=self.global_vars["AC3_fix"]
		self.set_new_bg(global_vars2)
		window=menu_preview(self.gladefile,self.structure,global_vars2)
		window=None
	
	
	def on_menu_default_bg_clicked(self,widget):
		
		self.global_vars["menu_bg"]=os.path.join(self.global_vars["path"],"backgrounds","default_bg.png")
		w=self.tree.get_object("menu_bg_file")
		w.set_filename(self.global_vars["menu_bg"])
	
	
	def set_new_bg(self,global_vars):
		
		w=self.tree.get_object("menu_bg_file")
		menu_filename=w.get_filename()
		if menu_filename==None:
			menu_filename=os.path.join(self.global_vars["path"],"backgrounds","default_bg.png")
		global_vars["menu_bg"]=menu_filename

		w=self.tree.get_object("menu_sound")
		sound_filename=w.get_filename()
		test=devede_newfiles.file_get_params()
		check,channels=test.read_file_values(sound_filename,True)
		global_vars["menu_sound"]=sound_filename
		global_vars["menu_sound_duration"]=test.length
		test=None

		w=self.tree.get_object("menufont")
		global_vars["fontname"]=w.get_font_name()
		
		w=self.tree.get_object("unselected_color")
		color=w.get_color()
		global_vars["menu_font_color"]=[color.red,color.green,color.blue,w.get_alpha()]
				
		w=self.tree.get_object("selected_color")
		color=w.get_color()
		global_vars["menu_selc_color"]=[color.red,color.green,color.blue,65535]
		
		w=self.tree.get_object("shadow_color")
		color=w.get_color()
		global_vars["menu_shadow_color"]=[color.red,color.green,color.blue,w.get_alpha()]
		
		w=self.tree.get_object("bg_color")
		color=w.get_color()
		global_vars["menu_bgcolor"]=[color.red,color.green,color.blue,w.get_alpha()]

		align=0 # top
		w=self.tree.get_object("menumiddle")
		if w.get_active():
			align=2 # middle
		else:
			w=self.tree.get_object("menubottom")
			if w.get_active():
				align=1 # bottom
		global_vars["menu_alignment"]=align
		
		halign=0 # left
		w=self.tree.get_object("menucenter")
		if w.get_active():
			halign=2 # middle
		else:
			w=self.tree.get_object("menuright")
			if w.get_active():
				halign=1 # right
		global_vars["menu_halignment"]=halign
		
		w=self.tree.get_object("domenu")
		global_vars["do_menu"]=w.get_active()
		
		w=self.tree.get_object("menu_title_text")
		global_vars["menu_title_text"]=w.get_text()
		
		w=self.tree.get_object("menu_title_color")
		color=w.get_color()
		global_vars["menu_title_color"]=[color.red,color.green,color.blue,w.get_alpha()]
		
		w=self.tree.get_object("menu_title_shadow")
		color=w.get_color()
		global_vars["menu_title_shadow"]=[color.red,color.green,color.blue,w.get_alpha()]
		
		w=self.tree.get_object("menu_title_font")
		global_vars["menu_title_fontname"]=w.get_font_name()
		
		# repaint the used size
		self.callback()


class menu_preview:
	
	def menu_preview_expose(self,widget,event):

		""" Callback to repaint the menu preview window when it
			sends the EXPOSE event """

		if self.menu_preview==None:
			return
		cr=self.menu_preview.window.cairo_create()
		cr.set_source_surface(self.sf)
		cr.paint()
		   
	
	def __init__(self,gladefile,structure,global_vars):
		
		""" Shows a window with a preview of the disc menu """
		
		self.menu_preview=None
		if global_vars["PAL"]:
			newtree=devede_other.create_tree(self,"wmenu_preview_pal",gladefile)
			window=newtree.get_object("wmenu_preview_pal")
			self.menu_preview=newtree.get_object("preview_draw_pal")
		else:
			newtree=devede_other.create_tree(self,"wmenu_preview_ntsc",gladefile)
			window=newtree.get_object("wmenu_preview_ntsc")
			self.menu_preview=newtree.get_object("preview_draw_ntsc")
		print self.menu_preview

		if global_vars.has_key("install_path")==False:
			global_vars["install_path"]=None
		if global_vars.has_key("path")==False:
			global_vars["path"]=""
		if global_vars.has_key("menu_sound")==False:
			global_vars["menu_sound"]=""
		if global_vars.has_key("menu_sound_duration")==False:
			global_vars["menu_sound_duration"]=1
		clase=devede_xml_menu.xml_files(None,None,None,structure,global_vars,"","")
		self.sf=clase.create_menu_bg(0,0)

		if self.sf==None:
			devede_dialogs.show_error(gladefile,_("Can't find the menu background.\nCheck the menu options."))
		else:
			window.show()
			window.run()
			window.hide()
		window.destroy()
		window=None
