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

import os
import stat

import pygtk # for testing GTK version number
pygtk.require ('2.0')
import gtk
import gobject
import sys
import gc
import copy
import time

import devede_other
import devede_executor
import devede_convert
import devede_dialogs
import devede_help
import math

# How to add new file options:

# In the class NEWFILE, method CREATE_DEFAULT_VIDEO_PARAMETERS, add the new option
# to the SELF.FILE_PROPERTIES dictionary, setting its default value based in the
# SELF.FILE_VALUES values (the ones obtained with MPLAYER --IDENTIFY), SELF.PAL (True
# for PAL output video, False for NTSC output video) and SELF.DISCTOCREATE (DVD, VCD, SVCD
# CVD or DIVX)

# In the class FILE_PROPERTIES

# In the method GET_WIDGETS, set the parameter value in the SELF.FILE_PROPERTIES
# dictionary using the widget's current value

# In the method SET_WIDGETS, set the widget's value using the parameter value in
# SELF.FILE_PROPERTIES

# If the widget must be disabled or enabled under some circumstances (other widgets)
# set that code in method SET_FILM_BUTTONS
#
# Finally, add the needed code in DEVEDE_LOADSAVE.PY to ensure that old project files
# work fine with the new options

class file_get_params(devede_executor.executor):


	def read_file_values(self,filename,check_audio):

		""" Reads the values of the video (width, heigth, fps...) and stores them
			into file_values.
		
		 	Returns (False,AUDIO) if the file is not a video (with AUDIO the number
		 	of audio tracks)
		 	
		 	Returns (True,0) if the file is a right video file """
		
		handler=''

		vrate=0
		arate=0
		width=0
		height=0
		fps=0
		length=0
		audio=0
		video=0
		audiorate=0
		aspect_ratio=1.3333333333
		self.length=0

		# if CHECK_AUDIO is TRUE, we just check if it's an audio file

		if check_audio:
			nframes=0
		else:
			nframes=1

		if (sys.platform=="win32") or (sys.platform=="win64"):
			command="mplayer.exe"
		else:
			command="mplayer"
		launcher=[command, "-loop","1","-identify", "-ao", "null", "-vo", "null", "-frames", str(nframes), filename]
		handler=self.launch_program(launcher, win32arg=False,with_stderr=False)

		minimum_audio=10000
		audio_list=[]
		while True:
			linea=handler.stdout.readline()
			linea=self.remove_ansi(linea)
			if linea=="":
				break
			position=linea.find("ID_")
			if position==-1:
				continue
			linea=linea[position:]
			if linea[:16]=="ID_VIDEO_BITRATE":
				vrate=int(linea[17:])
			if linea[:14]=="ID_VIDEO_WIDTH":
				width=int(linea[15:])
			if linea[:15]=="ID_VIDEO_HEIGHT":
				height=int(linea[16:])
			if linea[:15]=="ID_VIDEO_ASPECT":
				aspect_ratio=float(linea[16:])
			if linea[:12]=="ID_VIDEO_FPS":
				fps2=linea[13:]
				while ord(fps2[-1])<32:
					fps2=fps2[:-1]
				posic=linea.find(".")
				if posic==-1:
					fps=int(linea[13:])
				else:
					fps=int(linea[13:posic])
					if linea[posic+1]=="9":
						fps+=1
			if linea[:16]=="ID_AUDIO_BITRATE":
				arate=int(linea[17:])
			if linea[:13]=="ID_AUDIO_RATE":
				audiorate=int(linea[14:])
			if linea[:9]=="ID_LENGTH":
				length=int(float(linea[10:]))
			if linea[:11]=="ID_VIDEO_ID":
				video+=1
			if linea[:11]=="ID_AUDIO_ID":
				audio+=1
				audio_track=int(linea[12:])
				if minimum_audio>audio_track:
					minimum_audio=audio_track
				audio_list.append(audio_track)
				
		handler.wait()
		
		if (video==0) or (width==0) or (height==0):
			if (audio!=0):
				self.length=length
				self.audio=audio
			return False,audio
		
		if aspect_ratio==0.0 or math.isnan(aspect_ratio) :
			aspect_ratio=(float(width))/(float(height))
			if aspect_ratio<=1.5:
				aspect_ratio=(4.0/3.0)
		
		self.file_values={}
		self.file_values["vrate"]=vrate
		self.file_values["arate"]=arate
		self.file_values["video_streams"]=video
		self.file_values["audio_streams"]=audio
		self.file_values["width"]=width
		self.file_values["height"]=height
		self.file_values["fps"]=fps
		self.file_values["ofps2"]=fps2
		self.file_values["length"]=length
		self.file_values["aspect_ratio"]=aspect_ratio
		self.file_values["audiorate"]=audiorate
		self.file_values["audio_list"]=audio_list
		self.file_values["audio_stream"]=minimum_audio
		
		return True,0

class newfile(file_get_params):
	
	def __init__(self,pal,disctocreate):
		""" This class manages every new film added. It reads its parameters (resolution, FPS, number of
		channels...) and allows to generate the default values, both when choosing manually a file from the
		Properties window, or when dragging&dropping them into the main window """
		
		self.pal=pal
		self.disctocreate=disctocreate
		self.file_values=None
		self.file_properties=None

		
	def get_recomended_resolution(self,vrate,arate,desired_resolution):

		""" Returns the recomended resolution for a video based in its original
			resolution and the resolution chosed by the user.
		
		 	DESIRED_RESOLUTION is a value from 0 to 7:
		 	0=auto, 1=720x480, 2=704x480, 3=480x480, 4=352x480, 5=352x240
		 	6=1280x720, 7=1920x1080, 8 160x128
		 	
		 	It returns the recomended audio and video rate for that resolution,
		 	but only if the user hasn't changed them """

		if self.pal:
			nheigh1=576
			nheigh2=288
		else:
			nheigh1=480
			nheigh2=240

		if self.file_values==None:
			return 0,0,False,0,0

		if desired_resolution==0: # default resolution; we have to take the most similar resolution
			if self.disctocreate=="vcd":
				resx=352
				resy=nheigh2
			elif self.disctocreate=="cvd":
				resx=352
				resy=nheigh1
			elif self.disctocreate=="svcd":
				resx=480
				resy=nheigh1
			else: # dvd o divx
				if self.file_values["width"]<=352:
					resx=352
					if self.file_values["height"]<=nheigh2:
						resy=nheigh2
					else:
						resy=nheigh1
				else:
					resx=720
					resy=nheigh1
		elif desired_resolution==1:
			resx=720
			resy=nheigh1
		elif desired_resolution==2:
			resx=704
			resy=nheigh1
		elif desired_resolution==3:
			resx=480
			resy=nheigh1
		elif desired_resolution==4:
			resx=352
			resy=nheigh1
		elif desired_resolution==5:
			resx=352
			resy=nheigh2
		elif desired_resolution==6:
			resx=1280
			resy=720
		elif desired_resolution==7:
			resx=1920
			resy=1080
		elif desired_resolution==8:
			resx=160
			resy=128
	
		if (((resx==720) and (resy==nheigh1)) or ((self.disctocreate=="divx") and (desired_resolution!=8))) and (self.file_values["aspect_ratio"]>=1.77):
			use_widescreen=True
		else:
			use_widescreen=False

		if (vrate==5001) or (vrate==3001) or (vrate==2001):
			if (resx>703):
				vrate=5001
			if (resx==480) or ((resx==352) and (resy==nheigh1)):
				vrate=3001
			if (resx==352) and (resy==nheigh2):
				vrate=2001
			if (self.disctocreate!="dvd") and (self.disctocreate!="divx"):
				vrate=2001
		
		if self.disctocreate=="vcd":
			vrate=1152
			arate=224

		return resx,resy,use_widescreen,vrate,arate


	def create_default_video_parameters(self,filename):

		""" This method fills the FILE_PROPERTIES property with the default values for the file.
			It returns False if the file isn't a valid video. The tuple contains the number of sound
			tracks found, so if it's different from 0, its an audio-only file. """

		if filename==None:
			return False,0

		isvideo,audio_tracks=self.read_file_values(filename,True)
		if isvideo==False:
			return False,audio_tracks
		isvideo,audio_tracks=self.read_file_values(filename,False) # get all the values in FILE_VALUES

		while filename[-1]==os.sep:
			filename=filename[:-1]
	
		nombre=filename
		while True: # get the filename without the path
			posic=nombre.find(os.path.sep)
			if posic==-1:
				break
			else:
				nombre=nombre[posic+1:]
	
		# filename[0]; path[1]; width[2]; heigh[3]; length[4] (seconds); original fps[5];
		# original videorate["oarate"]; original audiorate[7];
		# final videorate[8]; final arate[9]; final width[10]; final heigh[11];
		# 0=Black bars, 1=Scale picture [12];
		# length of chapters[13]; audio delay["fps"]; final fps["arateunc"]; original audio rate (uncompressed)["oaspect"];
		# original aspect ratio[17]; final aspect ratio[18];
		# 0=full length, 1=first half, 2=second half [19];
		# Resolution: 0=auto, 1=720x480, 2=704x480, 3=480x480, 4=352x480, 5=352x240, 6=1280x720, 7=1920x1080 [20]
		# extra parameters [21]

		self.file_properties={}
		self.file_properties["filename"]=nombre # filename without path
		self.file_properties["path"]=filename # file with complete path
		self.file_properties["owidth"]=self.file_values["width"] # original width
		self.file_properties["oheight"]=self.file_values["height"] # original height
		self.file_properties["olength"]=self.file_values["length"] # original length (in seconds)
		self.file_properties["ovrate"]=self.file_values["vrate"]/1000 # original videorate (in kbytes/second)
		self.file_properties["oarate"]=self.file_values["arate"]/1000 # original audiorate (in kbytes/second)
		self.file_properties["arateunc"]=self.file_values["audiorate"] # original uncompressed audiorate
		self.file_properties["oaspect"]=self.file_values["aspect_ratio"] # original aspect ratio
		self.file_properties["audio_list"]=self.file_values["audio_list"][:]
		self.file_properties["audio_stream"]=self.file_values["audio_stream"]
		
		if self.pal:
			self.file_properties["fps"]=25
		else:
			self.file_properties["fps"]=30

		self.file_properties["ofps"]=self.file_values["fps"]
		self.file_properties["ofps2"]=self.file_values["ofps2"]
		
		self.file_properties["blackbars"]=0 # black bars, no scale
		self.file_properties["lchapters"]=5
		self.file_properties["adelay"]=0 # no audio delay
		self.file_properties["cutting"]=0 # full length
		self.file_properties["resolution"]=0 # output resolution = auto
		self.file_properties["params"]="" # no mencoder extra parameters
		self.file_properties["params_vf"]="" # no mencoder extra VF parameters
		self.file_properties["params_lavc"]="" # no mencoder extra LAVC parameters
		self.file_properties["params_lame"]="" # no mencoder extra LAME parameters
		self.file_properties["ismpeg"]=False # is already an MPEG-2 compliant file
		self.file_properties["copy_audio"]=False # recompress the audio
		self.file_properties["isvob"]=False # recompress both audio and video
		self.file_properties["swap_fields"]=False # swap fields in interlaced videos
		self.file_properties["subfont_size"]=28 # subtitle font size
		self.file_properties["sound51"]=False # don't use 5.1 sound
		self.file_properties["gop12"]=True # GOP of 12 by default to increase compatibility
		self.file_properties["filesize"]=os.stat(filename)[stat.ST_SIZE] # file size
		self.file_properties["trellis"]=True # use trellis
		self.file_properties["twopass"]=False # two pass encoding
		self.file_properties["turbo1stpass"]=False # use turbo 1st pass on two pass encoding
		self.file_properties["mbd"]=2 # maximum quality
		self.file_properties["deinterlace"]="none" # don't deinterlace
		self.file_properties["sub_list"]=[]
		self.file_properties["force_subs"]=False

		resx,resy,use_widescreen,vrate,arate=self.get_recomended_resolution(5001, 224, 0)
		self.file_properties["width"]=resx
		self.file_properties["height"]=resy
		self.file_properties["vrate"]=vrate
		self.file_properties["arate"]=arate
		
		self.file_properties["rotate"]=0 # no rotation
		self.file_properties["hmirror"]=False
		self.file_properties["vmirror"]=False

		if use_widescreen:
			self.file_properties["aspect"]=1.7777777
		else:
			self.file_properties["aspect"]=1.3333333
			
		self.file_properties["volume"]=100
			
		return True,audio_tracks


	def split_dnd(self,data):

		""" Takes the list of files dragged into the window and returns them in a list """

		lista=[]
		item=""
		tempo=""
		mode=0
		
		if (sys.platform=="win32") or (sys.platform=="win64"):
			length=8
		else:
			length=7
		
		cadena2=""
		for elemento in data:
			if (ord(elemento)<32):
				cadena2+="\n"
			else:
				cadena2+=elemento
		
		while(True):
			pos=cadena2.find("file:///")
			if (pos==-1):
				break
			pos2=cadena2.find("\n",pos)
			if (pos2==-1):
				cadena=cadena2[pos+length:]
				cadena2=""
			else:
				cadena=cadena2[pos+length:pos2]
				cadena2=cadena2[pos2:]
			while (True):
				pos=cadena.find("%")
				if (pos==-1):
					break
				cadena=cadena[:pos]+chr(int(cadena[pos+1:pos+3],16))+cadena[pos+3:]
			lista.append(cadena)
		
		
		print "Dragged files: "+str(lista)
		return lista


##################################################################################


class file_properties(newfile):

	""" This class manages the properties window, where the user can choose the properties
		of each video file """
	
	def motion_cb(self,wid, context, x, y, time):
		context.drag_status(gtk.gdk.ACTION_COPY, time)
		return True
	
	def drop_cb(self, wid, context, x, y, time):
		# Used with windows drag and drop
		print 'drop'
		self.have_drag = False
		if context.targets:
			wid.drag_get_data(context, context.targets[0], time)
			return True
		return False
	
	# public methods	
	
	def __init__(self,global_vars,title,chapter,structure,callback_refresh):
		
		newfile.__init__(self,global_vars["PAL"],global_vars["disctocreate"])
		self.gladefile=global_vars["gladefile"]
		self.global_vars=global_vars
		self.title=title
		self.chapter=chapter
		self.structure=structure
		self.callback_refresh=callback_refresh
		
		self.tree=devede_other.create_tree(self,"wfile",self.gladefile)
		self.window=self.tree.get_object("wfile")
		self.window.show()
		self.window.drag_dest_set(0,[],0)
		self.window.connect('drag_drop', self.drop_cb)
		self.window.connect('drag_motion', self.motion_cb)

		w = self.tree.get_object("expander_advanced")
		w.set_expanded(self.global_vars["expand_advanced"])
		
		if global_vars["PAL"]:
			w=self.tree.get_object("video_pal")
		else:
			w=self.tree.get_object("video_ntsc")
		w.set_active(True)
		
		# Model and view for subtitles
		# first element: position
		# second: filename
		# third: codepage
		
		self.sub_model=gtk.ListStore(gobject.TYPE_INT, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)
		self.sub_tree=self.tree.get_object("sub_treeview")
		self.sub_tree.set_model(self.sub_model)
		render1=gtk.CellRendererText()
		column1=gtk.TreeViewColumn(_("Subtitle"),render1,text=1)
		self.sub_tree.append_column(column1)
		render2=gtk.CellRendererText()
		column2=gtk.TreeViewColumn(_("Codepage"),render2,text=2)
		self.sub_tree.append_column(column2)
		render3=gtk.CellRendererText()
		column3=gtk.TreeViewColumn(_("Language"),render3,text=3)
		self.sub_tree.append_column(column3)
		
		# Model and view for audio tracks
		
		self.audio_model=gtk.ListStore(gobject.TYPE_STRING)
		self.audio_view=self.tree.get_object("audiotrack")
		self.audio_view.set_model(self.audio_model)
		audiorender=gtk.CellRendererText()
		self.audio_view.pack_start(audiorender,True)
		self.audio_view.add_attribute(audiorender,"text",0)
		
		w1 = self.tree.get_object("subtitles_label")
		w2 = self.tree.get_object("frame_special")
		w3 = self.tree.get_object("gop12")
		w4 = self.tree.get_object("res1280x720")
		w5 = self.tree.get_object("res1920x1080")
		w6 = self.tree.get_object("subtitles_list")
		w7 = self.tree.get_object("res160x128")

		if (self.disctocreate == "divx"):
			w1.show()
			w2.hide()
			w3.hide()
			w4.show()
			w5.show()
			w6.hide()
			w7.show()
		else:
			w1.hide()
			w2.show()
			w3.show()
			w4.hide()
			w5.hide()
			w6.show()
			w7.hide()
		
		w=self.tree.get_object("noaudiotracks")
		w.hide()
		
		w=self.tree.get_object("file_split_frame")
		if (self.disctocreate=="vcd") or (self.disctocreate=="svcd") or (self.disctocreate=="cvd"):
			w.show()
		else:
			w.hide()
		
		w = self.tree.get_object("frame_division") # SPLIT THE FILES IN CHAPTERS FOR EASY SEEKING
		if (self.disctocreate == "dvd"):
			w.show()
		else:
			w.hide()
		
		self.set_resolution()
		self.change_file=False
		if (self.chapter!=-1): # we want to modify a chapter
			the_chapter=structure[title][chapter]
			print "Chequeo "+str(the_chapter["path"])
			isvideo,audio_tracks=self.read_file_values(the_chapter["path"],True)
			if isvideo==True:
				self.read_file_values(the_chapter["path"],False) # get all the values in FILE_VALUES
				self.file_properties=copy.deepcopy(the_chapter)
				self.change_file=True # we are changing the file name manually
				w=self.tree.get_object("moviefile")
				print "Pongo nombre por propiedades"
				w.set_filename(self.file_properties["path"])
			else:
				w1.set_sensitive(False)
		else:
			if (self.global_vars["filmpath"]!=""):
				w=self.tree.get_object("moviefile")
				w.set_current_folder(self.global_vars["filmpath"])
		
		w=self.tree.get_object("moviefile")
		self.file_filter_videos=gtk.FileFilter()
		self.file_filter_videos.set_name(_("Video files"))
		if (sys.platform!="win32") and (sys.platform!="win64"):
			self.file_filter_videos.add_mime_type("video/*")
			self.file_filter_videos.add_pattern("*.rmvb")
		else:
			self.file_filter_videos.add_custom(gtk.FILE_FILTER_FILENAME|gtk.FILE_FILTER_DISPLAY_NAME, self.custom_video_filter)
		self.file_filter_all=gtk.FileFilter()
		self.file_filter_all.set_name(_("All files"))
		self.file_filter_all.add_pattern("*")
		print "Anado filtro"
		w.add_filter(self.file_filter_videos)
		print "Anado filtro"
		w.add_filter(self.file_filter_all)
		self.set_widgets()
		if (self.chapter!=-1): # we want to modify a chapter
			self.set_global_values()
		self.set_film_buttons()
		if (self.chapter!=-1): # we want to modify a chapter
			print "Modificando"
			w=self.tree.get_object("fileaccept")
			w.set_sensitive(True)
			w=self.tree.get_object("preview_film")
			w.set_sensitive(True)
		
		print "Fin"


	# help methods

	def custom_video_filter(self, filter_info=None, data=None):
		"""Custom file filter.  Filter for video files when running on win32"""
		video_types=["m2ts","wmv", "avi", "asf", "flv", "bin", "vob", "es", "ps", "pes","qt", "mov", "mp4", "mpg", "mpeg", "rm", "mkv", "nut", "nsv", "vivo", "fli", "yuv4mpeg", "cpk","ogm", "asx", "3gp"]
		if os.path.splitext(filter_info[2])[1][1:] in video_types:
			return True
		return False


	def get_desired_resolution(self):
		
		""" Returns the resolution desired by the user as a single number """
		
		if (self.tree.get_object("res160x128").get_active()):
			return 8
		if (self.tree.get_object("res1920x1080").get_active()):
			return 7
		if (self.tree.get_object("res1280x720").get_active()):
			return 6
		
		if (self.tree.get_object("res720x480").get_active()):
			return 1
		if (self.tree.get_object("res704x480").get_active()):
			return 2
		if (self.tree.get_object("res480x480").get_active()):
			return 3
		if (self.tree.get_object("res352x480").get_active()):
			return 4
		if (self.tree.get_object("res352x240").get_active()):
			return 5
		return 0


	def adjust_resolution(self):
		
		""" Sets the final resolution and bitrate based on the original resolution and the
			desired one by the user """
		
		if self.file_properties==None:
			return
		
		w1=self.tree.get_object("video_rate")
		vrate=w1.get_value()
		w2=self.tree.get_object("audio_rate")
		arate=w2.get_value()
		resx,resy,use_widescreen,vrate,arate=self.get_recomended_resolution(vrate, arate, self.get_desired_resolution())
		self.file_properties["width"]=resx
		self.file_properties["height"]=resy
		w1.set_value(vrate)
		w2.set_value(arate)
		w=self.tree.get_object("aspect_ratio_4_3")
		if ((resx<720) or (resy<480)) and (self.disctocreate!="divx"):
			w.set_active(True)

		if w.get_active():
			self.file_properties["aspect"]=1.3333333
		else:
			self.file_properties["aspect"]=1.7777777
			

	def get_widgets(self):
		
		""" Fills the file_properties list with the values expressed in the widgets """

		if len(self.file_properties["audio_list"])>0:
			w=self.tree.get_object("audiotrack")
			pos=w.get_active()
			if (pos==-1):
				pos=0
			self.file_properties["audio_stream"]=self.file_properties["audio_list"][pos]
			

		w=self.tree.get_object("force_subs")
		self.file_properties["force_subs"]=w.get_active()
		
		w=self.tree.get_object("blackbars")
		if w.get_active():
			self.file_properties["blackbars"]=0
		else:
			self.file_properties["blackbars"]=1
	
		w=self.tree.get_object("trell")
		self.file_properties["trellis"]=w.get_active()
	
		w=self.tree.get_object("twopass")
		self.file_properties["twopass"]=w.get_active()
		
		w=self.tree.get_object("turbo1stpass")
		self.file_properties["turbo1stpass"]=w.get_active()
	
		self.file_properties["mbd"]=0
		w=self.tree.get_object("mbd1")
		if w.get_active():
			self.file_properties["mbd"]=1
		w=self.tree.get_object("mbd2")
		if w.get_active():
			self.file_properties["mbd"]=2
		
		self.file_properties["deinterlace"]="none"
		w=self.tree.get_object("deinterlace_lb")
		if w.get_active():
			self.file_properties["deinterlace"]="lb"
		w=self.tree.get_object("deinterlace_md")
		if w.get_active():
			self.file_properties["deinterlace"]="md"
		w=self.tree.get_object("deinterlace_fd")
		if w.get_active():
			self.file_properties["deinterlace"]="fd"
		w=self.tree.get_object("deinterlace_l5")
		if w.get_active():
			self.file_properties["deinterlace"]="l5"
		w=self.tree.get_object("deinterlace_yadif")
		if w.get_active():
			self.file_properties["deinterlace"]="yadif"
		
		w=self.tree.get_object("ismpeg")
		self.file_properties["ismpeg"]=w.get_active()

		self.file_properties["swap_fields"]=self.tree.get_object("swap_fields").get_active()

		w=self.tree.get_object("copy_audio")
		self.file_properties["copy_audio"]=w.get_active()

		w=self.tree.get_object("isvob")
		self.file_properties["isvob"]=w.get_active()

		w=self.tree.get_object("sound51")
		self.file_properties["sound51"]=w.get_active()

		w=self.tree.get_object("gop12")
		self.file_properties["gop12"]=w.get_active()

		w=self.tree.get_object("do_chapters")
		if w.get_active():
			w=self.tree.get_object("chapter_long")
			self.file_properties["lchapters"]=w.get_value()
		else:
			self.file_properties["lchapters"]=0

		w=self.tree.get_object("subfont_size")
		self.file_properties["subfont_size"]=int(w.get_value())
	
		w=self.tree.get_object("audiodelay")
		self.file_properties["adelay"]=float(w.get_value())
		
		w=self.tree.get_object("video_rate")
		self.file_properties["vrate"]=int(w.get_value())
		w=self.tree.get_object("audio_rate")
		self.file_properties["arate"]=int(w.get_value())
		
		w=self.tree.get_object("volume_adj")
		self.file_properties["volume"]=int(w.get_value())
	
		w=self.tree.get_object("full_length")
		if w.get_active():
			self.file_properties["cutting"]=0
		else:
			w=self.tree.get_object("first_half")
			if w.get_active():
				self.file_properties["cutting"]=1
			else:
				self.file_properties["cutting"]=2

		w=self.tree.get_object("video_pal")
		if w.get_active():
			self.file_properties["fps"]=25
		else:
			self.file_properties["fps"]=30
	
		if (self.disctocreate=="dvd") or (self.disctocreate=="divx"):
			w=self.tree.get_object("aspect_ratio_16_9")
			if w.get_active():
				self.file_properties["aspect"]=1.77777777
			else:
				self.file_properties["aspect"]=1.33333333
		else:
			self.file_properties["aspect"]=1.33333333

		self.file_properties["resolution"]=self.get_desired_resolution()
	
		w=self.tree.get_object("custom_params")
		self.file_properties["params"]=w.get_text()

		w=self.tree.get_object("custom_params_vf")
		self.file_properties["params_vf"]=w.get_text()
		
		w=self.tree.get_object("custom_params_lavcopts")
		self.file_properties["params_lavc"]=w.get_text()
		
		if (self.disctocreate=="divx"):
			w=self.tree.get_object("custom_params_lameopts")
			self.file_properties["params_lame"]=w.get_text()

		w=self.tree.get_object("rotation0")
		if w.get_active():
			self.file_properties["rotate"]=0 # no rotation
		w=self.tree.get_object("rotation90")
		if w.get_active():
			self.file_properties["rotate"]=90 # rotate 90 degrees clockwise
		w=self.tree.get_object("rotation180")
		if w.get_active():
			self.file_properties["rotate"]=180 # rotate 180 degrees
		w=self.tree.get_object("rotation270")
		if w.get_active():
			self.file_properties["rotate"]=270 # rotate 90 degrees counter-clockwise
		
		w=self.tree.get_object("hmirror")
		self.file_properties["hmirror"]=w.get_active()
		w=self.tree.get_object("vmirror")
		self.file_properties["vmirror"]=w.get_active()

	# Callbacks
	
	def on_reset_volume_clicked(self,widget):
		w=self.tree.get_object("volume_adj")
		w.set_value(100)
		
	
	def on_sub_add_clicked(self,widget):
		
		window=ask_subtitle(self.gladefile,self.global_vars["filmpath"],self.global_vars)
		ret=window.run()
		window=None
		if ret!=None:
			self.file_properties["sub_list"].append(ret)
			self.refresh_subtitles()
			self.set_global_values()

	
	def on_sub_remove_clicked(self,widget):
		
		w=self.tree.get_object("sub_treeview")
		try:
			ctree,iter=w.get_selection().get_selected()
			subtitle=ctree.get_value(iter,0)
		except:
			subtitle=-1
			
		if subtitle==-1:
			return

		newtree=devede_other.create_tree(self,"wdel_subtitle",self.gladefile,False)
		window=newtree.get_object("wdel_subtitle")
		window.show()
		ret=window.run()
		window.hide()
		window.destroy()
		window=None
		newtree=None
		if ret==-5:
			del (self.file_properties["sub_list"])[subtitle]

		self.refresh_subtitles()
		self.set_global_values()
	
	
	def on_filecancel_clicked(self,widget):

		w=self.tree.get_object("expander_advanced")
		self.global_vars["expand_advanced"]=w.get_expanded()
		self.window.destroy()
		self.window=None
		gc.collect()


	def on_fileaccept_clicked(self,widget):
		
		w=self.tree.get_object("expander_advanced")
		self.global_vars["expand_advanced"]=w.get_expanded()
		self.get_widgets()
		if self.chapter==-1: # add this file as a new chapter
			self.structure[self.title].append(self.file_properties)
		else:
			self.structure[self.title][self.chapter]=self.file_properties
		self.window.destroy()
		self.window=None
		(self.callback_refresh)()
		gc.collect()


	def on_wfile_delete_event(self,widget,arg2):
		self.window.destroy()
		self.window=None
		gc.collect()
		return True


	def on_wfile_destroy_event(self,widget,arg2):
		self.window.destroy()
		self.window=None
		gc.collect()
	
	
	def on_clear_subtitles_clicked(self,widget):
		
		""" clears the subtitle filechooser """
		
		w=self.tree.get_object("subtitles_chooser")
		w.unselect_all()
	

	def on_moviefile_file_set(self,widget):
		
		w=self.tree.get_object("moviefile")
		filename=widget.get_filename()
		
		print "File changed to "+str(filename)
		
		if (filename==None) or (filename==""):
			self.set_widgets()
			self.set_global_values()
			self.set_film_buttons()
			return

		self.global_vars["filmpath"]=os.path.split(filename)[0]
		
		if self.change_file:
			self.set_widgets()
			self.set_global_values()
			self.set_film_buttons()
			self.change_file=False
			return
		
		fine,tracks=self.create_default_video_parameters(filename)
		if fine==False: # it's not a video file
			if tracks==0: # it's not a multimedia file
				devede_dialogs.show_error(self.gladefile,_("File doesn't seem to be a video file."))
			else:
				devede_dialogs.show_error(self.gladefile,_("File seems to be an audio file."))
			w.unselect_all()
		self.set_widgets()
		self.set_global_values()
		self.set_film_buttons()


	def on_video_pal_toggled(self,widget):
		
		""" Detects the change in the option PAL/NTSC """
		
		w=self.tree.get_object("video_pal")
		self.pal=w.get_active()
		self.set_resolution()
		self.adjust_resolution()
		self.set_global_values()


	def on_res_toggled(self,widget):
		
		self.adjust_resolution()
		self.set_global_values()
		self.set_film_buttons()


	def on_length_toggled(self,widget):
		
		self.set_global_values()


	def on_video_rate_value_changed(self,widget):
		self.set_global_values()
		

	def on_audio_rate_value_changed(self,widget):
		self.set_global_values()


	def on_subtitles_chooser_selection_changed(self,widget):
		self.set_global_values()


	def on_aspect_ratio_toggled(self,widget):
		
		if self.file_properties==None:
			return
		
		w=self.tree.get_object("aspect_ratio_16_9")
		if w.get_active()==False:
			return

		self.set_resolution()
		if (self.file_properties["width"]<720) or (self.file_properties["height"]<480):
			w=self.tree.get_object("res720x480")
			w.set_active(True)


	def on_ismpeg_toggled(self,widget):
		
		self.set_film_buttons()
		self.set_global_values()


	def on_copy_audio_toggled(self,widget):
		
		self.set_film_buttons()
		self.set_global_values()


	def on_isvob_toggled(self,widget):
		
		self.set_film_buttons()
		self.set_global_values()

	def on_twopass_toggled(self,widget):
		w = self.tree.get_object("turbo1stpass")
		if widget.get_active():
			w.set_sensitive(True)
		else:
			w.set_active(False)
			w.set_sensitive(False)
			
	def on_sound51_toggled(self,widget):

		self.set_film_buttons()
		self.set_global_values()


	def on_preview_film_clicked(self,widget):

		self.get_widgets()
		self.global_vars["erase_temporary_files"]=True
		self.global_vars["number_actions"]=1
		tmp_structure=[["",self.file_properties]]
		converter=devede_convert.create_all(self.gladefile,tmp_structure,self.global_vars,self.callback)
		converter.preview(self.global_vars["temp_folder"])


	def on_file_help_clicked(self,widget):
	
		help_class=devede_help.show_help(self.gladefile,self.global_vars["help_path"],"file.html")


	def callback(self):
		
		""" This method is called after a preview """
		
		return None # do nothing


	def draganddrop(self,widget,drag_context, x, y, selection, info, time):

		""" Manages the Drag&Drop in the property window """

		sub_extensions3=[".sub",".srt",".ssa",".smi",".txt",".aqt",".jss", ".ass"]
		sub_extensions2=[".rt",".js"]

		lista=self.split_dnd(selection.data)

		if len(lista)==0:
			return

		if len(lista)>1:
			devede_dialogs.show_error(self.gladefile,_("Please, add only one file each time."))
			return

		if self.disctocreate!="divx":
			print("Entro en subs")
			filename=str(lista[0]).lower()
			if len(filename)>=4:
				extension3=filename[-4:]
				extension2=filename[-3:]
				print "Extensiones: "+str(extension3)+" "+str(extension2)
				if (0!=sub_extensions3.count(extension3)) or (0!=sub_extensions2.count(extension2)): # is a subtitle
					current_file=self.tree.get_object("moviefile").get_filename()
					if (current_file=="") or (current_file==None):
						devede_dialogs.show_error(self.gladefile,_("Please, add a movie file before adding subtitles."))
						return
					window=ask_subtitle(self.gladefile,self.global_vars["filmpath"],self.global_vars,lista[0])
					ret=window.run()
					window=None
					if ret!=None:
						self.file_properties["sub_list"].append(ret)
						self.refresh_subtitles()
						self.set_global_values()
					return

		w=self.tree.get_object("moviefile")
		print "Adding "+str(lista[0])
		w.set_filename(str(lista[0]))


	# data visualization methods


	def set_resolution(self):

		""" Sets the labels with the rigth resolution values, depending
		if the user selected PAL/SECAM or NTSC """

		if self.pal:
			res1="288"
			res2="576"
		else:
			res1="240"
			res2="480"

		w=self.tree.get_object("res720x480")
		w.set_label("720x"+res2)
		w=self.tree.get_object("res704x480")
		w.set_label("704x"+res2)
		w=self.tree.get_object("res480x480")
		w.set_label("480x"+res2)
		w=self.tree.get_object("res352x480")
		w.set_label("352x"+res2)
		w=self.tree.get_object("res352x240")
		w.set_label("352x"+res1)


	def set_widgets(self):
		
		""" sets the widgets to the values specificated in SELF.FILE_PROPERTIES """
		
		dsize,minvid,maxvid=devede_other.get_dvd_size(None,self.disctocreate)

		if self.disctocreate=="vcd":
			w=self.tree.get_object("video_rate_adj")
			w.set_value(1152)
			w=self.tree.get_object("audio_rate_adj")
			w.set_value(224)
		elif (self.disctocreate=="svcd") or (self.disctocreate=="cvd"):
			w=self.tree.get_object("audio_rate_adj")
			w.set_lower(64)
			w.set_upper(384)
			#w.set_range(64,384)
		else:
			print "entro en parte critica"
			w=self.tree.get_object("audio_rate_adj")
			print "paso por set_lower"
			w.set_lower(128)
			w.set_upper(448)
			#w.set_range(128,448)
			
		if self.disctocreate!="vcd":
			w=self.tree.get_object("video_rate_adj")
			w.set_lower(minvid)
			w.set_upper(maxvid)
			#w.set_range(minvid,maxvid)

		if self.file_properties==None:
			return
		
		w=self.tree.get_object("force_subs")
		w.set_active(self.file_properties["force_subs"])

		w1=self.tree.get_object("aspect_ratio_4_3")
		w2=self.tree.get_object("aspect_ratio_16_9")
		w1.set_active(True)
		print "Activo ASPECT_RATIO"
		print self.disctocreate
		if (self.disctocreate=="dvd") or (self.disctocreate=="divx"):
			w1.set_sensitive(True)
			w2.set_sensitive(True)
			if self.file_properties["aspect"]>1.6:
				w2.set_active(True)
			else:
				w1.set_active(True)
		else:
			w1.set_sensitive(False)
			w2.set_sensitive(False)

		if self.file_properties["resolution"]==0: # auto resolution
			w=self.tree.get_object("resauto")
		elif self.file_properties["resolution"]==1: # 720x480
			w=self.tree.get_object("res720x480")
		elif self.file_properties["resolution"]==2: # 704x480
			w=self.tree.get_object("res704x480")
		elif self.file_properties["resolution"]==3: # 480x480
			w=self.tree.get_object("res480x480")
		elif self.file_properties["resolution"]==4: # 352x480
			w=self.tree.get_object("res352x480")
		elif self.file_properties["resolution"]==6: # 1280x720
			w=self.tree.get_object("res1280x720")
		elif self.file_properties["resolution"]==7: # 1920x1080
			w=self.tree.get_object("res1920x1080")
		elif self.file_properties["resolution"]==8: # 160x128
			w=self.tree.get_object("res160x128")
		else:
			w=self.tree.get_object("res352x240")
	
		w.set_active(True)
	
		w=self.tree.get_object("trell")
		w.set_active(self.file_properties["trellis"])
	
		w=self.tree.get_object("twopass")
		w.set_active(self.file_properties["twopass"])
		
		w=self.tree.get_object("turbo1stpass")
		w.set_active(self.file_properties["turbo1stpass"])
		
		w.set_sensitive(self.file_properties["twopass"])
		
		if self.file_properties["mbd"]==0:
			w=self.tree.get_object("mbd")
		elif self.file_properties["mbd"]==1:
			w=self.tree.get_object("mbd1")
		else:
			w=self.tree.get_object("mbd2")
		w.set_active(True)
	
		if self.file_properties["deinterlace"]=="none":
			w=self.tree.get_object("deinterlace")
		else:
			w=self.tree.get_object("deinterlace_"+self.file_properties["deinterlace"])
		w.set_active(True)
	
		w=self.tree.get_object("volume_adj")
		w.set_value(self.file_properties["volume"])
	
		w=self.tree.get_object("ismpeg")
		w.set_active(self.file_properties["ismpeg"])

		w=self.tree.get_object("copy_audio")
		w.set_active(self.file_properties["copy_audio"])

		w=self.tree.get_object("isvob")
		w.set_active(self.file_properties["isvob"])
	
		w=self.tree.get_object("sound51")
		w.set_active(self.file_properties["sound51"])
		
		w=self.tree.get_object("gop12")
		w.set_active(self.file_properties["gop12"])
		
		w=self.tree.get_object("subfont_size")
		w.set_value(self.file_properties["subfont_size"])
		
		w=self.tree.get_object("swap_fields")
		w.set_active(self.file_properties["swap_fields"])
	
		w=self.tree.get_object("custom_params")
		w.set_text(self.file_properties["params"])

		w=self.tree.get_object("custom_params_lavcopts")
		w.set_text(self.file_properties["params_lavc"])
		
		w=self.tree.get_object("custom_params_vf")
		w.set_text(self.file_properties["params_vf"])
		
		if (self.disctocreate=="divx"):
			w=self.tree.get_object("custom_params_lameopts")
			w.set_text(self.file_properties["params_lame"])
	
		vrate=self.tree.get_object("video_rate")
		vrate.set_value(self.file_properties["vrate"])
		arate=self.tree.get_object("audio_rate")
		arate.set_value(self.file_properties["arate"])
		w=self.tree.get_object("audiodelay")
		w.set_value(self.file_properties["adelay"])
		if self.file_properties["blackbars"]==0:
			w=self.tree.get_object("blackbars")
		else:
			w=self.tree.get_object("scalepict")
		w.set_active(True)
		
		w=self.tree.get_object("do_chapters")
		if self.file_properties["lchapters"]==0:
			w.set_active(False)
			w=self.tree.get_object("chapter_long")
			w.set_sensitive(False)
		else:
			w.set_active(True)
			w=self.tree.get_object("chapter_long")
			w.set_sensitive(True)
			w.set_value(self.file_properties["lchapters"])
		
		if self.file_properties["fps"]==25:
			w=self.tree.get_object("video_pal")
		else:
			w=self.tree.get_object("video_ntsc")
		w.set_active(True)
	
		if self.file_properties["cutting"]==0:
			w=self.tree.get_object("full_length")
		elif self.file_properties["cutting"]==1:
			w=self.tree.get_object("first_half")
		else:
			w=self.tree.get_object("second_half")
		w.set_active(True)
	
		print "Rotate: "+str(self.file_properties["rotate"])
		if self.file_properties["rotate"]==0:
			w=self.tree.get_object("rotation0")
		elif self.file_properties["rotate"]==90:
			w=self.tree.get_object("rotation90")
		elif self.file_properties["rotate"]==180:
			w=self.tree.get_object("rotation180")
		elif self.file_properties["rotate"]==270:
			w=self.tree.get_object("rotation270")
		w.set_active(True)
		
		w=self.tree.get_object("hmirror")
		w.set_active(self.file_properties["hmirror"])
		w=self.tree.get_object("vmirror")
		w.set_active(self.file_properties["vmirror"])

		self.audio_model.clear()
		if len(self.file_properties["audio_list"])>0:
			w=self.tree.get_object("hasaudiotracks")
			w.show()
			w=self.tree.get_object("noaudiotracks")
			w.hide()
			position=0
			for track in self.file_properties["audio_list"]:
				print "Meto pista "+str(track)
				iterator=self.audio_model.insert(position)
				self.audio_model.set_value(iterator,0,track)
				position+=1
			print "Pista seleccionada: "+str(self.file_properties["audio_stream"])
			w=self.tree.get_object("audiotrack")
			w.set_active(self.file_properties["audio_list"].index(self.file_properties["audio_stream"]))
		else:
			w=self.tree.get_object("hasaudiotracks")
			w.hide()
			w=self.tree.get_object("noaudiotracks")
			w.show()

		self.refresh_subtitles()
		
		if (self.global_vars["use_ffmpeg"]):
			use_ffmpeg=False
		else:
			use_ffmpeg=True
		
		self.tree.get_object("turbo1stpass").set_visible(use_ffmpeg)
		self.tree.get_object("deinterlace_md").set_visible(use_ffmpeg)
		self.tree.get_object("deinterlace_l5").set_visible(use_ffmpeg)
		self.tree.get_object("deinterlace_lb").set_visible(use_ffmpeg)
		self.tree.get_object("lavcopts_label").set_visible(use_ffmpeg)
		self.tree.get_object("lameopts_label").set_visible(use_ffmpeg)
		self.tree.get_object("custom_params_lavcopts").set_visible(use_ffmpeg)
		self.tree.get_object("custom_params_lameopts").set_visible(use_ffmpeg)
		#self.tree.get_object("volume_frame").set_visible(use_ffmpeg)
		self.tree.get_object("audiotrack_box").set_visible(use_ffmpeg)
		self.tree.get_object("frame_field_order").set_visible(use_ffmpeg)
		

	def refresh_subtitles(self):

		self.sub_model.clear()
		position=0
		for subtitle in self.file_properties["sub_list"]:
			iterator=self.sub_model.insert(position)
			self.sub_model.set_value(iterator,0,position)
			name=subtitle["subtitles"]
			while True:
				pos=name.find(os.sep)
				if (pos==-1):
					break
				name=name[pos+1:]
			
			self.sub_model.set_value(iterator,1,name)
			self.sub_model.set_value(iterator,2,subtitle["sub_codepage"])
			self.sub_model.set_value(iterator,3,subtitle["sub_language"])
			position+=1
		w=self.tree.get_object("sub_treeview")
		w.get_selection().select_path(0)
		self.set_film_buttons()
			

	def set_film_buttons(self):

		""" Enables or disables all the buttons, based in the current disk type and other widgets """

		w1=self.tree.get_object("fileaccept")
		w=self.tree.get_object("moviefile")
		cfile=w.get_filename()
		
		w=self.tree.get_object("preview_film")
		if (cfile=="") or (cfile==None):
			w.set_sensitive(False)
			w1.set_sensitive(False)
		else:
			w.set_sensitive(True)
			w1.set_sensitive(True)

		w0=self.tree.get_object("ismpeg")
		w0s=w0.get_active()
		if w0s:
			grupo2=False
		else:
			grupo2=True

		w1=self.tree.get_object("copy_audio")
		w1s=w1.get_active()
		if w1s:
			copy_audio=False
		else:
			copy_audio=grupo2

		w2=self.tree.get_object("isvob")
		w2s=w2.get_active()
		if w2s:
			isvob=False
		else:
			isvob=grupo2

		if (self.disctocreate!="dvd") and (self.disctocreate!="divx"):
			w1.set_active(False)
			w1.set_sensitive(False)
			sound51=False
		else:
			w1.set_sensitive(grupo2)
			sound51=grupo2

		if w0s:
			w2.set_sensitive(False)
			w1.set_sensitive(False)
		else:
			w2.set_sensitive(True)
			w1.set_sensitive(True)
			if w1s:
				w2.set_sensitive(False)
			else:
				w2.set_sensitive(True)
				if w2s:
					w0.set_sensitive(False)
					w1.set_sensitive(False)
				else:
					w1.set_sensitive(True)
					w0.set_sensitive(True)

		if self.disctocreate =="vcd":
			grupo1=False
		else:
			grupo1=grupo2
		
		if (self.disctocreate=="dvd") or (self.disctocreate=="divx"):
			w=self.tree.get_object("sound51")
			if w.get_active():
				w=self.tree.get_object("audio_rate_adj")
				w.set_lower(384)
				w.set_upper(448)
				if w.get_value()<384:
					w.set_value(384)
				#w.set_range(384,448)		
			else:
				w=self.tree.get_object("audio_rate_adj")
				w.set_lower(128)
				w.set_upper(448)
				#w.set_range(128,448)

		grupo3=grupo2
		try:
			if self.file_properties["olength"]<60:
				grupo3=False
		except:
			grupo3=False

		w=self.tree.get_object("video_rate")
		w.set_sensitive(grupo1 and isvob)
		w=self.tree.get_object("audio_rate")
		w.set_sensitive(grupo1 and copy_audio and isvob)
		w=self.tree.get_object("swap_fields")
		w.set_sensitive(grupo1 and isvob)
		w=self.tree.get_object("gop12")
		w.set_sensitive(grupo2 and isvob)
		w=self.tree.get_object("volume_scale")
		w.set_sensitive(grupo2 and isvob and copy_audio)
		w=self.tree.get_object("volume_level")
		w.set_sensitive(grupo2 and isvob and copy_audio)
		w=self.tree.get_object("reset_volume")
		w.set_sensitive(grupo2 and isvob and copy_audio)
		w=self.tree.get_object("sound51")
		if grupo1==False:
			w.set_active(False)
		w.set_sensitive(sound51)
		w=self.tree.get_object("resauto")
		w.set_sensitive(grupo1 and isvob)
		if (w.get_active()) and (self.disctocreate=="divx"):
			set_aspect=False
		else:
			set_aspect=True
		w=self.tree.get_object("res352x240")
		w.set_sensitive(grupo1 and isvob)
		w=self.tree.get_object("res352x480")
		w.set_sensitive(grupo1 and isvob)
		w=self.tree.get_object("res480x480")
		w.set_sensitive(grupo1 and isvob)
		w=self.tree.get_object("res704x480")
		w.set_sensitive(grupo1 and isvob)
		w=self.tree.get_object("res720x480")
		w.set_sensitive(grupo1 and isvob)
		
		w=self.tree.get_object("full_length")
		w.set_sensitive(grupo3)
		w=self.tree.get_object("first_half")
		w.set_sensitive(grupo3)
		w=self.tree.get_object("second_half")
		w.set_sensitive(grupo3)
		w=self.tree.get_object("video_pal")
		w.set_sensitive(grupo2 and isvob)
		w=self.tree.get_object("video_ntsc")
		w.set_sensitive(grupo2 and isvob)
		w=self.tree.get_object("audiodelay")
		w.set_sensitive(copy_audio and isvob)
		w=self.tree.get_object("blackbars")
		w.set_sensitive(grupo2 and isvob)
		w=self.tree.get_object("scalepict")
		w.set_sensitive(grupo2 and isvob)
		w=self.tree.get_object("custom_params")
		w.set_sensitive(grupo2 and isvob)
		w=self.tree.get_object("custom_params_vf")
		w.set_sensitive(grupo2 and isvob)
		w=self.tree.get_object("custom_params_lavcopts")
		w.set_sensitive(grupo2 and isvob)
		w=self.tree.get_object("custom_params_lameopts")
		w.set_sensitive(copy_audio and isvob)
		w2=self.tree.get_object("lameopts_label")
		if self.disctocreate=="divx":
			w.show()
			w2.show()
		else:
			w.hide()
			w2.hide()

		w=self.tree.get_object("trell")
		w.set_sensitive(grupo2 and isvob)
		
		w=self.tree.get_object("rotation0")
		w.set_sensitive(grupo2 and isvob)
		w=self.tree.get_object("rotation90")
		w.set_sensitive(grupo2 and isvob)
		w=self.tree.get_object("rotation180")
		w.set_sensitive(grupo2 and isvob)
		w=self.tree.get_object("rotation270")
		w.set_sensitive(grupo2 and isvob)
		w=self.tree.get_object("hmirror")
		w.set_sensitive(grupo2 and isvob)
		w=self.tree.get_object("vmirror")
		w.set_sensitive(grupo2 and isvob)
		
		w=self.tree.get_object("mbd")
		w.set_sensitive(grupo2 and isvob)
		w=self.tree.get_object("mbd1")
		w.set_sensitive(grupo2 and isvob)
		w=self.tree.get_object("mbd2")
		w.set_sensitive(grupo2 and isvob)
		w=self.tree.get_object("twopass")
		w.set_sensitive(grupo2 and isvob)
		tp = w.get_active()
		w=self.tree.get_object("turbo1stpass")
		w.set_sensitive(grupo2 and isvob and tp)
		w=self.tree.get_object("deinterlace")
		w.set_sensitive(grupo2 and isvob)
		w=self.tree.get_object("deinterlace_lb")
		w.set_sensitive(grupo2 and isvob)
		w=self.tree.get_object("deinterlace_md")
		w.set_sensitive(grupo2 and isvob)
		w=self.tree.get_object("deinterlace_fd")
		w.set_sensitive(grupo2 and isvob)
		w=self.tree.get_object("deinterlace_l5")
		w.set_sensitive(grupo2 and isvob)
		w=self.tree.get_object("deinterlace_yadif")
		w.set_sensitive(grupo2 and isvob)
		w=self.tree.get_object("audiotrack")
		w.set_sensitive(grupo2)
		w1=self.tree.get_object("aspect_ratio_4_3")
		w2=self.tree.get_object("aspect_ratio_16_9")
		if (self.disctocreate == "dvd") or (self.disctocreate == "divx"):
			w1.set_sensitive(grupo2 and isvob and set_aspect)
			w2.set_sensitive(grupo2 and isvob and set_aspect)
		else:
			w1.set_sensitive(False)
			w2.set_sensitive(False)

		w1=self.tree.get_object("sub_remove")
		w2=self.tree.get_object("sub_add")
		try:
			sub_number=len(self.file_properties["sub_list"])
			if sub_number==0:
				w1.set_sensitive(False)
			else:
				w1.set_sensitive(True)
			
			if sub_number>=32:
				w2.set_sensitive(False)
			else:
				w2.set_sensitive(True)
		except:
			w1.set_sensitive(False)
			w2.set_sensitive(False)


	def set_global_values(self):

		""" Repaints all the data about the current film, recalculating
			the size needed and other params """
		
		if self.file_properties==None:
			empty=True
		else:
			empty=False
	
		w=self.tree.get_object("o_size2")
		if empty:
			w.set_text("")
		else:
			w.set_text(str(self.file_properties["owidth"])+"x"+str(self.file_properties["oheight"]))

		w=self.tree.get_object("leng2")
		if empty:
			w.set_text("")
		else:
			w.set_text(str(self.file_properties["olength"]))
		
		w=self.tree.get_object("fps")
		if empty:
			w.set_text("")
		else:
			w.set_text(str(self.file_properties["ofps"]))

		w=self.tree.get_object("vrate2")
		if empty:
			w.set_text("")
		else:
			w.set_text(str(self.file_properties["ovrate"]))

		w=self.tree.get_object("arate2")
		if empty:
			w.set_text("")
		else:
			w.set_text(str(self.file_properties["oarate"]))
	
		w=self.tree.get_object("video_rate")
		vrate=w.get_value()
		w=self.tree.get_object("audio_rate")
		arate=w.get_value()
	
		w=self.tree.get_object("full_length")
		if w.get_active():
			divide=False
			divide2=0
		else:
			divide=True
			divide2=1
		
		w=self.tree.get_object("eleng2")
		if empty:
			w.set_text("")
		else:
			w2=self.tree.get_object("ismpeg")
			w4=self.tree.get_object("isvob")
			props={}
			props["ofps"]=self.file_properties["ofps"]
			props["ofps2"]=self.file_properties["ofps2"]
			w3=self.tree.get_object("video_pal")
			if w3.get_active():
				props["fps"]=25
			else:
				props["fps"]=30
			w3=self.tree.get_object("copy_audio")
			props["copy_audio"]=w3.get_active()
			w3=self.tree.get_object("ismpeg")
			props["ismpeg"]=w3.get_active()
			print "Props: "+str(props)
			speed1,speed2=devede_other.get_speedup(props)
			l=devede_other.calcula_tamano_parcial(vrate,arate,self.file_properties["filesize"],self.file_properties["olength"],len(self.file_properties["sub_list"]),w2.get_active(),w4.get_active(),divide2,speed1,speed2)
			#if w2.get_active():
			#	l=int(self.file_properties["filesize"]/1000000)
			#else:
			#	l=int(((vrate+arate)*self.file_properties["olength"])/8000)
			#	if divide:
			#		l/=2
			
			#l+=int((8.0*float(len(self.file_properties["sub_list"]))*self.file_properties["olength"])/8000.0)
			w.set_text(str(int(l/1000)))
		
		w=self.tree.get_object("f_size2")
		if empty:
			w.set_text("")
		else:
			w.set_text(str(self.file_properties["width"])+"x"+str(self.file_properties["height"]))		


class ask_subtitle:
	
	def __init__(self,gladefile,filepath,gvars,filename=None):

		self.global_vars=gvars
		self.gladefile=gladefile
		self.tree=devede_other.create_tree(self,"add_subtitle2",self.gladefile)
		self.lang_list=[]
		self.cpage_list=[]
		
		pos=0
		self.lang=-1
		self.asciie=-1
		self.utf8e=-1
		self.utf16e=-1
		self.isoe=-1
		languages=open(os.path.join(self.gladefile,"languages.lst"),"r")
		w=self.tree.get_object("sub_language")
		for element in languages:
			if element[:-1]==self.global_vars["sub_language"]:
				self.lang=pos
			w.append_text(element[:-1])
			self.lang_list.append(element[:-1])
			pos+=1
		languages.close()
		w.set_active(self.lang)
		
		pos=0
		self.chelement=0
		codepages=open(os.path.join(self.gladefile,"codepages.lst"),"r")
		w=self.tree.get_object("sub_codepage")
		for element in codepages:
			if element[:-1]=="ASCII":
				self.asciie=pos
			if element[:-1]=="UTF-8":
				self.utf8e=pos
			if element[:-1]=="UTF-16":
				self.utf16e=pos
			if element[:-1]=="ISO-8859-1":
				self.isoe=pos
			if element[:-1]==self.global_vars["sub_codepage"]:
				self.chelement=pos
			w.append_text(element[:-1])
			self.cpage_list.append(element[:-1])
			pos+=1
		codepages.close()
		if self.chelement!=-1:
			w.set_active(self.chelement)
		elif (self.utf8e!=-1):
			w.set_active(self.utf8e)
		else:
			w.set_active(self.isoe)

		self.window=self.tree.get_object("add_subtitle")
		if (filepath!=""):
			w=self.tree.get_object("subtitles_chooser")
			w.set_current_folder(filepath)
		if (filename!=None) and (filename!=""):
			self.tree.get_object("subtitles_chooser").set_filename(filename)
		self.window.show()
		self.set_status()


	def on_clear_subtitles_clicked(self,widget):

		file=self.tree.get_object("subtitles_chooser")
		file.unselect_all()


	def on_subtitles_chooser_selection_changed(self,widget):
		
		filename=widget.get_filename()
		if (filename!="") and (filename!=None):
			w=self.tree.get_object("sub_codepage")
			autotype=devede_other.check_utf().do_check(filename)
			print "Subtitles changed to type: "+str(autotype)
			if autotype=="ascii":
				w.set_active(self.asciie)
				self.autotype="ASCII"
			elif autotype=="utf8":
				w.set_active(self.utf8e)
				self.autotype="UTF-8"
			elif autotype=="utf16":
				w.set_active(self.utf16e)
				self.autotype="UTF-16"
			elif self.chelement!=-1:
				w.set_active(self.chelement)
				self.autotype=""
			else:
				w.set_active(self.isoe)
				self.autotype=""
		self.set_status()


	def set_status(self):
		
		filename=self.tree.get_object("subtitles_chooser").get_filename()
		
		if (filename=="") or (filename==None):
			status=False
		else:
			status=True
			
		w=self.tree.get_object("sub_accept")
		w.set_sensitive(status)

	
	def run(self):
		
		ret=self.window.run()
		if ret==-5: # OK
			ret_val={}
			w=self.tree.get_object("subtitles_chooser")
			ret_val["subtitles"]=w.get_filename()
			w=self.tree.get_object("sub_codepage")
			ret_val["sub_codepage"]=self.cpage_list[w.get_active()]
			if (ret_val["sub_codepage"]!=self.autotype) and (ret_val["sub_codepage"][:3]!="UTF"):
				self.global_vars["sub_codepage"]=ret_val["sub_codepage"]
			w=self.tree.get_object("sub_language")
			ret_val["sub_language"]=self.lang_list[w.get_active()]
			self.global_vars["sub_language"]=ret_val["sub_language"]
			w=self.tree.get_object("sub_up")
			ret_val["subtitles_up"]=w.get_active()
		else:
			ret_val=None
		self.window.hide()
		self.window.destroy()
		self.window=None
		return(ret_val)
