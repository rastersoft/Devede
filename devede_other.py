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


###########################################################################
# This block contains generic help functions that are used in the program #
###########################################################################

import os
import subprocess
import stat
import sys
import shutil
import cairo
import gtk
import struct

import devede_executor


class check_utf(devede_executor.executor):
	
	""" This class allows to detect if a file is pure ASCII, UTF-8 or UTF-16, and allows
		to convert from UTF-16 to UFT-8 """
	
	def check_ascii(self,filename):
		
		try:
			file=open(filename,"rb")
		except:
			return False
		
		while True:
			element=file.read(1)
			if len(element)==0:
				return True
			if ord(element)>127:
				return False
	

	def read_utf8_element(self,file,base_value,nb):
		
		value=base_value
		for counter in range(nb-1):
			element=file.read(1)
			if element=="":
				return False
			if (ord(element)>191) or (ord(element)<128):
				return False
			value*=64 # rotate value 6 bits to the left
			value+=ord(element)-128
		return value

	
	def check_utf8(self,filename):
		
		try:
			file=open(filename,"rb")
		except:
			return False
		
		while True:
			el=file.read(1)
			if el=="":
				file.close()
				return True
			element=ord(el)
	
			if element<128:
				continue
			
			if element<194: # it's a mid-sequence element or a 2-byte start sequence for an element smaller than 128
				print "Elemento 1"
				file.close()
				return False # invalid element found
			
			if element<224: # two-byte element
				value=self.read_utf8_element(file,element-192, 2)
				if value==False:
					print "Elemento 2"
					file.close()
					return False # invalid sequence
				if value<128:
					print "Elemento 3"
					file.close()
					return False # invalid value for a 2-byte sequence
				continue
				
			if element<240: # three-byte element
				value=self.read_utf8_element(file,element-224, 3)
				if value==False:
					print "Elemento 4"
					file.close()
					return False # invalid sequence
				if value<2048:
					print "Elemento 5"
					file.close()
					return False # invalid value for a 3-byte sequence
				continue
			
			if element<245: # four-byte element
				value=self.read_utf8_element(file,element-240, 4)
				if value==False:
					print "Elemento 6"
					file.close()
					return False # invalid sequence
				if value<65536:
					print "Elemento 7"
					file.close()
					return False # invalid value for a 4-byte sequence
				continue
			
			file.close()
			return False # invalid value


	def read_16(self,file,format_b):
		element=file.read(2)
		if element=="":
			return ""
		if len(element)!=2:
			return False
		value=struct.unpack(format_b,element)[0]
		return value

	
	def read_full16(self,file,format_b):
		value=self.read_16(file, format_b)
		if value=="":
			return True # end of file
		if value==False:
			return False
		if (value>=56320) and (value<=57343): # invalid value
			return False
		if (value>55295) and (value<56320): # surrogate pair
			value-=55296
			value2=self.read_16(file, format_b)
			if (value2==False) or (value2==""):
				return False
			if (value2<56320) or (value2>57343): # invalid surrogate pair
				return False
			value2-=56320
			return ((value*1024+value2)+65536)
		else:
			return value
	
	
	def write_utf8(self,file,value):
		
		if value<128:
			file.write(struct.pack("B",value))
		elif value<2048:
			v1=(value/64) & 31
			v2= value     & 63
			file.write(struct.pack("BB",v1+192,v2+128))
		elif value<65536:
			v1=(value/4096) & 15
			v2=(value/64)   & 63
			v3= value       & 63
			file.write(struct.pack("BBB",v1+224,v2+128,v3+128))
		else:
			v1=(value/262143) & 7
			v2=(value/4096)   & 63
			v3=(value/64)     & 63
			v4= value         & 63
			file.write(struct.pack("BBBB",v1+240,v2+128,v3+128,v4+128))		   
	
	
	def check_utf16BE(self,filename):
		
		try:
			file=open(filename,"rb")
		except:
			return False
		value=self.read_16(file, ">H")
		file.close()
		if value==65279:
			return True
		return False


	def check_utf16LE(self,filename):
		
		try:
		  file=open(filename,"rb")
		except:
			return False
		value=self.read_16(file, "<H")
		file.close()
		if value==65279:
			return True
		return False
	
	
	def check_utf16(self,filename,big_endian):
		
		try:
			file=open(filename,"rb")
		except:
			return False
		if big_endian:
			format_b=">H"
		else:
			format_b="<H"
		while True:
			value=self.read_full16(file, format_b)
			if value==True:
				print "True"
				return True
			if value==False:
				print "False"
				return False
			# value can be an integer too, that's why I put both IFs

	
	def convert_to_UTF8(self,infile_n,outfile_n,origin_format):
		
		command_line='iconv -f '+str(origin_format)+' -t UTF-8 "'+str(infile_n)+'" > "'+str(outfile_n)+'"'
		return self.launch_shell(command_line).wait()
	
	
	def convert_16_to_8(self,infile_n,outfile_n):
		
		if self.check_utf16BE(infile_n):
			format_b=">H"
		else:
			format_b="<H"
		
		infile=open(infile_n,"rb")
		outfile=open(outfile_n,"wb")
		
		first=True
		while True:
			value=self.read_full16(infile, format_b)
			if (value==65279) and first:
				first=False
				continue
			first=False
			if (value==True) or (value==False):
				break
			self.write_utf8(outfile, value)
		infile.close()
		outfile.close()
		return value
	
	
	def do_check(self,filename):
		
		""" Checks if a file is pure ASCII, UTF-8, UTF-16 or Unknown """
		
		self.type="Unknown"
		
		if self.check_ascii(filename):
			self.type="ascii"
			return self.type
		
		if self.check_utf8(filename):
			self.type="utf8"
			return self.type
		
		if (self.check_utf16BE(filename)):
			if (self.check_utf16(filename,True)):
				self.type="utf16"
			return self.type 
		
		if (self.check_utf16LE(filename)):
			if (self.check_utf16(filename,False)):
				self.type="utf16"
			return self.type
		
		return self.type



def get_speedup(videofile):
	
	""" configure speedup values when the original file
		is 23.976 or 24 fps and final file is 25 fps (PAL)
		this allows to avoid jerky jumps during reproduction """
		
	# First, check if the original is XX.9XX or XX.000 fps
	
	rational_fps=False
	pos=videofile["ofps2"].find(".")
	if (pos!=-1) and (len(videofile["ofps2"])>(pos+1)):
		if (videofile["ofps2"][pos+1]=="9"):
			rational_fps=True
			
	# if it's rational, we have to use a different pair of values to achieve good precission
	
	if (videofile["ofps"]==24) and (videofile["fps"]==25) and (videofile["copy_audio"]==False) and (videofile["ismpeg"]==False):
		if rational_fps:
			return 25025,24000
		else:
			return 25,24
	else:
		return 1,1


def get_font_params(font_name):
	
	font_elements=[]
	font_temp=font_name

	font_elements=font_name.split(" ")
	
	if (len(font_elements))<2:
		fontname="Sans"
		fontstyle=cairo.FONT_WEIGHT_NORMAL
		fontslant=cairo.FONT_SLANT_NORMAL
		fontsize=12
	else:
		fontname=""
		fontstyle=cairo.FONT_WEIGHT_NORMAL
		fontslant=cairo.FONT_SLANT_NORMAL
		for counter2 in range(len(font_elements)-1):
			if font_elements[counter2]=="Bold":
				fontstyle=cairo.FONT_WEIGHT_BOLD
			elif font_elements[counter2]=="Italic":
				fontslant=cairo.FONT_SLANT_ITALIC
			else:
				fontname+=" "+font_elements[counter2]
		if fontname!="":
			fontname=fontname[1:]
		else:
			fontname="Sans"

	try:
		fontsize=float(font_elements[-1])
	except:
		fontsize=12
		
	return fontname,fontstyle,fontslant,fontsize


def calcula_tamano_parcial(vrate,arate,filesize,length,subs,ismpeg,isvob,cutting,speed1,speed2):

	""" Calculates the estimated final size.
	
	VRATE and ARATE is the bit rate for video and audio.
	FILESIZE is the size of the original file.
	LENGTH is the file length in seconds
	SUBS is the number of subs
	ISMPEG is true if the file is already an MPEG-compliant file
	CUTTING is different than 0 if we are cutting the file in half.
	
	"""

	if (speed1!=speed2): # we are speeding up the film, so we must take it into account
		length=int((float(length))*((float(speed2))/(float(speed1))))

	if ismpeg or isvob:
		l=filesize/1000
	else:
		l=float(((vrate+arate)*length)/8)	
		if cutting!=0:
			l/=2
	l+=float((8*subs*length)/8) # add the subtitles (assume 8kbit/sec for each one)
	return l


def calcule_menu_size(structure,sound_duration):

	# each menu needs 1128 kbits/sec * sound_duration / 8
	return (141*sound_duration)*((len(structure)+9)/10)


def calcula_tamano_total(structure,sound_duration,disktype):

	""" Calculates the total size of the DVD """

	print "Calculating size for disk :"+str(disktype)
	total=0.0
	for element in structure:
		if len(element)>1:
			for film in element[1:]:
				speed1,speed2=get_speedup(film)
				total+=calcula_tamano_parcial(film["vrate"],film["arate"],film["filesize"],film["olength"],len(film["sub_list"]),film["ismpeg"],film["isvob"],film["cutting"],speed1,speed2)

	if disktype=="dvd":
		total+=calcule_menu_size(structure,sound_duration)

	return total


def check_program(programa):

	""" This function allows to check that a program is available in the system, just
	by calling it without arguments and checking the error returned """

	if (sys.platform=="win32") or (sys.platform=="win64"):
		launcher=devede_executor.executor()
		p=launcher.launch_program(programa,win32arg=False)
	else:
		p=subprocess.Popen(programa+" >/dev/null 2>/dev/null",shell=True)

	p.wait()
	return p.returncode


def load_config(global_vars):

	""" Load the configuration """
	home=get_home_directory()
	global_vars["PAL"]=True
	global_vars["multicore"]=1 # it shouldn't use multicore by default

	# TODO change to allow a windows temp directory

	if (sys.platform=="win32") or (sys.platform=="win64"):
		#global_vars["temp_folder"]=os.environ["TEMP"]
		global_vars["temp_folder"]=os.path.join(home,"Local Settings", "Temp")
	else:
		global_vars["temp_folder"]="/var/tmp"
	
	print "Temp Directory is: " , global_vars["temp_folder"]
	
	if (sys.platform=="win32") or (sys.platform=="win64"):
		home=os.path.join(home,"Application Data", "devede","devede.conf")
	else:
		home+=".devede"

	print "home load: ", home
	menuformat_found=False
	try:
		archivo=open(home,"r")
		while True:
			linea=archivo.readline()
			print "linea: ", linea
			if linea=="":
				break
			if linea[-1]=="\n":
				linea=linea[:-1]
			if linea=="pal":
				global_vars["PAL"]=True
			if linea=="ntsc":
				global_vars["PAL"]=False
			if linea[:13]=="video_format:":
				if linea[13:]=="pal":
					global_vars["PAL"]=True
				if linea[13:]=="ntsc":
					global_vars["PAL"]=False
			if linea[:12]=="temp_folder:":
				global_vars["temp_folder"]=linea[12:]
			if linea[:10]=="multicore:":
				global_vars["multicore"]=int(linea[10:]) # don't remember multicore
			if linea[:13]=="final_folder:":
				global_vars["finalfolder"]=linea[13:]
			if linea[:13]=="sub_language:":
				global_vars["sub_language"]=linea[13:]
			if linea[:13]=="sub_codepage:":
				global_vars["sub_codepage"]=linea[13:]
			#if linea[:]==":":
			#	global_vars[""]=linea[:]
		archivo.close()
	except IOError:
		pass


def save_config(global_vars):

	""" Stores the configuration """

	home=get_home_directory()

	if (sys.platform=="win32") or (sys.platform=="win64"):
		home=os.path.join(home,"Application Data", "devede")
		if not os.path.isdir(home):
			os.mkdir(home)
		home=os.path.join(home, "devede.conf")
	else:
		home+=".devede"

	if global_vars["temp_folder"][-1]!=os.sep:
		global_vars["temp_folder"]+=os.sep
	try:	
		archivo=open(home,"w")
		if global_vars["PAL"]:
			archivo.write("video_format:pal\n")
		else:
			archivo.write("video_format:ntsc\n")
		archivo.write("temp_folder:"+global_vars["temp_folder"]+"\n")
		archivo.write("multicore:"+str(global_vars["multicore"])+"\n")
		if global_vars["finalfolder"]!="":
			archivo.write("final_folder:"+str(global_vars["finalfolder"])+"\n")
		archivo.write("sub_language:"+str(global_vars["sub_language"])+"\n")
		archivo.write("sub_codepage:"+str(global_vars["sub_codepage"])+"\n")
		archivo.close()
	except IOError:
		pass


def get_new_param(parameters):

	""" This function groups the parameters passed by the user into a list """

	new_param=""
	
	while(True):
		if (parameters.find(" ")==0):
			parameters=parameters[1:] # erase blank spaces at start
		else:
			break

	if len(parameters)==0:
		return "",""
	
	p0=0
	while True:
		p1=parameters.find('\\',p0)
		p2=parameters.find(' ',p0)
		if p2==p1+1:
			p0=p2+1
		else:
			if p2<0: # no next space, take all the string
				retorno=""
				doble=False
				print parameters
				for letra in parameters:
					if (letra!='\\') or doble:
						retorno+=letra
						doble=False
					else:
						doble=True
				return "",retorno
			else:
				retorno=""
				doble=False
				print parameters[:p2]
				for letra in parameters[:p2]:
					if (letra!='\\') or doble:
						retorno+=letra
						doble=False
					else:
						doble=True
				return parameters[p2+1:],retorno


def get_home_directory():
	
	if (sys.platform=="win32") or (sys.platform=="win64"):
		home=os.environ["USERPROFILE"]
	else:
		home=os.environ.get("HOME")

	if home[-1]!=os.sep:
		home=home+os.sep

	print home
	return home


def return_time(seconds,empty):

	""" cuts a time in seconds into seconds, minutes and hours """

	seconds2=int(seconds)

	hours=str(seconds2/3600)
	if empty:
		if len(hours)==1:
			hours="0"+hours
	else:
		if hours=="0":
			hours=""
	if hours!="":
		hours+=":"
	
	minutes=str((seconds2/60)%60)
	if empty or (hours!=""):
		if len(minutes)==1:
			minutes="0"+minutes
	elif (minutes=="0") and (hours==""):
			minutes=""
	if minutes!="":
		minutes+=":"

	secs=str(seconds2%60)
	if (len(secs)==1) and (minutes!=""):
		secs="0"+secs

	return hours+minutes+secs


def get_max_titles(disctocreate):
	
	""" Returns the maximum number of titles/chapters for each type of disc """

	if disctocreate=="dvd":
		return 61
	else:
		return 99

def get_dvd_size(tree,disctocreate):
	
	""" Returns the size for the currently selected disk type, and the minimum and maximum
		videorate for the current video disk """
	
	if tree!=None:
		w=tree.get_object("dvdsize")
		active=w.get_active()
		
		# here we choose the size in Mbytes for the media
		if 0==active:
			tamano=170.0
		elif 1==active:
			tamano=700.0
		elif 2==active:
			tamano=750.0
		elif 3==active:
			tamano=1100.0
		elif 4==active:
			tamano=4200.0
		else:
			tamano=8000.0
	else:
		tamano=0
	
	if disctocreate=="vcd":
		minvrate=1152
		maxvrate=1152
	elif (disctocreate=="svcd") or (disctocreate=="cvd"):
		minvrate=400
		maxvrate=2300
	elif (disctocreate=="dvd"):
		minvrate=400
		maxvrate=8500
	elif (disctocreate=="divx"):
		minvrate=300
		maxvrate=6000
	
	tamano*=0.92 # a safe margin of 8% to ensure that it never will be bigger
				 # (it's important to have in mind the space needed by disk structures like
				 # directories, file entries, and so on)
	
	return tamano,minvrate,maxvrate


def get_picture_type(filename):
	
	try:
		f=open(filename,"r")
	except:
		return ""
	
	ftype=""
	line=f.read(4)

	if (line[0]=="\211") and (line[1:]=="PNG"):
		ftype="png"
	
	line2=f.read(7)
	if (line[0]=="\377") and (line[1]=="\330") and (line[2]=="\377") and (line[3]=="\340") and (line2[2:6]=="JFIF") and (line2[6]=="\000"):
		ftype="jpeg"
		
	f.close()
	print "tipo: "+str(ftype)
	return ftype


def create_tree(sobject,filename,builderpath="",autoconnect=True):
	
	tree=gtk.Builder()
	tree.set_translation_domain("devede")
	filename=os.path.join(builderpath,filename+".ui")
	print "Creating window "+filename
	tree.add_from_file(filename)
	if autoconnect:
		tree.connect_signals(sobject)

	return tree
