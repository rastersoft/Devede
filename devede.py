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


import sys
import os
import pygtk # for testing GTK version number
pygtk.require ('2.0')
import gtk
import gobject
import subprocess
import locale
import gettext
import stat
import shutil
import pickle
import cairo

print "DeVeDe 3.22.0beta1"
if (sys.platform!="win32") and (sys.platform!="win64"):
	try:
		print "Locale: "+str(os.environ["LANG"])
	except:
		print "Locale not defined"

# append the directories where we install the devede's own modules
tipo=-1

try:
	fichero=open("./interface/wmain.ui","r")
	fichero.close()
	tipo=2
	found=True
except:
	found=False	

if found==False:
	try:
		fichero=open("/usr/share/devede/wmain.ui","r")
		fichero.close()
		tipo=0
		found=True
	except:
		found=False

if found==False:
	try:
		fichero=open("/usr/local/share/devede/wmain.ui","r")
		fichero.close()
		tipo=1
		found=True
	except:
		found=False

if tipo==0:
	#gettext.bindtextdomain('devede', '/usr/share/locale')
	#Note also before python 2.3 you need the following if
	#you need translations from non python code (glibc,libglade etc.)
	#there are other access points to this function
	#gtk.glade.bindtextdomain("devede","/usr/share/locale")
	#arbol=gtk.Builder("/usr/share/devede/devede.glade",domain="devede")
	# append the directories where we install the devede's own modules

	share_locale="/usr/share/locale"
	glade="/usr/share/devede"
	sys.path.append("/usr/lib/devede")
	font_path="/usr/share/devede"
	pic_path="/usr/share/devede"
	other_path="/usr/share/devede"
	help_path="/usr/share/doc/devede"
	print "Using package-installed files"
	
elif tipo==1:
	# if the files aren't at /usr, try with /usr/local
	#gettext.bindtextdomain('devede', '/usr/share/locale')
	#Note also before python 2.3 you need the following if
	#you need translations from non python code (glibc,libglade etc.)
	#there are other access points to this function
	#gtk.glade.bindtextdomain("devede","/usr/share/locale")
	#arbol=gtk.Builder("/usr/local/share/devede/devede.glade",domain="devede")

	share_locale="/usr/share/locale" # Are you sure?
	# if the files aren't at /usr, try with /usr/local
	glade="/usr/local/share/devede"
	sys.path.append("/usr/local/lib/devede")
	font_path="/usr/local/share/devede"
	pic_path="/usr/local/share/devede"
	other_path="/usr/local/share/devede"
	help_path="/usr/local/share/doc/devede"
	print "Using local-installed files"
	
elif tipo==2:
	# if the files aren't at /usr/local, try with ./
	#gettext.bindtextdomain('devede', './po/')
	#Note also before python 2.3 you need the following if
	#you need translations from non python code (glibc,libglade etc.)
	#there are other access points to this function
	#gtk.glade.bindtextdomain("devede","/usr/share/locale")
	#arbol=gtk.Builder("./devede.glade",domain="devede")
	
	# if the files aren't at /usr/local, try with ./
	share_locale="./po/"
	glade="./interface"
	sys.path.append(os.getcwd())#("./")
	font_path=os.getcwd()#"./"
	pic_path=os.path.join(font_path, "pixmaps") #pic_path=font_path
	other_path=os.path.join(font_path,"pixmaps")
	help_path=os.path.join(font_path,"doc")
	print "Using direct files"
	
else:
	print "Can't locate extra files. Aborting."
	sys.exit(1)


#####################
#   GetText Stuff   #
#####################

gettext.bindtextdomain('devede',share_locale)
locale.setlocale(locale.LC_ALL,"")
gettext.textdomain('devede')
gettext.install("devede",localedir=share_locale) # None is sys default locale
#   Note also before python 2.3 you need the following if
#   you need translations from non python code (glibc,libglade etc.)
#   there are other access points to this function
#gtk.glade.bindtextdomain("devede",share_locale)

arbol=gtk.Builder()
arbol.set_translation_domain("devede")

#   To actually call the gettext translation functions
#   just replace your strings "string" with gettext("string")
#   The following shortcut are usually used:
_ = gettext.gettext

try:
	import devede_other
except:
	print "Failed to load modules DEVEDE_OTHER. Exiting"
	sys.exit(1)
try:
	import devede_convert
except:
	print "Failed to load modules DEVEDE_CONVERT. Exiting"
	sys.exit(1)
try:
	import devede_newfiles
except:
	print "Failed to load module DEVEDE_NEWFILES. Exiting"
	sys.exit(1)
try:
	import devede_xml_menu
except:
	print "Failed to load module DEVEDE_XML_MENU"
	sys.exit(1)

try:
	import devede_disctype
except:
	print "Failed to load module DEVEDE_DISCTYPE"
	sys.exit(1)

try:
	import devede_fonts
except:
	print "Failed to load module DEVEDE_FONTS"
	sys.exit(1)


home=devede_other.get_home_directory()

#locale.setlocale(locale.LC_ALL,"")
#gettext.textdomain('devede')
#_ = gettext.gettext

# global variables used (they are stored in a single dictionary to
# avoid true global variables):
# there are these two that aren't stored in the dictionary because they are very widely used:
# arbol
# structure

global_vars={}

if pic_path[-1]!=os.sep:
	pic_path+=os.sep

def get_number(line):
		
	pos=line.find(":")
	if pos==-1:
		return -1
	
	return int(line[pos+1:])

def get_cores():
		
	""" Returns the number of cores available in the system """
	if (sys.platform=="win32") or (sys.platform=="win64"):
		logical_cores = win32api.GetSystemInfo()[5] #Logical Cores
		return logical_cores

	failed=False
	try:
		proc=open("/proc/cpuinfo","r")
	except:
		failed=True
		
		
	if failed:
		# If can't read /proc/cpuinfo, try to use the multiprocessing module
		try:
			import multiprocessing
			return multiprocessing.cpu_count()
		except:
			pass
		return 1 # if we can't open /PROC/CPUINFO, return only one CPU (just in case)
	
	siblings=1 # default values
	cpu_cores=1 # for siblings and cpu cores
	notfirst=False
	ncores=0
	while(True):
		line=proc.readline()
		
		if (((line[:9]=="processor") and notfirst) or (line=="")):
			
			# each entry is equivalent to CPU_CORES/SIBLINGS real cores
			# (always 1 except in HyperThreading systems, where it counts 1/2)
			
			ncores+=(float(cpu_cores))/(float(siblings))
			siblings=1
			cpu_cores=1

		if line=="":
			break
			
		if line[:9]=="processor":
			notfirst=True
		elif (line[:8]=="siblings"):
			siblings=get_number(line)
		elif (line[:9]=="cpu cores"):
			cpu_cores=get_number(line)

	if(ncores<=1.0):
		return 1
	else:
		return int(ncores)

global_vars["PAL"]=True
global_vars["disctocreate"]=""
global_vars["path"]=pic_path
global_vars["install_path"]=other_path
global_vars["menu_widescreen"]=False
global_vars["gladefile"]=glade
global_vars["erase_temporary_files"]=True
global_vars["number_actions"]=1
global_vars["expand_advanced"]=False
global_vars["erase_files"]=True
global_vars["action_todo"]=2
global_vars["filmpath"]=""
global_vars["help_path"]=help_path
global_vars["finalfolder"]=""
global_vars["sub_codepage"]="ISO-8859-1"
global_vars["sub_language"]="EN (ENGLISH)"
global_vars["with_menu"]=True
global_vars["AC3_fix"]=False
global_vars["cores"]=get_cores()
global_vars["use_ffmpeg"]=True
global_vars["warning_ffmpeg"]=False
global_vars["shutdown_after_disc"]=False

global_vars["menu_top_margin"]=0.125
global_vars["menu_bottom_margin"]=0.125
global_vars["menu_left_margin"]=0.1
global_vars["menu_right_margin"]=0.1
#global_vars[""]=""

print "Cores: "+str(global_vars["cores"])

if font_path[-1]!=os.sep:
	font_path+=os.sep
font_path+="devedesans.ttf"
global_vars["font_path"]=font_path

print "Entro en fonts"
fonts_found=devede_fonts.prepare_devede_font(home,font_path)
print "Salgo de fonts"

devede_other.load_config(global_vars) # load configuration

errors="" # check for installed programs
if (sys.platform=="win32") or (sys.platform=="win64"):
	try:
		devede_other.check_program(["mplayer.exe", "-v"])
	except:
		errors+="mplayer\n"
	try:
		devede_other.check_program(["mencoder.exe", "-msglevel", "help"])
	except:
		errors+="mencoder\n"
	try:
		devede_other.check_program(["dvdauthor.exe", "--help"])
	except:
		errors+="dvdauthor\n"
	try:
		devede_other.check_program(["vcdimager.exe", "--help"])
	except:
		errors+="vcdimager\n"
	try:
		devede_other.check_program(["iconv.exe", "--help"])
	except:
		errors+="iconv\n"
	
	try:
		devede_other.check_program(["mkisofs.exe"])
		mkisofs=True
		global_vars["iso_creator"]="mkisofs.exe"
	except:
		mkisofs=False

	if mkisofs==False:
		try:
			devede_other.check_program(["genisoimage.exe"])
			global_vars["iso_creator"]="genisoimage.exe"
		except:
			errors+="genisoimage/mkisofs\n"

	try:
		devede_other.check_program(["spumux.exe", "--help"])
	except:
		errors+="spumux\n"

else:

	if 127==devede_other.check_program("mplayer -v"):
		errors+="mplayer\n"
	if 127==devede_other.check_program("mencoder -msglevel help"):
		errors+="mencoder\n"
	if 127==devede_other.check_program("ffmpeg --help"):
		errors+="ffmpeg\n"
	if 127==devede_other.check_program("dvdauthor --help"):
		errors+="dvdauthor\n"
	if 127==devede_other.check_program("vcdimager --help"):
		errors+="vcdimager\n"
	if 127==devede_other.check_program("iconv --help"):
		errors+="iconv\n"
	if 127==devede_other.check_program("mkisofs -help"):
		if 127==devede_other.check_program("genisoimage -help"):
			errors+="genisoimage/mkisofs\n"
		else:
			global_vars["iso_creator"]="genisoimage"
	else:
		global_vars["iso_creator"]="mkisofs"

	if 127==devede_other.check_program("spumux --help"):
		errors+="spumux\n"


def program_exit(widget):
	
	gtk.main_quit()


if errors!="":
	arbol.add_from_file(os.path.join(glade,"wprograms.ui"))
	w=arbol.get_object("programs_label")
	w.set_text(errors)
	wprograms=arbol.get_object("wprograms")
	wprograms.show()
	w=arbol.get_object("program_exit")
	w.connect("clicked",program_exit)
	wprograms.connect("destroy",program_exit)
elif fonts_found==False:
	arbol.add_from_file(os.path.join(glade,"wnofonts.ui"))
	wprograms=arbol.get_object("wnofonts")
	wprograms.show()
	w=arbol.get_object("fonts_program_exit")
	w.connect("clicked",program_exit)
	wprograms.connect("destroy",program_exit)
else:
	new_file=devede_disctype.disctype(global_vars)

gtk.main()
print "Saving configuration"
devede_other.save_config(global_vars)
print "Exiting"
print "Have a nice day"
sys.stdout.flush()
sys.stderr.flush()
