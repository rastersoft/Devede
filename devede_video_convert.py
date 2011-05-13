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
		
		""" Mencoder allows only a limited list of audio bitrates. This function chooses the nearest legal value """
		
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
			else:
				resx_original2=resx_original
				resy_original2=resy_original

			if (resx_original2%2)==1:
				resx_original2+=1
			if (resy_original2%2)==1:
				resy_original2+=1
			resx_inter=resx_original2
			resy_inter=int((resy_original2*aspect_ratio_original)/aspect_ratio_final)
			if (resy_inter%2)==1:
				resy_inter+=1
			
			# due to a bug in MENCODER, we put bars only up and down, never left and right,
			# and we don't scale it if we have to add only 4 or less lines, because it is
			# too much work for so little profit
			
			if ((resy_inter<resy_original) or (resy_original+5>resy_inter)):
				addbars=False

		if addbars==False:
			resx_inter=resx_original
			resy_inter=resy_original
		else:
			addx=0
			addy=int((resy_inter-resy_original)/2)
			if(addy%2)==1:
				addy+=1

		command_var=[]
		if (sys.platform!="win32") and (sys.platform!="win64"):
			command_var=["mencoder"]
		else:
			command_var=["mencoder.exe"]

		if (disctype=="dvd") or (disctype=="divx"):
			audio_desired_final_rate=48000
		else:
			audio_desired_final_rate=44100

		afvalues=""

		if isvob==False:
			if ((audio_final_rate!=audio_desired_final_rate) and (copy_audio==False)) or (speedup!=None):
				command_var.append("-srate")
				command_var.append(str(audio_desired_final_rate))
				afvalues+="lavcresample="+str(audio_desired_final_rate)
			
			if (copy_audio==False) and volume!=100:
				if afvalues!="":
					afvalues+=":"
				afvalues+="volume="+str(10*math.log(volume/10,10))

			# Add the speedup code

			if speedup!=None:
				command_var.append("-speed")
				command_var.append(speedup)

		if afvalues!="":
			command_var.append("-af")
			command_var.append(afvalues)
			
		command_var.append("-noautosub")

		command_var.append("-oac")
		if copy_audio or isvob:
			command_var.append("copy")
		else:
			if (disctype=="divx"):
				command_var.append("mp3lame")
			else:
				command_var.append("lavc")

		if (audiostream!=10000):
			command_var.append("-aid")
			command_var.append(str(audiostream))


		
		telecine=False
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
		
		if gop12:
			keyintv=12
		
		command_var.append("-ovc")
		if isvob:
			command_var.append("copy")
		else:
			command_var.append("lavc")
		
		if (disctype!="divx"):
			command_var.append("-of")
			command_var.append("mpeg")
			command_var.append("-mpegopts")
			if disctype=="dvd":
				if telecine and isvob==False:
					command_var.append("format=dvd:tsaf:telecine")
				else:
					command_var.append("format=dvd:tsaf")
			elif disctype=="vcd":
				command_var.append("format=xvcd")
			elif (disctype=="svcd") or (disctype=="cvd"):
				command_var.append("format=xsvcd")
			else:
				print "Error, disc format incorrect. Talk with the creator."
				sys.exit(1)

		if seconds!=0:
			command_var.append("-endpos")
			command_var.append(str(seconds))
		else:
			if videofile["cutting"]==1: # first half only
				command_var.append("-endpos")
				command_var.append(str(videofile["olength"]/2))
			elif videofile["cutting"]==2: # second half only
				command_var.append("-ss")
				command_var.append(str((videofile["olength"]/2)-5)) # start 5 seconds before

		if (audiodelay!=0.0) and (copy_audio==False) and (isvob==False):
			command_var.append("-delay")
			command_var.append(str(audiodelay))

		if sound51:
			command_var.append("-channels")
			command_var.append("6")

		if (isvob==False) and (default_res==False):
			command_var.append("-ofps")
			command_var.append(str_final_framerate)

		if disctype=="divx":
			command_var.append("-ffourcc")
			command_var.append("DX50")

		lineatemp=""
		acoma=False;
		
		if swap_fields:
			lineatemp+="phase=a"
			acoma=True
		
		extra_params=videofile["params_vf"] # take the VF extra params
		while (extra_params!=""):
			extra_params,new_param=devede_other.get_new_param(extra_params)
			if (new_param!="") and (new_param!=','):
				while (len(new_param)>1) and (new_param[0]==','):
					new_param=new_param[1:]
				while (len(new_param)>1) and (new_param[-1]==','):
					new_param=new_param[:-1]
				if acoma:
					lineatemp+=","
				lineatemp+=new_param
				acoma=True
		
		vmirror=0
		hmirror=0
		passlog_var = None
		
		if videofile["deinterlace"]!="none":
			if acoma:
				lineatemp+=","
			if videofile["deinterlace"]!="yadif":
				lineatemp+="pp="+videofile["deinterlace"]
			else:
				lineatemp+="yadif=0"
			acoma=True
			
		if videofile["rotate"]==180:
			vmirror=1-vmirror
			hmirror=1-hmirror
		
		if videofile["vmirror"]:
			vmirror=1-vmirror
		
		if videofile["hmirror"]:
			hmirror=1-hmirror
		
		if vmirror==1:
			if acoma:
				lineatemp+=","
			lineatemp+="flip"
			acoma=True
		
		if hmirror==1:
			if acoma:
				lineatemp+=","
			lineatemp+="mirror"
			acoma=True
		
		print "Addbars "+str(addbars)+" resx_o "+str(resx_original)+" resy_o "+str(resy_original)
		print "resx_i "+str(resx_inter)+" resy_i "+str(resy_inter)
		if addbars and ((resx_inter!=resx_original) or (resy_inter!=resy_original)) and (default_res==False):
			if acoma:
				lineatemp+=","
			lineatemp+="expand="+str(resx_inter)+":"+str(resy_inter)+":"+str(addx)+":"+str(addy)
			acoma=True

		if videofile["rotate"]==90:
			if acoma:
				lineatemp+=","
			lineatemp+="rotate=1"
			acoma=True
		
		if videofile["rotate"]==270:
			if acoma:
				lineatemp+=","
			lineatemp+="rotate=2"
			acoma=True

		if ((resx_inter!=resx_final) or (resy_inter!=resy_final)) and (default_res==False):
			if acoma:
				lineatemp+=","
			lineatemp+="scale="+str(resx_final)+":"+str(resy_final)
			acoma=True
		
		if disctype!="divx":
			if acoma:
				lineatemp+=","
			lineatemp+="harddup"
			acoma=True

		if (lineatemp!="") and (isvob==False):
			command_var.append("-vf")		
			command_var.append(lineatemp)

		if isvob==False:
			command_var.append("-lavcopts")
			
			lavcopts=""
			
			# Currently Mencoder supports up to 8 threads
			if threads>8:
				nthreads=8
			else:
				nthreads=threads
			
			if nthreads>1:
				lavcopts="threads="+str(nthreads)+":"
			lavcopts+="vcodec="
			if disctype=="vcd":
				lavcopts+="mpeg1video"
			elif disctype=="divx":
				lavcopts+="mpeg4"
			else:
				lavcopts+="mpeg2video"
		
			if videofile["trellis"]:
				lavcopts+=":trell"
		
			if videofile["mbd"]==0:
				lavcopts+=":mbd=0"	
			elif videofile["mbd"]==1:
				lavcopts+=":mbd=1"
			elif videofile["mbd"]==2:
				lavcopts+=":mbd=2"
	
			lavcopts+=":sc_threshold=1000000000:cgop"

			if disctype!="divx":
				lavcopts+=":vstrict=0:vrc_maxrate="+str(max_videorate)
				lavcopts+=":vrc_buf_size="
				if (disctype=="vcd"):
					lavcopts+="327"
				elif (disctype=="svcd") or (disctype=="cvd"):
					lavcopts+="917"
				elif (disctype=="dvd"):
					lavcopts+="1835"
			if disctype=="vcd":
				lavcopts+=":vrc_minrate="+str(min_videorate)
	
			lavcopts+=":vbitrate="+str(videorate)
		
			if disctype!="divx":
				lavcopts+=":keyint="+str(keyintv)
				if(copy_audio==False):
					lavcopts+=":acodec="
					if disctype=="dvd":
						if fix_ac3:
							lavcopts+="ac3_fixed"
						else:
							lavcopts+="ac3"
					else:
						lavcopts+="mp2"
					lavcopts+=":abitrate="+str(audiorate)

			if (default_res==False):
				if aspect_ratio_final>1.4:
					lavcopts+=":aspect=16/9"
				else:
					lavcopts+=":aspect=4/3"
			
			if encpass > 0:
				lavcopts+=":vpass=" + str(encpass)
				passlog_var = os.path.join(filefolder,filename)+".log"
				if encpass==1:
					try:
						os.remove(passlog_var)
					except:
						 pass
					if videofile["turbo1stpass"]:
						lavcopts+=":turbo"
				
	
			extra_params=videofile["params_lavc"] # take the LAVC extra params
			while (extra_params!=""):
				extra_params,new_param=devede_other.get_new_param(extra_params)
				if (new_param!="") and (new_param!=':'):
					while (len(new_param)>1) and (new_param[0]==':'):
						new_param=new_param[1:]
					while (len(new_param)>1) and (new_param[-1]==':'):
						new_param=new_param[:-1]
					lavcopts+=":"+new_param
			command_var.append(lavcopts)
	
		if (disctype=="divx") and (copy_audio==False) and (isvob==False):
			lameopts="abr:br="+str(audiorate)
			command_var.append("-lameopts")
			extra_params=videofile["params_lame"] # take the LAME extra params
			while (extra_params!=""):
				extra_params,new_param=devede_other.get_new_param(extra_params)
				if (new_param!="") and (new_param!=':'):
					while (len(new_param)>1) and (new_param[0]==':'):
						new_param=new_param[1:]
					while (len(new_param)>1) and (new_param[-1]==':'):
						new_param=new_param[:-1]
					lameopts+=":"+new_param
			command_var.append(lameopts)
	
		currentfile=self.create_filename(filefolder+filename,title,chapter,disctype=="divx")

		if (passlog_var != None):
			command_var.append("-passlogfile")
			command_var.append(passlog_var)

		command_var.append("-o")
		command_var.append(currentfile)
		command_var.append(videofile["path"])

		extra_params=videofile["params"] # take the extra params
		while (extra_params!=""):
			extra_params,new_param=devede_other.get_new_param(extra_params)
			if new_param!="":
				command_var.append(new_param)

		self.print_error=_("Conversion failed.\nIt seems a bug of Mencoder.")
		if (videofile["params"]!="") or (videofile["params_vf"]!="") or (videofile["params_lavc"]!="") or (videofile["params_lame"]!=""):
			self.print_error+="\n"+_("Also check the extra params passed to Mencoder for syntax errors.")
		self.error_not_done=True
		self.launch_program(command_var,read_chars=300)
		


	def end_process(self,eraser,erase_temporal_files):

		return


	def set_progress_bar(self):

		if self.pulse:
			self.bar.pulse()
			return True

		pos=self.cadena.find("Pos:")
		if pos==-1:
			return False # don't erase the string
		pos2=self.cadena.find("s",pos+3)
		if pos2==-1:
			return False
		valuetemp=float(self.cadena[pos+4:pos2])
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
