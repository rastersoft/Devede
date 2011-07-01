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
import gobject
import os
import sys

import devede_other
import devede_newfiles
import devede_dvdmenu
import devede_loadsave
import devede_title_properties
import devede_dialogs
import devede_convert
import devede_help
import devede_settings

if (sys.platform=="win32") or (sys.platform=="win64"):
	import win32api

class main_window:
	
	def __init__(self,global_vars,callback):
		
		self.global_vars=global_vars
		self.gladefile=global_vars["gladefile"]
		
		self.tree=devede_other.create_tree(self,"wmain",self.gladefile)
		self.window=self.tree.get_object("wmain")

		if (sys.platform=="win32") or (sys.platform=="win64"):
			self.window.drag_dest_set(0,[],0)
			self.window.connect('drag_drop', self.drop_cb)
		else:
			self.window.drag_dest_set(gtk.DEST_DEFAULT_MOTION | gtk.DEST_DEFAULT_HIGHLIGHT | gtk.DEST_DEFAULT_DROP,[ ( "text/plain", 0, 80), ( "video/*", 0, 81) ],gtk.gdk.ACTION_COPY)
		self.global_vars["main_window"]=self.window
		
		self.list_titles=gtk.TreeStore(gobject.TYPE_PYOBJECT,gobject.TYPE_STRING)
		self.list_chapters=gtk.TreeStore(gobject.TYPE_PYOBJECT,gobject.TYPE_STRING)
		
		ltitles=self.tree.get_object("ltitles")
		lchapters=self.tree.get_object("lchapters")
		
		ltitles.set_model(self.list_titles)
		lchapters.set_model(self.list_chapters)
		
		renderertitles=gtk.CellRendererText()
		columntitles = gtk.TreeViewColumn("Title", renderertitles, text=1)
		ltitles.append_column(columntitles)
		
		rendererchapters=gtk.CellRendererText()
		columnchapters = gtk.TreeViewColumn("Title", rendererchapters, text=1)
		lchapters.append_column(columnchapters)
		
		#ltitles.connect("button_release_event",self.on_titleclick)
		#lchapters.connect("button_release_event",self.on_chapterclick)
		
		self.set_default_global()
		
		self.callback=callback # callback to call to show again the SELECT_DISK dialog
		
		if global_vars["PAL"]:
			w=self.tree.get_object("default_pal")
			os.environ["VIDEO_FORMAT"]="PAL"
		else:
			w=self.tree.get_object("default_ntsc")
			os.environ["VIDEO_FORMAT"]="NTSC"
		w.set_active(True)
		
		self.window.show()


	def hide(self):
		if self.window!=None:
			self.window.hide()


	def show(self):
		if self.window!=None:
			self.window.show()


	def drop_cb(self, wid, context, x, y, time):
		# Used with windows drag and drop
		print 'drop'
		self.have_drag = False
		if context.targets:
			wid.drag_get_data(context, context.targets[0], time)
			return True
		return False


	def set_default_global(self):
		
		""" Sets the default GLOBAL vars each time the user wants to create a new disc """
		
		self.global_vars["action_todo"]=2
		self.global_vars["struct_name"]=""
		self.global_vars["do_menu"]=True
		self.global_vars["with_menu"]=True
		self.global_vars["menu_bg"]=os.path.join(self.global_vars["path"],"backgrounds","default_bg.png")
		self.global_vars["menu_sound"]=os.path.join(self.global_vars["path"],"silence.ogg")
		test=devede_newfiles.file_get_params()
		check,channels=test.read_file_values(self.global_vars["menu_sound"],True)
		if (check!=False) or (channels!=1):
			self.global_vars["menu_sound_duration"]=20
		else:
			self.global_vars["menu_sound_duration"]=test.length
		print "Longitud sonido: "+str(test.length)
		test=None
		self.global_vars["titlecounter"]=2
		self.current_title_selected=-1
		self.current_file_selected=-2
		self.global_vars["fontname"]="Sans 12"
		self.global_vars["menu_bgcolor"]=[0,0,0,49152]
		self.global_vars["menu_font_color"]=[65535,65535,65535,65535]
		self.global_vars["menu_selc_color"]=[0,65535,65535,65535]
		self.global_vars["menu_shadow_color"]=[0,0,0,0]
		self.global_vars["menu_alignment"]=2 # middle
		self.global_vars["menu_halignment"]=2 # center
		self.global_vars["menu_title_color"]=[0,0,0,65535]
		self.global_vars["menu_title_shadow"]=[0,0,0,0]
		self.global_vars["menu_title_text"]=""
		self.global_vars["menu_title_fontname"]="Sans 14"
		

	def set_disc_type(self,delete_structure):
		
		""" Changes the interface to adjust to the disk type """
		
		if delete_structure:
			self.structure=[]
			self.structure.append(self.create_new_structure(1))
			self.set_default_global()
		
		self.disctocreate = self.global_vars["disctocreate"]
		
		# choose the default disk type
		w = self.tree.get_object("dvdsize")
		if (self.disctocreate == "dvd") or (self.disctocreate == "divx"):
			w.set_active(4)
		else:
			w.set_active(2)
		
		w = self.tree.get_object("autosize")
		if (self.disctocreate == "vcd"):
			w.hide()
		else:
			w.show()
		
		w = self.tree.get_object("include_menu")
		if (self.disctocreate == "dvd"):
			w.show()
		else:
			w.hide()
		
		w1 = self.tree.get_object("frame1") # contains the titles
		w2 = self.tree.get_object("create_dvd") # toggle to create the DVD structure
		w5 = self.tree.get_object("menuoptions") # button to show the menu options
		w6 = self.tree.get_object("menu_preview") # button to preview the menu
		
		if self.disctocreate == "dvd":
			w1.show()
			w2.show()
			w5.show()
			w6.show()
		else:
			self.global_vars["do_menu"] = False
			w1.hide()
			w2.hide()
			w5.hide()
			w6.hide()
		
		w1 = self.tree.get_object("frame5") # ACTION frame
		w2 = self.tree.get_object("expander2")
		if self.disctocreate == "divx":
			w1.hide()
			self.global_vars["action_todo"]=0
			w = self.tree.get_object("only_convert")
			w.set_active(True)
			w2.hide()
		else:
			w1.show()
			if self.global_vars["action_todo"]==2:
				w=self.tree.get_object("create_iso")
			elif self.global_vars["action_todo"]==1:
				w=self.tree.get_object("create_dvd")
			else:
				w=self.tree.get_object("only_convert")
				self.global_vars["action_todo"]=0
			w.set_active(True)
			w2.show()
	
		# now select the first title and chapter
		
		ltitles=self.tree.get_object("ltitles")
		ltitles.get_selection().select_path( (0,))
		
		lchapters=self.tree.get_object("lchapters")
		lchapters.get_selection().select_path( (0,))
		
		# refresh the title and chapter lists		
		self.refresh_titles()
		self.refresh_chapters()
		
		# set the window title
		self.set_title()
		
		# and set the buttons'status
		self.set_buttons()
		

	def get_surface(self,element):
		
		""" Return data from a video, to be able to compute the optimal bitrate to fullfill the disk.
			SIZE is the size in kbytes
			SURFACE is the surface in square pixels
			LENGTH is the efective length in seconds
			AUDIORATE is the audio rate """
		
		length = float(element["olength"])
		speed1,speed2=devede_other.get_speedup(element)
		if (speed1!=speed2): # we are speeding up the film, so we must take it into account
			length*=((float(speed2))/(float(speed1)))

		if element["cutting"]!=0: # we want only half the file
			length/=2

		surface = float(element["width"]*element["height"])
		
		surface/=84480.0 # normalize surface respect to 352x240
		
		if (element["copy_audio"]):
			audiorate=element["oarate"]
		else:
			audiorate=element["arate"]

		if (element["ismpeg"]):
			size=element["filesize"]/1000
		else:
			size=(length*(element["vrate"]+audiorate))/8

		return size,surface,length,audiorate
	

	# Callbacks

	def on_autosize_clicked(self,widget):
		
		""" Adjust the videorate of each file to ensure that the disk usage is optimal """
		
		fixed_size=[]
		variable_size=[]
		
		# First, set the non-adjustable bitrate videos in a different list
		
		for element in self.structure:
			for element2 in element[1:]:
				if (element2["ismpeg"]) or (element2["isvob"]):
					fixed_size.append(element2)
				else:
					variable_size.append(element2)
		
		discsize,minrate,maxrate=devede_other.get_dvd_size(self.tree,self.disctocreate)	
		discsize*=1000 # size in kbytes
		# remove the space needed by menus
		discsize-=devede_other.calcule_menu_size(self.structure,self.global_vars["menu_sound_duration"])
		
		size_error=False
		dowhile=True
		while(dowhile):
			dowhile=False
			v_fixed_size=0
			for element in fixed_size:
				size,surface,length,arate = self.get_surface(element)
				subrate=8*len(element["sub_list"])
				v_fixed_size+=size+int((subrate*element["olength"])/8)

			available_size=discsize-v_fixed_size
				
			if (available_size<0): # the fixed_size videos need more disk space than the currently available
				size_error=True
				break
			
			if (len(variable_size)==0):
				break
			
			total_len=0.0
			total_surface=0.0
			for element in variable_size:
				size,surface,length,arate = self.get_surface(element)
				total_len+=length
				total_surface+=surface*length
				
			for element in variable_size:
				subrate=8*len(element["sub_list"])
				size,surface,length,arate = self.get_surface(element)
				videorate=8*(float(available_size))*((surface*length)/total_surface)
				videorate/=length
				videorate-=(arate+subrate)
				element["vrate"]=int(videorate)
				print int(videorate)
				if videorate<minrate:
					element["vrate"]=minrate
					dowhile=True
					fixed_size.append(element)
					variable_size.remove(element)
					break
				if videorate>maxrate:
					element["vrate"]=maxrate
					dowhile=True
					fixed_size.append(element)
					variable_size.remove(element)
					break

		if size_error:
			devede_dialogs.show_error(self.gladefile,_("Too many videos for this disc size.\nPlease, select a bigger disc type or remove some videos."))
		
		self.set_video_values()


	def wmain_delete_event_cb(self,widget,signal):
	
		""" Delete callback for main window """
	
		self.on_main_cancel_clicked(widget)
		return True
	
	
	def on_main_cancel_clicked(self,widget):
	
		""" Callback for Exit button (in main window) and Quit menu item,
			where it shows the "Are you sure?" window """
	
		window=devede_dialogs.ask_exit(self.gladefile)
		retval=window.run()
		window=None
		if retval==-5:
			gtk.main_quit()
		return
	

	def draganddrop(self,widget,drag_context, x, y, selection, info, time):
	
		""" Manages the Drag&Drop in the main window """
		
		converter=devede_newfiles.newfile(self.global_vars["PAL"],self.disctocreate)
		
		list=converter.split_dnd(selection.data)
		
		if (len(list)==1): # check if it's a configuration file
			filename=list[0].lower()
			if len(filename)>6:
				if filename[-7:]==".devede":
					self.on_devede_open_activate(None, list[0])
					return
		
		fine=True
		list2=[]
		for element in list:
			done,audio=converter.create_default_video_parameters(element) # check if files are videos
			print done
			print audio
			if (done==False):
				fine=False
				break
			list2.append(converter.file_properties)
		
		if fine:
			title,chapter=self.get_marked()
			element=self.structure[title]
			for element2 in list2:
				element.append(element2)
			self.refresh_chapters()
			self.set_buttons()
		else:
			error=devede_dialogs.show_error(self.gladefile,_("Some files weren't video files.\nNone added."))
			error=None
	
	
	def on_default_pal_toggled(self,widget):
		
		if widget.get_active():
			self.global_vars["PAL"]=True
			os.environ["VIDEO_FORMAT"]="PAL"
		else:
			self.global_vars["PAL"]=False
			os.environ["VIDEO_FORMAT"]="NTSC"
		print "PAL: "+str(self.global_vars["PAL"])
	
	
	def on_chapterclick(self,widget,event,step=None):
	
		""" Callback for click event in the chapter list. It
		sets the buttons and film info """
	
		self.set_buttons()
	
	
	def on_dvdsize_changed(self,widget):

		""" This function is called when the user changes the media size """

		self.set_video_values()
	
	
	def on_include_menu_toggled(self,widget):
		
		w1=self.tree.get_object("menuoptions")
		w2=self.tree.get_object("menu_preview")
		status=widget.get_active()
		w1.set_sensitive(status)
		w2.set_sensitive(status)
		self.global_vars["with_menu"]=status
	
	
	def on_main_go_clicked(self,widget):

		total=0
		for title in self.structure:
			total+=len(title)-1
	
		maxtitles=devede_other.get_max_titles(self.disctocreate)
		if total>maxtitles:
			devede_dialogs.show_error(self.gladefile,(_("Your project contains %(X)d movie files, but the maximum is %(MAX)d. Please, remove some files and try again.")) % {"X":total , "MAX":maxtitles})
			return
	
		actions=0	
		w=self.tree.get_object("only_convert")
		if w.get_active():
			actions=1
		else:
			w=self.tree.get_object("create_dvd")
			if (w.get_active()) or ((self.disctocreate!="dvd") and (self.disctocreate!="divx")):
				actions=2
			else:
				actions=3
	
		self.global_vars["number_actions"]=actions
		
		self.global_vars["erase_temporary_files"]=self.global_vars["erase_files"]
		
		print "Threads: "+str(self.global_vars["multicore"])
		conversor=devede_convert.create_all(self.gladefile,self.structure,self.global_vars,self.callback2)
		if conversor.create_disc():
			self.window.hide()
	
	
	# titles-related callbacks
	
	
	def on_titleclick(self,widget,event,step=None):
	
		""" Callback for click event in the title list. It refreshes the chapters
		and sets the buttons and film info """
	
		self.refresh_chapters()
		self.set_buttons()
	
	
	def on_add_title_clicked(self,widget):

		""" Callback for "Add title" button. It adds a new title and
		refreshes the list of titles """
	
		self.structure.append(self.create_new_structure(self.global_vars["titlecounter"]))
		self.global_vars["titlecounter"]+=1
		self.current_title_selected=10000 # to ensure that we select the newly created
		self.refresh_titles()
		self.refresh_chapters()
		self.set_buttons()
	
	
	def on_del_title_clicked(self,widget):
	
		""" Callback for "Delete title" button. It asks the user if
		is sure """
	
		title,chapter=self.get_marked()
		window=devede_dialogs.ask_delete_title(self.structure[title][0]["nombre"],self.gladefile)
		retval=window.run()
		window=None
		if retval==-6:
			return
		title,chapter=self.get_marked()
		self.structure.pop(title)
		self.refresh_titles()
		self.refresh_chapters()
		self.set_buttons()
	
	
	def on_titleup_clicked(self,widget):

		""" Moves a title up in the list """
	
		title,chapter=self.get_marked()
		
		temp=self.structure[title-1]
		self.structure[title-1]=self.structure[title]
		self.structure[title]=temp
		
		self.current_title_selected-=1
		self.refresh_titles()
		self.refresh_chapters()
		self.set_buttons()
	
	
	def on_titledown_clicked(self,widget):
	
		""" Moves a title down in the list """
	
		title,chapter=self.get_marked()
		
		temp=self.structure[title+1]
		self.structure[title+1]=self.structure[title]
		self.structure[title]=temp
		self.current_title_selected+=1
		self.refresh_titles()
		self.refresh_chapters()
		self.set_buttons()
	
	
	def on_prop_titles_clicked(self,widget):
	
		title,chapter=self.get_marked()
		w = devede_title_properties.title_properties(self.gladefile,self.structure,title)
		w = None
		self.refresh_titles()
		self.refresh_chapters()
	
	
	# chapter-related callbacks


	def on_add_chapter_clicked(self,widget):
	
		""" Callback for the "Add chapter" button """
	
		title,chapter=self.get_marked()
		window=devede_newfiles.file_properties(self.global_vars,title,-1,self.structure,self.refresh_all)
		
	
	def on_prop_chapter_clicked(self,widget):
	
		""" Callback for the "Modify chapter" button """
	
		title,chapter=self.get_marked()
		window=devede_newfiles.file_properties(self.global_vars,title,chapter,self.structure,self.refresh_all)


	def on_del_chapter_clicked(self,widget):
		
		title,chapter=self.get_marked()
				
		w=devede_dialogs.ask_delete_chapter(self.structure[title][chapter]["filename"],self.gladefile)
		retval=w.run()
		w=None
		if retval!=-5:
			return
		
		self.structure[title].pop(chapter)
	
		self.refresh_chapters()
		self.set_buttons()


	def on_main_preview_clicked(self,widget):
	
		title,chapter=self.get_marked()
		self.global_vars["erase_temporary_files"]=True
		self.global_vars["number_actions"]=1
		tmp_structure=[["",self.structure[title][chapter]]]
		converter=devede_convert.create_all(self.gladefile,tmp_structure,self.global_vars,self.callback3)
		converter.preview(self.global_vars["temp_folder"])


	def callback3(self):
		
		""" This method is called after a preview """
		
		return None # do nothing


	def on_filesup_clicked(self,widget):

		""" Moves a chapter up in the list """
	
		title,chapter=self.get_marked()
		
		temp=self.structure[title][chapter-1]
		self.structure[title][chapter-1]=self.structure[title][chapter]
		self.structure[title][chapter]=temp
		self.current_file_selected-=1
		self.refresh_chapters()
		self.set_buttons()


	def on_filesdown_clicked(self,widget):

		""" Moves a chapter down in the list """
	
		title,chapter=self.get_marked()
		
		temp=self.structure[title][chapter+1]
		self.structure[title][chapter+1]=self.structure[title][chapter]
		self.structure[title][chapter]=temp
		self.current_file_selected+=1
		self.refresh_chapters()
		self.set_buttons()

	
	# dvd-menu-related callbacks	
	
	def on_menu_preview_clicked(self,widget):
	
		window=devede_dvdmenu.menu_preview(self.gladefile,self.structure,self.global_vars)
		window=None

	
	def on_menuoptions_clicked(self,widget):
	
		window=devede_dvdmenu.menu_options(self.gladefile,self.structure,self.global_vars,self.set_video_values)
		window=None
	

	# Main menu callbacks
	
	def on_devede_about_activate(self,widget):
		
		window=devede_dialogs.show_about(self.gladefile)
		window=None
	
	
	def on_devede_new_activate(self,widget):
	
		""" Callback for NEW menu item,	where it asks for confirmation """
		
		print self.structure
		w = devede_dialogs.ask_erase_all(self.gladefile)
		retval=w.run()
		w = None
		if retval==-5:
			(self.callback)()

	
	def on_devede_open_activate(self,widget,filename=None):
		
		""" Callback for OPEN menu item """
		
		load = devede_loadsave.load_save_config(self.gladefile,self.structure,self.global_vars,self.tree)
		load.load(filename)
		if load.done==False:
			load=None
			return
		
		self.set_disc_type(False)
		self.refresh_titles()
		self.refresh_chapters()
		self.set_buttons()
		self.set_title()
		if self.global_vars["PAL"]:
			w=self.tree.get_object("default_pal")
			os.environ["VIDEO_FORMAT"]="PAL"
		else:
			w=self.tree.get_object("default_ntsc")
			os.environ["VIDEO_FORMAT"]="NTSC"
		w.set_active(True)
		
		w=self.tree.get_object("include_menu")
		print"Con menu: "+str(self.global_vars["with_menu"])
		w.set_active(self.global_vars["with_menu"])
		load=None

	
	def on_devede_save_activate(self,widget):
		
		self.save_file(False)


	def on_devede_saveas_activate(self,widget):
		
		self.save_file(True)

	
	def on_main_help_clicked(self,widget):
		
		help_class=devede_help.show_help(self.gladefile,self.global_vars["help_path"],"main.html")
	
	
	def on_help_index_activate(self,widget):
	
		help_class=devede_help.show_help(self.gladefile,self.global_vars["help_path"],"index.html")
	
	
	def on_devede_settings_activate(self,widget):
		
		settings=devede_settings.devede_settings(self.gladefile,self.structure,self.global_vars)
	
	
	# help methods

	def callback2(self):
		
		""" This method is called when the conversion ends """
		
		self.window.show()


	def refresh_all(self):
		
		self.refresh_chapters()
		self.set_buttons()


	def save_file(self,mode):
		
		""" Saves the current structure """
		
		save=devede_loadsave.load_save_config(self.gladefile,self.structure,self.global_vars,self.tree)
		save.save(mode)
		self.set_title()
		save=None


	def get_marked(self):
	
		""" Returns the title and chapter currently marked in the main window """
	
		ltitles=self.tree.get_object("ltitles")
		lchapters=self.tree.get_object("lchapters")
	
		try:
			ctree,iter=ltitles.get_selection().get_selected()
			title=ctree.get_value(iter,0)
		except:
			title=-1
			
		try:
			ctree,iter=lchapters.get_selection().get_selected()
			chapter=1+ctree.get_value(iter,0) # zero is the Title value
		except:
			chapter=-1
		
		self.current_title_selected=title
		self.current_file_selected=chapter
		
		return title,chapter


	def set_buttons(self):
	
		""" Enables or disables the button to create a DVD, and the
		buttons to move up or down a title or chapter """
	
		title,chapter=self.get_marked()
			
		if title==-1:
			title_marked=False
		else:
			title_marked=True
	
		title_up=self.tree.get_object("titleup")
		if title==0:
			title_up.set_sensitive(False)
		else:
			title_up.set_sensitive(True)
		
		title_down=self.tree.get_object("titledown")
		if (title+1)==len(self.structure):
			title_down.set_sensitive(False)
		else:
			title_down.set_sensitive(True)
	
		if chapter==-1:
			chapter_marked=False
		else:
			chapter_marked=True
	
		files_up=self.tree.get_object("filesup")
		if chapter<2:
			files_up.set_sensitive(False)
		else:
			files_up.set_sensitive(True)
		
		files_down=self.tree.get_object("filesdown")
		if (chapter==-1) or (chapter+1==len(self.structure[title])):
			files_down.set_sensitive(False)
		else:
			files_down.set_sensitive(True)
	
		del_title=self.tree.get_object("del_title")
		if len(self.structure)>1:
			del_title.set_sensitive(title_marked)	
		else:
			del_title.set_sensitive(False)
		
		add_title=self.tree.get_object("add_title")
		if (len(self.structure)<61):
			add_title.set_sensitive(True)
		else:
			add_title.set_sensitive(False)
		
		add_chapter=self.tree.get_object("add_chapter")
		add_chapter.set_sensitive(title_marked)
		
		del_chapter=self.tree.get_object("del_chapter")
		del_chapter.set_sensitive(chapter_marked)
		
		main_preview=self.tree.get_object("main_preview")
		main_preview.set_sensitive(chapter_marked)
		
		prop_chapter=self.tree.get_object("prop_chapter")
		prop_chapter.set_sensitive(chapter_marked)
		
		value=False
		for element in self.structure:
			if len(element)>1:
				value=True
				break
	
		main_go=self.tree.get_object("main_go")
		main_go.set_sensitive(value)
		self.set_video_values()


	def set_video_values(self):
	
		""" Sets the video values in the main window when the user clicks
		a chapter """
	
		title,chapter=self.get_marked()
		if (chapter!=-1) and (title!=-1) and (title<len(self.structure)) and (chapter<len(self.structure[title])):
			found2=self.structure[title]
			found=found2[chapter]
			
			w=self.tree.get_object("oaspect")
			if (found["aspect"])>1.5:
				w.set_text("16:9")
			else:
				w.set_text("4:3")
				
			w=self.tree.get_object("o_size")
			w.set_text(str(found["owidth"])+"x"+str(found["oheight"]))
			
			w=self.tree.get_object("leng")
			w.set_text(str(found["olength"]))
			
			w=self.tree.get_object("vrate")
			w.set_text(str(found["vrate"]))
			
			w=self.tree.get_object("arate")
			w.set_text(str(found["arate"]))
			
			w=self.tree.get_object("eleng")
			speed1,speed2=devede_other.get_speedup(found)
			length=devede_other.calcula_tamano_parcial(found["vrate"],found["arate"],found["filesize"],found["olength"],len(found["sub_list"]),found["ismpeg"],found["isvob"],found["cutting"],speed1,speed2)
			#length=int(((found["vrate"]+found["arate"])*found["olength"])/8000)
			w.set_text(str(int(length/1000)))
			
			w=self.tree.get_object("achap")
			if found["lchapters"]==0:
				w.set_text(_("no chapters"))
			else:
				w.set_text(str(int(found["lchapters"])))
			
			w=self.tree.get_object("video_format")
			if found["fps"]==25:
				w.set_text("25 (PAL)")
			elif found["fps"]==30:
				if (found["ofps"]==24) and (self.disctocreate!="vcd") and (self.disctocreate!="svcd") and (self.disctocreate!="cvd"):
					w.set_text("24 (NTSC)")
				else:
					w.set_text("30 (NTSC)")
			else:
				w.set_text(str(int(found["fps"])))
			
			w=self.tree.get_object("fsizem")
			w.set_text(str(found["width"])+"x"+str(found["height"]))

		else:

			w=self.tree.get_object("oaspect")
			w.set_text("")
			w=self.tree.get_object("o_size")
			w.set_text("")
			w=self.tree.get_object("leng")
			w.set_text("")
			w=self.tree.get_object("vrate")
			w.set_text("")
			w=self.tree.get_object("arate")
			w.set_text("")
			w=self.tree.get_object("eleng")
			w.set_text("")
			w=self.tree.get_object("achap")
			w.set_text("")
			w=self.tree.get_object("video_format")
			w.set_text("")
			w=self.tree.get_object("fsizem")
			w.set_text("")
			
		total=devede_other.calcula_tamano_total(self.structure,self.global_vars["menu_sound_duration"],self.disctocreate)
		total/=1000
		
		tamano,minvrate,maxvrate = devede_other.get_dvd_size(self.tree,self.disctocreate)
		
		w=self.tree.get_object("usage")
		if total>tamano:
			w.set_fraction(1.0)
			addv=1
		else:
			w.set_fraction(total/tamano)
			addv=0
		w.set_text(str(addv+int((total/tamano)*100))+"%")


	def set_title(self):
		
		""" Sets the window's title, with the current structure name if saved """
		
		name=os.path.basename(str(self.global_vars["struct_name"]))
		if name=="":
			name=_("Unsaved disc structure")
		self.window.set_title(name+' - DeVeDe')


	def refresh_titles(self):
	
		""" Refreshes the title list """
	
		self.current_file_selected=-1
		
		self.list_titles.clear()
		self.list_chapters.clear()
			
		counter=-1
		for element in self.structure:
			counter+=1
			entry=self.list_titles.insert_before(None,None)
			self.list_titles.set_value(entry,1,element[0]["nombre"])
			self.list_titles.set_value(entry,0,counter)
		
		if counter<self.current_title_selected:
			self.current_title_selected=counter
		
		if self.current_title_selected<0:
			self.current_title_selected=0
	
		ltitles=self.tree.get_object("ltitles")
		ltitles.get_selection().select_path((self.current_title_selected,))

	
	def refresh_chapters(self):
	
		""" Refreshes the chapter list """
	
		file=self.current_file_selected
		title,file2=self.get_marked()
		
		if (title==-1):
			return
		
		if (self.current_file_selected==-1):
			self.current_file_selected=1
		else:
			self.current_file_selected=file
		
		self.list_chapters.clear()
		
		list=self.structure[title]
	
		if len(list)<=1:
			return
			
		counter=0
		for element in list[1:]:
			entry=self.list_chapters.insert_before(None,None)
			self.list_chapters.set_value(entry,1,element["filename"])
			self.list_chapters.set_value(entry,0,counter)
			counter+=1
		
		if counter<self.current_file_selected:
			self.current_file_selected=counter
		
		lchapters=self.tree.get_object("lchapters")
		lchapters.get_selection().select_path( (self.current_file_selected-1,))

		
	def create_new_structure(self,number):
	
		name=_("Title %(X)d") % {"X":int(number)}
		var={}
		var["nombre"]=name
		var["jumpto"]="menu" # can be MENU, FIRST, NEXT, LAST or LOOP
		return [var]
