#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright 2006-2009 (C) Raster Software Vigo (Sergio Costas)
# Copyright 2006-2007 (C) Peter Gill - win32 parts

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
import shutil
import sys

def prepare_devede_font(home,font_path):
	
	""" This function copies the default font for subtitles into $HOME/.spumux
		It's made this way because Red Hat package mandates removing font files
		from RPM files, so DeVeDe must search in several directories """
	
	path_list=[font_path,"/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans.ttf","/usr/share/fonts/truetype/ttf-dejavu/dejavusans.ttf"]
	
	#if our font for subtitles isn't installed, we install it

	exists=True
	try:
		if (sys.platform!="win32") and (sys.platform!="win64"):
			fichero=open(home+".spumux/devedesans.ttf")
			fichero.close()
		else: # get home
			t=os.path.join(os.environ["WINDIR"], "Fonts", "devedesans.ttf")
			fichero=open(t)
			fichero.close()
		return True
	except:
		exists=False
		
	if exists:
		return

	if (sys.platform!="win32") and (sys.platform!="win64"):
		try:
			t=os.path.join(home,".spumux")
			print "Creating spumux directory"+str(t)
			os.mkdir(t)
		except:
			print "Already existed"
			pass

	for element in path_list:
		print element
		try:
			if (sys.platform=="win32") or (sys.platform=="win64"):
				print "win32"
				t=os.path.join(os.environ["WINDIR"], "Fonts" )#=r'C:\WINDOWS\Fonts\\'
				t2=os.path.join(t,"devedesans.ttf")
				# spummux needs font in the windows font directory
				print "\n\nFont Path: " , element
				print "\n\nT: " , t
				shutil.copyfile(element,t2)
			else:
				print "Hago"
				t=os.path.join(home,".spumux")
				t2=os.path.join(t,"devedesans.ttf")
				print t2
				shutil.copyfile(element,t2)
				print "hecho"
				#handle=subprocess.Popen("mkdir "+home+".spumux",bufsize=8192,shell=True)
				#handle.wait()
				#handle=subprocess.Popen("cp "+font_path+" "+home+".spumux/",bufsize=8192,shell=True)
				#handle.wait()
			print "retorno"
			return True
		except:
			print "fallo"
			pass
		
	return False