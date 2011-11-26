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

import devede_executor
import devede_other

class subtitles_adder(devede_executor.executor):
	
	def expand_xml(self,text):
		
		text=text.replace('&','&amp;')
		text=text.replace('<','&lt;')
		text=text.replace('>','&gt;')
		text=text.replace('"','&quot;')
		text=text.replace("'",'&apos;')
		return text

	
	def __init__(self,videofile,filename,filefolder,progresbar,proglabel,disctype,title,chapter,stream):

		""" This class adds the subtitles to an already converted file

		VIDEOFILE contains the parameters to convert the video
		FILENAME is the generic file name given by the user
		FILEFOLDER is the path where all the temporary and finall files will be created
		PROGRESBAR is the progress bar where the class will show the progress
		PROGLABEL is the label where the class will show what is it doing
		DISCTYPE can be dvd, vcd, svcd, cvd or divx
		TITLE and CHAPTER are the numbers used to identify the TITLE and CHAPTER number for this file
		STREAMS is the stream number (to allow to add several subtitles)
		"""

		devede_executor.executor.__init__(self,filename,filefolder,progresbar)
		progresbar.pulse()
		proglabel.set_text(_("Adding subtitles to")+"\n"+videofile["filename"])
		self.currentfile=self.create_filename(filefolder+filename,title,chapter,disctype=="divx")

		subtitle_list=videofile["sub_list"][stream]

		# generate the XML file

		self.error=""

		try:
			print "Trying to create "+filefolder+filename+"_sub.xml"
			fichero=open(filefolder+filename+"_sub.xml","w")
		except IOError:
			print "IOError en subtitulos"
			self.print_error=_("Failed to write to the destination directory.\nCheck that you have privileges and free space there.")
			self.initerror=True
			return
		
		fichero.write('<subpictures format="')
		if (videofile["fps"]==25) :
			fichero.write('PAL')
		else:
			fichero.write('NTSC')
		fichero.write('">\n\t<stream>')
		if (subtitle_list["sub_codepage"]!="UTF-8"):
			final_type="UTF-8"
			subfilename=os.path.join(filefolder,filename+"_sub_tmp.sub")
			self.deletesub=subfilename
			if 0!=devede_other.check_utf().convert_to_UTF8(subtitle_list["subtitles"],subfilename,subtitle_list["sub_codepage"]):
				#except IOError:
				print "IOError al convertir a UTF8"
				self.print_error=_("Failed to write to the destination directory.\nCheck that you have privileges and free space there.")
				self.initerror=True
				return
		else:
			self.deletesub=""
			final_type=subtitle_list["sub_codepage"]
			subfilename=subtitle_list["subtitles"]
		fichero.write('\n\t\t<textsub filename="'+self.expand_xml(subfilename)+'"')

		if (sys.platform=="win32") or (sys.platform=="win64"):
			if os.path.isfile(os.path.join(os.environ["WINDIR"],"Fonts","devedesans.ttf")):
				fichero.write('\n\t\tfont="devedesans.ttf"')
			else:
				fichero.write('\n\t\tfont="ARIAL.ttf"')
		else:
			fichero.write('\n\t\tfont="devedesans.ttf"')
		if ((subtitle_list["sub_codepage"]!="") and (subtitle_list["sub_codepage"]!="ASCII")):
			fichero.write('\n\t\tcharacterset="'+final_type+'"')
		fichero.write('\n\t\thorizontal-alignment="center"')

		if (videofile["fps"]==25):
			ancho=716
			alto=572
			tamanofont=videofile["subfont_size"]
		else:
			ancho=716
			alto=476
			tamanofont=videofile["subfont_size"]

		margin_hor=int((58*ancho)/720)
		margin_vert=int((28*alto)/576)
		bottom_margin=margin_vert

		fichero.write('\n\t\tmovie-width="'+str(ancho-4)+'"')
		fichero.write('\n\t\tmovie-height="'+str(alto-4)+'"')
		fichero.write('\n\t\tleft-margin="'+str(margin_hor)+'"')
		fichero.write('\n\t\tright-margin="'+str(margin_hor)+'"')

		if subtitle_list["subtitles_up"]:
			tamanofont-=1
			bottom_margin=4+(alto/8) # put it in the border of 16:9 aspect ratio

		fichero.write('\n\t\tbottom-margin="'+str(bottom_margin)+'"')
		fichero.write('\n\t\ttop-margin="'+str(margin_vert)+'"')

		fichero.write('\n\t\tfontsize="'+str(tamanofont)+'.0"')

		if (videofile["fps"]==30):
			if (videofile["ofps"]==24) and ((disctype=="dvd") or (disctype=="divx")):
				fps_out="24000/1001"
			else:
				fps_out="30000/1001"
		else:
			fps_out="25"

		if videofile["ismpeg"]:
			fps_out=videofile["ofps2"]
			print "FPS sub 1 original"
		else:
			print "FPS sub 1 final"

		fichero.write('\n\t\tmovie-fps="'+str(fps_out)+'"')
		speed1,speed2=devede_other.get_speedup(videofile)
		if speed1==speed2:
			fps_out_subs=fps_out
			print "FPS sub 2 final"
		else:
			if speed2==24:
				fps_out_subs="24"
			else:
				fps_out_subs=videofile["ofps2"]
			print "FPS sub 2 original"

		fichero.write('\n\t\tsubtitle-fps="'+fps_out_subs+'"')
		fichero.write('\n\t\tvertical-alignment="bottom" />')
		fichero.write("\n\t</stream>\n</subpictures>")
		fichero.close()
		
		comando=""
		if (sys.platform=="win32") or (sys.platform=="win64"):
			comando=["spumux.exe"]
			comando.append("-m")
			if disctype=="vcd":
				comando.append("svcd")
			else:
				comando.append(disctype)
			comando.append("-s")
			comando.append(str(stream))
			
			comando.append(filefolder+filename+"_sub.xml")
			comando.append("-i")
			comando.append(self.currentfile)
			comando.append("-o")
			comando.append(self.currentfile+".sub")
			self.print_error=_("Conversion failed.\nIt seems a bug of SPUMUX.")
			self.launch_program(comando,output=True)
		else:
			comando="spumux -m "
			if disctype=="vcd":
				comando+="svcd"
			else:
				comando+=disctype
		
			comando+=' -s '+str(stream)+' "'+filefolder+filename+'_sub.xml"'
		
			self.print_error=_("Conversion failed.\nIt seems a bug of SPUMUX.")
			self.launch_shell(comando,output=True,stdinout=[self.currentfile,self.currentfile+".sub"])


	def end_process(self,eraser,erase_temporal_files):

		shutil.move(self.currentfile+".sub", self.currentfile)
		if erase_temporal_files:
			eraser.delete_sub_xml(self.deletesub)
			


	def set_progress_bar(self):

		self.bar.pulse()		
		position=self.cadena.find("STAT: ")
		if (position!=-1):
			position2=self.cadena.find(".",position+6)
			if position2!=-1:
				self.bar.set_text(self.cadena[position:position2])
		return True
