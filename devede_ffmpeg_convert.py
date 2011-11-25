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


import signal
import os
import sys
import re
import shutil
import math

import devede_other

import devede_executor

if (sys.platform == "win32") or (sys.platform=="win64"):
	import win32file

class video_converter(devede_executor.executor):
	
	def adjust_audiorate(self,audiorate,isdvd):
		
		""" Just in case, we choose the nearest legal value """

		if isdvd:
			values=[448,384,320,256,224,192,160,128,112,96,80,64,56,48,32]
		else:
			values=[384,320,256,224,192,160,128,112,96,80,64,56,48,32]
		
		for element in values:
			if audiorate>=element:
				return element

		return 32

	
	def __init__(self,global_vars,videofile,filename,filefolder,progresbar,proglabel,disctype,title,chapter,threads,seconds,encpass,fix_ac3):

		""" This class converts a video file to MPEG-1 or MPEG-2 format

		VIDEOFILE contains the parameters to convert the video
		FILENAME is the generic file name given by the user
		FILEFOLDER is the path where all the temporary and finall files will be created
		PROGRESBAR is the progress bar where the class will show the progress
		PROGLABEL is the label where the class will show what is it doing
		DISCTYPE can be dvd, vcd, svcd, cvd or divx
		TITLE and CHAPTER are the numbers used to identify the TITLE and CHAPTER number for this file
		THREADS is the number of threads to use
		SECONDS is the number of seconds we want to convert (for previews) 
		ENCPASS is the number of encoding pass"""
		
		devede_executor.executor.__init__(self,filename,filefolder,progresbar)
		self.printout=False

		self.percent2=120
		self.film_length=float(videofile["olength"])
		if seconds==0:
			self.divide=float(videofile["olength"])
			if (videofile["cutting"]==1) or (videofile["cutting"]==2): # if we want only one half of the file
				self.divide/=2
		else:
			self.divide=float(seconds)

		if self.divide==0:
			self.divide=1

		self.error=""
		progresbar.set_fraction(0)
		progresbar.set_text("")
		
		if videofile["ismpeg"]: # if the file hasn't to be converted, we simply copy or link it
			self.pulse=True
			self.print_error=_("File copy failed\nMaybe you ran out of disk space?")
			if seconds==0:
				texto=_("Copying the file")+"\n"
			else:
				texto=_("Creating preview")+"\n"
			proglabel.set_text(texto+videofile["filename"])
			currentfile=self.create_filename(filefolder+filename,title,chapter,disctype=="divx")
		
			print "\ncurrentfile is: ", currentfile , "\n" 

			try:
				os.remove(currentfile)
			except:
				pass

			if (sys.platform=="win32") or (sys.platform=="win64"):
				# links do not work on windows, so just copy the file
				# self.launch_shell('copy "'+videofile["path"].replace('"','""')+'" "'+currentfile+'"',output=False)
				# Only hardlinks are available on 2000 and XP, reparse points are available from vista onwards.
				win32file.CreateHardLink(currentfile, videofile["path"].replace('"','""'))
			else:
				if len(videofile["sub_list"])==0:
					self.launch_shell('ln -s "'+videofile["path"].replace('"','\\"')+'" "'+currentfile+'"',output=False)
				else:
					self.launch_shell('cp "'+videofile["path"].replace('"','\\"')+'" "'+currentfile+'"',output=False)
			return

		isvob=videofile["isvob"]

		self.pulse=False
		if seconds==0:
			texto=(_("Converting files from title %(title_number)s (pass %(pass_number)s)\n\n%(file_name)s") % {"title_number":str(title),"pass_number":str(encpass),"file_name":videofile["filename"]} )
			proglabel.set_text(texto) #+" "+str(title)+" Pass: "+ str(encpass) +"\n\n"+videofile["filename"] )
		else:
			texto=_("Creating preview")
			proglabel.set_text(texto+"\n"+videofile["filename"])

		addbars=False
		framerate=int(videofile["ofps"])
		videorate=int(videofile["vrate"])
		audiorate=self.adjust_audiorate(int(videofile["arate"]),disctype=="dvd")
		
		audio_final_rate=int(videofile["arateunc"])
		audiodelay=float(videofile["adelay"])
		final_framerate=float(videofile["fps"])
		aspect_ratio_original=videofile["oaspect"]
		aspect_ratio_final=videofile["aspect"]
		resx_final=videofile["width"]
		resy_final=videofile["height"]
		resx_original=videofile["owidth"]
		resy_original=videofile["oheight"]
		copy_audio=videofile["copy_audio"]
		sound51=videofile["sound51"]
		gop12=videofile["gop12"]
		audiostream=videofile["audio_stream"]
		swap_fields=videofile["swap_fields"]
		volume=videofile["volume"]

		if (videofile["resolution"]==0) and (disctype=="divx"):
			default_res=True
		else:
			default_res=False
		
		speed1,speed2=devede_other.get_speedup(videofile)
		if speed1==speed2:
			speedup=None
		else:
			speedup=str(speed1)+":"+str(speed2)
	
		if aspect_ratio_original<1.3:
			aspect_ratio_original=float(videofile["owidth"])/(float(videofile["oheight"]))
		if aspect_ratio_original<1.33333333:
			aspect_ratio_original=1.33333333
	
		max_videorate=int(videorate*2)
		min_videorate=int(videorate*0.75)
		
		dsize,minvid,maxvid=devede_other.get_dvd_size(None,disctype)
		
		if max_videorate>maxvid:
			max_videorate=maxvid
		if min_videorate<minvid:
			min_videorate=minvid
			
		if videofile["blackbars"]==0: # check if has to add black bars
			addbars=True
			if (videofile["rotate"]==90) or (videofile["rotate"]==270):
				resx_original2=resy_original
				resy_original2=resx_original
				aratio=1/aspect_ratio_original
			else:
				resx_original2=resx_original
				resy_original2=resy_original
				aratio=aspect_ratio_original

			if (resx_original2%2)==1:
				resx_original2+=1
			if (resy_original2%2)==1:
				resy_original2+=1
			
			resy_tmp = int(resy_final*aspect_ratio_final/aratio)
			resx_tmp = int(resx_final*aratio/aspect_ratio_final)
			
			
			if (resx_tmp>resx_final):
				resx_inter=resx_final
				resy_inter=resy_tmp
			else:
				resx_inter=resx_tmp
				resy_inter=resy_final
			
			#resx_inter=resx_original2
			#resy_inter=int((resy_original2*aspect_ratio_original)/aspect_ratio_final)
			if (resx_inter%2)==1:
				resx_inter-=1
			if (resy_inter%2)==1:
				resy_inter-=1
			
			#if ((resy_inter<resy_original) or (resy_original+5>resy_inter)):
			#	addbars=False

		if addbars==False:
			resx_inter=resx_final
			resy_inter=resy_final
		else:
			if (resx_inter==resx_final):
				addx=0
				addy=int((resy_final-resy_inter)/2)
				if(addy%2)==1:
					addy+=1
			else:
				addy=0
				addx=int((resx_final-resx_inter)/2)
				if(addx%2)==1:
					addx+=1
					
		
		command_var=["ffmpeg"]

		command_var.append("-i")
		command_var.append(videofile["path"])
		
		if (audiodelay!=0.0) and (copy_audio==False) and (isvob==False):
			command_var.append("-itsoffset")
			command_var.append(str(audiodelay))
			command_var.append("-i")
			command_var.append(videofile["path"])
			command_var.append("-map")
			command_var.append("1:0")
			command_var.append("-map")
			command_var.append("0:1")
		
		if (isvob==False):
			cmd_line=""
			
			extra_params=videofile["params_vf"] # take the VF extra params
			while (extra_params!=""):
				extra_params,new_param=devede_other.get_new_param(extra_params)
				if (new_param!="") and (new_param!=','):
					while (len(new_param)>1) and (new_param[0]==','):
						new_param=new_param[1:]
					while (len(new_param)>1) and (new_param[-1]==','):
						new_param=new_param[:-1]
					if new_param=="fifo":
						continue
					if cmd_line!="":
						cmd_line+=",fifo,"
					cmd_line+=new_param
			
			if videofile["deinterlace"]=="yadif":
				if (cmd_line!=""):
					cmd_line+=",fifo,"
				cmd_line+="yadif"
			
			vflip=0
			hflip=0
	
			if (videofile["rotate"]==90):
				if (cmd_line!=""):
					cmd_line+=",fifo,"
				cmd_line+="transpose=1"
			elif (videofile["rotate"]==270):
				if (cmd_line!=""):
					cmd_line+=",fifo,"
				cmd_line+="transpose=2"
			elif (videofile["rotate"]==180):
				vflip=1
				hflip=1
			
			if (videofile["vmirror"]):
				vflip=1-vflip
			if (videofile["hmirror"]):
				hflip=1-hflip
	
			if (vflip==1):
				if (cmd_line!=""):
					cmd_line+=",fifo,"
				cmd_line+="vflip"
			if (hflip==1):
				if (cmd_line!=""):
					cmd_line+=",fifo,"
				cmd_line+="hflip"
			
			if addbars and ((resx_inter!=resx_original) or (resy_inter!=resy_original)) and (default_res==False):
				if (cmd_line!=""):
					cmd_line+=",fifo,"
				cmd_line+="scale="+str(resx_inter)+":"+str(resy_inter)+",fifo,pad="+str(resx_final)+":"+str(resy_final)+":"+str(addx)+":"+str(addy)+":0x000000"
			
			if cmd_line!="":
				command_var.append("-vf")
				command_var.append(cmd_line)
			
		
		command_var.append("-y")

		vcd=False
		
		if (disctype!="divx"):
			command_var.append("-target")
			if (disctype=="dvd"):
				if final_framerate==30:
					command_var.append("ntsc-dvd")
				elif (framerate==24):
					command_var.append("film-dvd")
				else:
					command_var.append("pal-dvd")
			elif (disctype=="vcd"):
				vcd=True
				if final_framerate==30:
					command_var.append("ntsc-vcd")
				else:
					command_var.append("pal-vcd")
			elif (disctype=="svcd"):
				if final_framerate==30:
					command_var.append("ntsc-svcd")
				else:
					command_var.append("pal-svcd")
			elif (disctype=="cvd"):
				if final_framerate==30:
					command_var.append("ntsc-svcd")
				else:
					command_var.append("pal-svcd")
		else: # DivX
			command_var.append("-vcodec")
			command_var.append("mpeg4")
			command_var.append("-acodec")
			command_var.append("libmp3lame")
			command_var.append("-f")
			command_var.append("avi")
		
		if  (not isvob):
			command_var.append("-sn") # no subtitles

		if copy_audio or isvob:
			command_var.append("-acodec")
			command_var.append("copy")
		#else:
		#	if (disctype=="divx"):
		#		command_var.append("-acodec")
		#		command_var.append("mp3")

		#if (audiostream!=10000):
		#	command_var.append("-aid")
		#	command_var.append(str(audiostream))

		if isvob:
			command_var.append("-vcodec")
			command_var.append("copy")
		
		if (vcd==False):
			if final_framerate==30:
				if (framerate==24) and ((disctype=="dvd") or (disctype=="divx")):
					str_final_framerate="24000/1001"
					keyintv=15
					telecine=True
				else:
					str_final_framerate="30000/1001"
					keyintv=18
			else:
				str_final_framerate=str(int(final_framerate))
				keyintv=15
		
		if (disctype=="divx"):
			command_var.append("-g")
			command_var.append("300")
		elif gop12 and (isvob==False):
			command_var.append("-g")
			command_var.append("12")
		
		if seconds!=0:
			command_var.append("-t")
			command_var.append(str(seconds))
		else:
			if videofile["cutting"]==1: # first half only
				command_var.append("-t")
				command_var.append(str(videofile["olength"]/2))
			elif videofile["cutting"]==2: # second half only
				command_var.append("-ss")
				command_var.append(str((videofile["olength"]/2)-5)) # start 5 seconds before

		#if (audiodelay!=0.0) and (copy_audio==False) and (isvob==False):
		#	command_var.append("-delay")
		#	command_var.append(str(audiodelay))

		command_var.append("-ac")
		if (sound51) and ((disctype=="dvd") or (disctype=="divx")):
			command_var.append("6")
		else:
			command_var.append("2")

		#if (isvob==False) and (default_res==False):
		#	command_var.append("-ofps")
		#	command_var.append(str_final_framerate)

		if disctype=="divx":
			command_var.append("-vtag")
			command_var.append("DX50")

		lineatemp=""
		acoma=False;
		
		#if swap_fields:
		#	lineatemp+="phase=a"
		#	acoma=True
		
		passlog_var = None
		
		if (videofile["deinterlace"]!="none") and (videofile["deinterlace"]!="yadif") and (isvob==False):
			command_var.append("-deinterlace")
			
		print "Addbars "+str(addbars)+" resx_o "+str(resx_original)+" resy_o "+str(resy_original)
		print "resx_i "+str(resx_inter)+" resy_i "+str(resy_inter)
 
 		if (isvob==False) and (vcd==False):
				command_var.append("-s")
				command_var.append(str(resx_final)+"x"+str(resy_final))

		# Currently Mencoder supports up to 8 threads
		if isvob==False:
			if threads>8:
				nthreads=8
			else:
				nthreads=threads
			
			if nthreads>1:
				command_var.append("-threads")
				command_var.append(str(nthreads))

			command_var.append("-trellis")
			if videofile["trellis"]:
				command_var.append("1")
			else:
				command_var.append("0")
		
			if videofile["mbd"]==0:
				command_var.append("-mbd")
				command_var.append("0")
			elif videofile["mbd"]==1:
				command_var.append("-mbd")
				command_var.append("1")
			elif videofile["mbd"]==2:
				command_var.append("-mbd")
				command_var.append("2")
	
			if (vcd==False):
				command_var.append("-b")
				command_var.append(str(videorate)+"000")
		
			if disctype!="divx":
			#	lavcopts+=":keyint="+str(keyintv)
				if(copy_audio==False) and (vcd==False):
#					lavcopts+=":acodec="
#					if disctype=="dvd":
#						if fix_ac3:
#							lavcopts+="ac3_fixed"
#						else:
#							lavcopts+="ac3"
#					else:
#						lavcopts+="mp2"
					#lavcopts+=":abitrate="+str(audiorate)
					command_var.append("-ab")
					command_var.append(str(audiorate)+"000")

			if (default_res==False):
				command_var.append("-aspect")
				if aspect_ratio_final>1.4:
					command_var.append("16:9")
				else:
					command_var.append("4:3")
			
			passlog_var=None
			if (encpass>0)  and (isvob==False):
				command_var.append("-pass")
				command_var.append(str(encpass))
				passlog_var=os.path.join(filefolder,filename)+".log"
				if encpass==1:
					try:
						os.remove(passlog_var)
					except:
						 pass
					#if videofile["turbo1stpass"]:
					#	lavcopts+=":turbo"

#	
#		if (disctype=="divx") and (copy_audio==False) and (isvob==False):
#			lameopts="abr:br="+str(audiorate)
#			command_var.append("-lameopts")
#			extra_params=videofile["params_lame"] # take the LAME extra params
#			while (extra_params!=""):
#				extra_params,new_param=devede_other.get_new_param(extra_params)
#				if (new_param!="") and (new_param!=':'):
#					while (len(new_param)>1) and (new_param[0]==':'):
#						new_param=new_param[1:]
#					while (len(new_param)>1) and (new_param[-1]==':'):
#						new_param=new_param[:-1]
#					lameopts+=":"+new_param
#			command_var.append(lameopts)
	
		currentfile=self.create_filename(filefolder+filename,title,chapter,disctype=="divx")

		if (passlog_var != None) and (isvob==False):
			command_var.append("-passlogfile")
			command_var.append(passlog_var)

		if (encpass==1) and (isvob==False):
			command_var.append("-y")
			command_var.append("/dev/null")
		else:
			command_var.append(currentfile)
		

		extra_params=videofile["params"] # take the extra params
		while (extra_params!=""):
			extra_params,new_param=devede_other.get_new_param(extra_params)
			if new_param!="":
				command_var.append(new_param)

		self.print_error=_("Conversion failed.\nIt seems a bug of Mencoder.")
		if (videofile["params"]!="") or (videofile["params_vf"]!="") or (videofile["params_lame"]!=""):
			self.print_error+="\n"+_("Also check the extra params passed to Mencoder for syntax errors.")
		self.error_not_done=True
		self.launch_program(command_var,read_chars=300)
		


	def end_process(self,eraser,erase_temporal_files):

		return


	def getfloat(self,cadena,upper=0):
		
		pos=cadena.find(":")
		upper*=60
		if (pos==-1):
			try:
				val=upper+float(cadena)
			except:
				val=upper
		else:
			try:
				val2=upper+float(cadena[:pos])
			except:
				val2=upper
			val=self.getfloat(cadena[pos+1:],val2)
		return val


	def set_progress_bar(self):

		if self.pulse:
			self.bar.pulse()
			return True

		pos=self.cadena.find("time=")
		if pos==-1:
			return False # don't erase the string
		pos2=self.cadena.find("bitrate",pos+5)
		if pos2==-1:
			return False
		
		cadena2=self.cadena[pos+5:pos2]
		
		valuetemp=self.getfloat(cadena2)
		
		value=(100.0*valuetemp)/self.divide
		if (value!=self.percent2) or (self.percent2==120):
			if (value)>100.0:
				value=100.0
			self.bar.set_fraction(value/100.0)
			self.bar.set_text(str(int(value))+"%")
			self.percent2=value
			if self.error_not_done:
				self.error_not_done=False
				self.print_error=_("Conversion failed\nMaybe you ran out of disk space?")
		return True
