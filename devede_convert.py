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


#################################################################
# This block contains all the functions to convert a video file #
# into an MPEG2-PS DVD-compliant file                           #
#################################################################

import time
import select
import signal
import subprocess
import sys
import os
import re
import shutil
import glob
import posixpath
import gtk
import devede_other
import gobject
import cairo
import dbus

if (sys.platform=="win32") or (sys.platform=="win64"):
	import win32api

import devede_other
import devede_video_convert
import devede_ffmpeg_convert
import devede_subtitles
import devede_xml_menu
import devede_delete
import devede_dvd
import devede_bincue
import devede_executor
import devede_dialogs

import gc

class create_all:

	def cancel_clicked(self,widget,temp=False):
		
		newtree=devede_other.create_tree(self,"wcancel_job_dialog",self.gladefile,False)
		window=newtree.get_object("wcancel_job_dialog")
		window.show()
		value=window.run()
		window.hide()
		window.destroy()
		if value!=-5: # no
			return True

		self.runner.cancel()
		self.runner.wait_end()
		gobject.source_remove(self.timer)
		self.window.hide()
		self.window.destroy()
		newtree=devede_other.create_tree(self,"waborted_dialog",self.gladefile,False)
		window=newtree.get_object("waborted_dialog")
		window.show()
		window.run()
		window.hide()
		window.destroy()
		window=None
		gc.collect()
		(self.main_window_callback)() # show the main window
		return True


	def iso_changed(self,args,arbol):

		iso_name=arbol.get_object("iso_filename")
		iso_folder=arbol.get_object("final_directory")
	
		w=arbol.get_object("button_folder_accept")
	
		mode=True
	
		if iso_name.get_text()=="":
			mode=False
		
		folder=iso_folder.get_current_folder()
		if folder==None:
			mode=False
		elif folder=="":
			mode=False
		
		w.set_sensitive(mode)


	def check_free_space(self,filefolder,structure,actions,erase_temporary_files,sound_duration):

		""" Returns TRUE if the free space in FILEFOLDER is insuficient to generate
		the disk STRUCTURE """
		# TODO Windows Stuff
		estado=''
		freespace=''
		if (sys.platform!="win32") and (sys.platform!="win64"):
			print "Checking "+str(filefolder)
			estado=os.statvfs(filefolder) # eg. f="C:\Documents and Settings\User name\Desktop"
			freespace=95*estado.f_bsize*estado.f_bavail/100000
		else:
			try:
				test_drive = os.path.splitdrive(filefolder)[0] + "\\" # So it will also work on Windows 2000 
				spc, bps, fc, tc = win32api.GetDiskFreeSpace(test_drive)
				freespace=fc * spc * bps

			except ImportError:
				pass
		print "Free space in "+str(filefolder)+": "+str(freespace)
		print "estatus ", estado, "\n"
	
		total=devede_other.calcula_tamano_total(structure,sound_duration,self.disk_type)

		print "Free: "+str(freespace)
		print "Needed: "+str(total)
	
		if (actions!=3):
			total*=actions # if we only create the MPEG files or the DVD structure...
		else:
			if erase_temporary_files: # or if we create the ISO image
				total*=2
			else:
				total*=3
		total*=1.1 # a safe margin of 10%

		if (freespace<total):
			return True,_("Insuficient free space. To create this disc\n%(total)d MBytes are needed, but only %(free)d MBytes are available.") % {'total':int(total/1000),'free':int(freespace/1000)}
		else:
			return False,""

	
	def __init__(self,gladefile,structure,global_vars,callback):
		
		if (0!=devede_other.check_program("k3b -v")):
			self.k3b_available=False
		else:
			self.k3b_available=True
		
		if (0!=devede_other.check_program("brasero --help")):
			self.brasero_available=False
		else:
			self.brasero_available=True
		
		self.gladefile=gladefile
		self.structure=structure
		self.global_vars=global_vars
		self.tree=devede_other.create_tree(self,"wprogress",self.gladefile)
		
		self.window=self.tree.get_object("wprogress")
		self.partial=self.tree.get_object("progresspartial")
		self.erase_temp=global_vars["erase_temporary_files"]
		self.iso_creator=global_vars["iso_creator"]

		self.queue=[]
		self.current_action=0
		self.actions=global_vars["number_actions"]
		self.total=self.tree.get_object("progress_total")
		self.label=self.tree.get_object("lcreating")
		self.total.set_fraction(0)
		self.partial.set_fraction(0)
		self.partial.set_text("0%")
		self.label.set_text("")
		self.start_time=time.time()
		self.disk_type=global_vars["disctocreate"]
		self.main_window_callback=callback
		self.tiempo=time.time()


	def init_queue(self):

		total=0
		title=0
		for element in self.structure:
			chapter=0
			for element2 in element[1:]:
				if self.structure[title][chapter+1]["twopass"] == True:
					self.queue.append(["C1",title,chapter])
					self.queue.append(["C2",title,chapter])
				else:
					self.queue.append(["C",title,chapter])
				stream=0
				for element3 in element2["sub_list"]:
					self.queue.append(["S",title,chapter,stream])
					stream+=1

				#if self.structure[title][chapter+1]["twopass"] == True:
				#	self.queue.append(["C2",title,chapter])
				#	stream=0
				#	for element3 in element2["sub_list"]:
				#		self.queue.append(["S",title,chapter,stream])
				#		stream+=1
						
				chapter+=1
			title+=1


	def preview(self,filefolder):
		
		self.init_queue()
		newtree=devede_other.create_tree(self,"wpreview_dialog",self.gladefile,False)
		timev=newtree.get_object("seconds_preview")
		timev.set_value(60)
		
		w=newtree.get_object("wpreview_dialog")
		w.show()
		ret=w.run()
		w.hide()
		self.filefolder=filefolder
		if self.filefolder[-1]!=os.sep:
			self.filefolder+=os.sep
		self.seconds=timev.get_value()
		w.destroy()
		if ret!=-6:
			self.window.destroy()
			return

		self.runner=None
		self.queue.append(["PREVIEW"]) # Preview
		self.total_done=0.0
		self.filename="previewfile"
		
		try:
			fichero=open(self.filefolder+"write_check","w")
			fichero.write("Testing")
			fichero.close()
		except:
			self.show_error(_("Failed to write to the destination directory.\nCheck that you have privileges and free space there."))
			self.window.destroy()
			return
		
		try:
			os.remove(self.filefolder+"write_check")
		except:
			print "Failed to erase the write check file"
		
		self.eraser=devede_delete.delete_files(self.filename,self.filefolder)
		self.erase_temp=True
		self.timer=gobject.timeout_add(250,self.time_callback)
		self.window.show()
		return
		

	def on_iso_filename_activate(self,widg,ventana):
		
		ventana.response(-6)


	def create_disc(self):
		
		self.time=0
		
		# first, check for empty titles
		
		empty=False
		for element in self.structure:
			if len(element)<2:
				empty=True
				break
			
		if empty:
			newtree=devede_other.create_tree(self,"wempty_titles_dialog",self.gladefile,False)
			w=newtree.get_object("wempty_titles_dialog")
			w.show()
			value=w.run()
			w.hide()
			w.destroy()
			if value!=-6:
				return False

		# ask the folder and filename
		
		newtree=devede_other.create_tree(self,"wfolder_dialog",self.gladefile,False)
		wdir=newtree.get_object("final_directory")
		if self.global_vars["finalfolder"]!="":
			wdir.set_current_folder(self.global_vars["finalfolder"])
		wfile=newtree.get_object("iso_filename")
		wfolder_dialog=newtree.get_object("wfolder_dialog")
		do_shdw=newtree.get_object("do_shutdown")
		wfile.set_text("movie")
		wfile.connect("activate",self.on_iso_filename_activate,wfolder_dialog)
		wfile.connect("changed",self.iso_changed,newtree)
		wdir.connect("current-folder-changed",self.iso_changed,newtree)
		#self.iso_changed("",newtree)

		wfolder_dialog.show()
		wfile.grab_focus()
		print "Entro en RUN"
		value=wfolder_dialog.run()
		print "Salgo de RUN"
		self.global_vars["shutdown_after_disc"]=do_shdw.get_active()
		self.filename=wfile.get_text()
		self.filename.replace("/","_")
		self.filename.replace("|","_")
		self.filename.replace("\\","_")
		
		filefolder=wdir.get_current_folder()
		
		wfolder_dialog.hide()
		wfolder_dialog.destroy()
		if value!=-6:
			self.window.hide()
			self.window.destroy()
			(self.main_window_callback)()
			return False
		
		self.global_vars["finalfolder"]=filefolder
		
		filefolder2=os.path.join(filefolder,self.filename)
		
		self.filefolder=filefolder2
		
		if self.filefolder[-1]!=os.sep:
			self.filefolder+=os.sep
		
		if (os.path.exists(filefolder2)):
			newtree=devede_other.create_tree(self,"wfolder_exists",self.gladefile,False)
			w=newtree.get_object("wfolder_exists")
			wtext=newtree.get_object("folder_exists_label")
			wtext.set_text(_("The file or folder\n\n%(folder)s\n\nalready exists. If you continue, it will be deleted.") % {'folder':filefolder2})
			w.show()
			value=w.run()
			w.hide()
			w.destroy()
			if value!=2:
				self.window.hide()
				self.window.destroy()
				(self.main_window_callback)()
				return False
		
		try:
			os.remove(filefolder2)
		except:
			pass
		
		try:
			os.mkdir(filefolder2)
		except:
			pass
	
		self.eraser=devede_delete.delete_files(self.filename,self.filefolder)
		hasfree,msg=self.check_free_space(self.filefolder,self.structure,self.actions,self.erase_temp,self.global_vars["menu_sound_duration"])
		if hasfree:
			self.window.hide()
			self.window.destroy()
			self.show_error(msg)
			(self.main_window_callback)()
			return False
	
		# erase all conflicting files
		
		self.eraser.delete_all()
		
		# now, create the XML files (even with VCD, SVCD or CVD, to check if we have write permissions)

		xml_files=devede_xml_menu.xml_files(self.partial,self.filename,self.filefolder,self.structure,self.global_vars,self.label)

		counter=0
		counter2=0
		if (self.disk_type=="dvd"):
			if xml_files.do_menus():
				nelements=xml_files.get_elements_per_menu()
				while (len(self.structure[counter:])!=0):
					self.queue.append(["M1",xml_files,counter,counter2])
					counter+=nelements
					counter2+=1

		self.init_queue()

		retorno=xml_files.create_files()
		if retorno!=None:
			self.window.hide()
			self.window.destroy()
			self.show_error(retorno)
			(self.main_window_callback)()
			return False
		
		self.runner=None
		if self.actions!=1: # want to do, at least, the DVD structure, or the VCD image
			if self.disk_type=="dvd":
				self.queue.append(["DVD_STRUCTURE"])
				if self.actions==3: # do DVD image too
					self.queue.append(["DVD_IMAGE"])
			else:
				self.queue.append(["CD_IMAGE"])
		
		self.queue.append(["END"])
		self.seconds=0
		self.total_done=0.0
		self.timer=gobject.timeout_add(250,self.time_callback)
		self.window.show()
		return True


	def time_callback(self):

		""" This method launches all the conversion stages when needed, using the standard executor
		interface to manage all of them in an easy way """

		self.total.set_text(str(self.current_action)+"/"+str(len(self.queue)-1))
		self.total.set_fraction(float(self.current_action)/(float(len(self.queue)-1)))
		if self.runner!=None:
			if self.runner.initerror:
				retval=-1;
			else:
				retval=self.runner.refresh()
			if retval==0: # no error, still running
				return True
			else:
				self.current_action+=1
				retval=self.runner.wait_end()
				if (retval!=0) or (self.runner.initerror):
					self.window.hide()
					self.window.destroy()
					if self.runner.print_error==None:
						self.runner.print_error=_("Unknown error")
					self.show_error(self.runner.print_error)
					(self.main_window_callback)()
					return False
				else:
					self.runner.end_process(self.eraser,self.erase_temp)
				self.runner=None
		
		action=self.queue[self.current_action]
		
		if action[0]=="M1":
			self.runner=action[1]
			self.runner.create_menu1(action[2],action[3],self.global_vars["multicore"])
			return True
		
		if (action[0]=='C') or (action[0]=='C1') or (action[0]=='C2'):
			title=action[1]
			chapter=action[2]
			if action[0]=="C":
				encpass = 0
			else:
				encpass = int(action[0][1])
			print "Segundos "+str(self.seconds)
			if (self.global_vars["use_ffmpeg"]):
				self.runner=devede_ffmpeg_convert.video_converter(self.global_vars,self.structure[title][chapter+1],self.filename,self.filefolder,self.partial,self.label,self.global_vars["disctocreate"],title+1,chapter+1,self.global_vars["multicore"],self.seconds, encpass,self.global_vars["AC3_fix"])
			else:
				self.runner=devede_video_convert.video_converter(self.global_vars,self.structure[title][chapter+1],self.filename,self.filefolder,self.partial,self.label,self.global_vars["disctocreate"],title+1,chapter+1,self.global_vars["multicore"],self.seconds, encpass,self.global_vars["AC3_fix"])
			return True
		
		if action[0]=="C2":
			title=action[1]
			chapter=action[2]
			if (self.global_vars["use_ffmpeg"]):
				self.runner=devede_ffmpeg_convert.video_converter(self.structure[title][chapter+1],self.filename,self.filefolder,self.partial,self.label,self.global_vars["disctocreate"],title+1,chapter+1,self.global_vars["multicore"],self.seconds, 2,self.global_vars["AC3_fix"])
			else:
				self.runner=devede_video_convert.video_converter(self.structure[title][chapter+1],self.filename,self.filefolder,self.partial,self.label,self.global_vars["disctocreate"],title+1,chapter+1,self.global_vars["multicore"],self.seconds, 2,self.global_vars["AC3_fix"])
			return True
		
		if action[0]=="S":
			title=action[1]
			chapter=action[2]
			sub_stream=action[3]
			self.runner=devede_subtitles.subtitles_adder(self.structure[title][chapter+1],self.filename,self.filefolder,self.partial,self.label,self.global_vars["disctocreate"],title+1,chapter+1,sub_stream)
			return True
		
		if action[0]=="PREVIEW":
			self.window.hide()
			self.window.destroy()
			if (sys.platform=="win32") or (sys.platform=="win64"):
				mplay="mplayer.exe"
			else:
		 		mplay="mplayer"
		 	fname=self.filefolder+"previewfile_01_01."
		 	if self.disk_type=="divx":
		 		fname+="avi"
		 	else:
		 		fname+="mpg"
			parameters=[mplay,"-sid","0",fname,"-loop","1"]
			newtree=devede_other.create_tree(self,"wpreviewagain_dialog",self.gladefile,False)
			w=newtree.get_object("wpreviewagain_dialog")
			while True:
				salida=devede_executor.executor("previewfile",self.filefolder,None)
				salida.launch_program(parameters,output=False)
				salida.wait_end()
				w.show()
				ret=w.run()
				w.hide()
				if ret!=-6:
					break
				while gtk.events_pending():	
					gtk.main_iteration()
			w.destroy()
			os.remove(fname)
			return False
		
		if action[0]=="DVD_STRUCTURE":
			self.runner=devede_dvd.dvd_generator(self.filename,self.filefolder,self.partial,self.label)		
			return True
		
		if action[0]=="CD_IMAGE":
			self.runner=devede_bincue.xvcd_generator(self.filename,self.filefolder,self.partial,self.label,self.structure,self.disk_type)
			return True

		if action[0]=="DVD_IMAGE":
			self.runner=devede_bincue.iso_generator(self.filename,self.filefolder,self.partial,self.label,self.iso_creator)
			return True
		
		if action[0]=="END":
			self.show_final_time()
			return False
		return True


	def show_final_time(self):
		if (self.erase_temp):
			self.eraser.delete_xml()

		self.window.hide()
		self.window.destroy()
		if (self.global_vars["shutdown_after_disc"]):
			print "\n\nApago el ordenador\n\n"
			failure=False
			
			# First, try with ConsoleKit
			try:
				bus = dbus.SystemBus()
				bus_object = bus.get_object("org.freedesktop.ConsoleKit", "/org/freedesktop/ConsoleKit/Manager")
				bus_object.Stop(dbus_interface="org.freedesktop.ConsoleKit.Manager")
			except:
				failure=True
			if (failure):
				failure=False
				
				# If it fails, try with HAL
				try:
					bus = dbus.SystemBus()
					bus_object = bus.get_object("org.freedesktop.Hal", "/org/freedesktop/Hal/devices/computer")
					bus_object.Shutdown(dbus_interface="org.freedesktop.Hal.Device.SystemPowerManagement")
				except:
					failure=True

			if (failure==False):
				gtk.main_quit()

		newtree=devede_other.create_tree(self,"wend_dialog",self.gladefile,False)
		label=newtree.get_object("elapsed")
		tiempo2=devede_other.return_time(time.time()-self.tiempo,True)
		label.set_text(tiempo2)
		window=newtree.get_object("wend_dialog")
		burn = newtree.get_object("burn_button")
		# only enable button if k3b is available
		# TODO: support other burners
		
		if (self.k3b_available==False) and (self.brasero_available==False):
			burn.set_sensitive(False)
		
		burn.connect('clicked', self.burn)
		window.show()
		window.run()
		window.hide()
		window.destroy()
		window = None
		newtree = None
		gc.collect()
		(self.main_window_callback)()

	def burn(self, widget):

		"""Burns resulting iso"""

		path = self.filefolder + self.filename + ".iso"
		print path
		parameters = []
		if (self.brasero_available):
			parameters.append("brasero")
			parameters.append("--image="+path)
		else:
			parameters.append("k3b")
			parameters.append("--burn")
			parameters.append(path)
		runner=devede_executor.executor()
		runner.launch_program(parameters,output=False)
		salida.wait_end()


	def show_error(self,message):
		
		self.window.hide()
		self.window.destroy()
		devede_dialogs.show_error(self.gladefile,message)
		return

