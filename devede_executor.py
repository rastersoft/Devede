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
import subprocess
import select
import time
if (sys.platform=="win32") or (sys.platform=="win64"):
	import win32api
	import win32process
	import win32con
	import time

import threading
import gobject

class executor:

	""" Base class for all launchers (Mplayer, Mencoder, SPUmux, DVDauthor, mkisofs...). """

	def __init__(self,filename=None,filefolder=None,progresbar=None):

		# FILENAME is the generic file name given by the user
		# FILEFOLDER is the path where all the temporary and finall files will be created
		# PROGRESBAR is the GtkProgressBar where the class will show the progress

		self.initerror=False
		self.handle=None

		if filename!=None:
			self.bar=progresbar
			if progresbar!=None:
				progresbar.set_text(" ")
			self.filefolder=filefolder
			self.filename=filename
			self.platform_win32=((sys.platform=="win32") or (sys.platform=="win64"))
			self.cadena=""
			self.printout=True
			self.print_error="Undefined error"


	def cancel(self):

		""" Called to kill this process. """

		if self.handle==None:
			return
		if (sys.platform=="win32") or (sys.platform=="win64"):
			try:
				win32api.TerminateProcess(int(self.handle._handle), -1)
			except Exception , err:
				print "Error: ", err
		else:
			os.kill(self.handle.pid,signal.SIGKILL)
		
	
	def wait_end(self):
		
		""" Wait until the process ends """
		
		if self.handle==None:
			return 0
		
		self.handle.wait()
		return self.handle.returncode


	def launch_shell(self,program,read_chars=80,output=True,stdinout=None):
		
		""" Launches a program from a command line shell. Usefull for programs like SPUMUX, which
		takes the input stream from STDIN and gives the output stream to STDOUT, or for programs
		like COPY, CP or LN """
		
		self.read_chars=read_chars
		self.output=output
		self.handle=None
				
		if stdinout!=None: # we want to apply a file as STDIN and another one as STDOUT
			lprogram=program+' < "'+stdinout[0]+'" > "'+stdinout[1]+'"'
			if (sys.platform=="win32") or (sys.platform=="win64"):
				try:
					pos=program.find(" ")
					if pos==-1:
						command=program
					else:
						command=program[:pos] # get the command itself (usually SPUMUX.EXE)
					wd=sys.path[-1:] # Current working Directory.  To work with py2exe
					b=os.path.join(wd[0], "bin", command)
					lprogram=lprogram.replace(command, '"' + b + '"')
					batfile=open(os.path.join(wd[0],"menu.bat"),"w")
					batfile.write(lprogram)
					batfile.close()
				except:
					return None
				lprogram=os.path.join(wd[0],"menu.bat")
		else:
			lprogram=program

		print "Launching shell program: "+str(lprogram)
		print

		try:
			if output:
				if (sys.platform=="win32") or (sys.platform=="win64"):
					handle=MyPopen(lprogram,shell=False,bufsize=32767,stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=win32process.CREATE_NO_WINDOW)
				else:
					handle=subprocess.Popen(lprogram,shell=True,bufsize=32767,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
			else:
				if (sys.platform=="win32") or (sys.platform=="win64"):
					handle=subprocess.Popen(lprogram,shell=True,stdin=subprocess.PIPE, stdout=subprocess.PIPE, creationflags=win32process.CREATE_NO_WINDOW)
				else:
					handle=subprocess.Popen(lprogram,shell=True)
		except OSError:
			print "error launching shell\n\n\n\n"
			pass
		else:
			self.handle=handle
			return handle

		print "Fallo"
		return None	


	def launch_program(self,program,read_chars=80,output=True,win32arg=True,with_stderr=True):

		""" Launches a program that can be located in any of the directories stored in PATHLIST """

		self.read_chars=read_chars
		self.output=output
		self.handle=None

		wd=sys.path[-1:] # working directory.  This works with py2exe
		if (sys.platform=="win32") or (sys.platform=="win64"):
			pathlist=[os.path.join(wd[0],"bin"),os.path.join(os.getcwd(),"bin"), r'C:\WINDOWS', r'C:\WINDOWS\system32', r'C:\WINNT']
		else:
			pathlist=["/usr/bin","/usr/local/bin","/usr/share/bin","/usr/share/local/bin","/bin",os.path.join(wd[0],"bin")]

		print "Launching program: ",
		for elemento in program:
			print str(elemento),
		print

		for elemento in pathlist:
			print "elemento: ", elemento
			if elemento[-1]!=os.sep:
				elemento+=os.sep
			try:
				program2=program[:]
				program2[0]=elemento+program2[0]
				if output:
					if with_stderr:
						if (sys.platform=="win32") or (sys.platform=="win64"):
							handle=MyPopen(program2,executable=program2[0],shell=False,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=win32process.CREATE_NO_WINDOW, threaded=win32arg, read=read_chars)
						else:
							handle=subprocess.Popen(program2,executable=program[0],shell=False,bufsize=32767,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
					else:
						if (sys.platform=="win32") or (sys.platform=="win64"):
							handle=MyPopen(program2,executable=program2[0],shell=False,stdin=subprocess.PIPE, stdout=subprocess.PIPE, creationflags=win32process.CREATE_NO_WINDOW, threaded=False, read=read_chars)
						else:
							handle=subprocess.Popen(program2,executable=program[0],shell=False,bufsize=32767,stdout=subprocess.PIPE)
				else:
					if (sys.platform=="win32") or (sys.platform=="win64"):
						handle=MyPopen(program2,executable=program2[0],shell=False,creationflags=win32process.CREATE_NO_WINDOW, threaded=win32arg, read=read_chars)
					else:
						handle=subprocess.Popen(program2,executable=program[0],shell=False)
			except OSError:
				print "error in launch program\n"
				pass
			else:
				self.handle=handle
				if (sys.platform=="win32") or (sys.platform=="win64"):
					handle.set_priority()
				return handle
		return None


	def refresh(self):
		
		""" Reads STDOUT and STDERR and refreshes the progress bar. """

		if self.handle==None:
			return -1 # there's no program running
		
		if self.output==False: # if we don't want to read the output...
			self.bar.pulse() # just PULSE the progress bar
			if self.handle.poll()==None:
				return 0 # if the program didn't end, return 0
			else:
				return 1 # and 1 if the program ended
		
		ret_value=1
		v1=[]
		while self.handle.poll()==None:
			if self.read_line_from_output():
				ret_value=0
				break
			
		if (self.set_progress_bar()): # progress_bar is defined in each subclass to fit the format
			self.cadena=""
		
		if ret_value==1: # read what remains in the STDOUT and STDERR queues
			while self.read_line_from_output():
				tmp=1
		
		return ret_value # 0: nothing to read; 1: program ended


	def read_line_from_output(self):
		if self.platform_win32:
			v1 = self.handle.recv_some()
		else:
			v1,v2,v3=select.select([self.handle.stderr,self.handle.stdout],[],[],0)

		if len(v1)==0:
			return True # nothing to read, so get out of the WHILE loop
		
		for element in v1:
			if (sys.platform=="win32") or (sys.platform=="win64"):
				readed = element#[0,self.read_chars]
				self.cadena+=readed
				if (self.printout) or (element==self.handle.stderr):
					print readed,
				break # this break statement and setting the priority lower in launch_program makes devede work a lot better on windows
			else:
				readed=element.readline(self.read_chars)
				self.cadena+=readed
				if (self.printout) or (element==self.handle.stderr):
					print readed,

		return False
	

	def set_progress_bar(self):
		
		# By default, just do nothing
		if self.filename!=None:
			self.bar.pulse()
		return True


	def create_filename(self,filename,title,file,avi):

		""" Starting from the generic filename, adds the title and chapter numbers and the extension """

		currentfile=filename+"_"
		if title<10:
			currentfile+="0"
		currentfile+=str(title)+"_"

		if file<10:
			currentfile+="0"

		if avi:
			currentfile+=str(file)+'.avi'
		else:
			currentfile+=str(file)+'.mpg'
		return currentfile


	def remove_ansi(self,line):
		
		output=""
		while True:
			pos=line.find("\033[") # try with double-byte ESC
			jump=2
			if pos==-1:
				pos=line.find("\233") # if not, try with single-byte ESC
				jump=1
			if pos==-1: # no ANSI characters; we ended
				output+=line
				break
			
			output+=line[:pos]
			line=line[pos+jump:]

			while True:
				if len(line)==0:
					break
				if (ord(line[0])<64) or (ord(line[0])>126):
					line=line[1:]
				else:
					line=line[1:]
					break
		return output


class MyPopen(subprocess.Popen):

	class Sender(gobject.GObject):
		def __init__(self):
			self.__gobject_init__()
	
	class PipeThread(threading.Thread):
		def __init__(self, parent, fin, chars=80):
			threading.Thread.__init__(self)
			self.chars=chars
			self.fin = fin
			self.sout = []
			self.parent = parent
			self.sender = parent.Sender()
			self.sender.connect("z_signal", parent.read_callback)
			#self.sout = ""
			
		def run(self):
			self.sender.connect("z_signal", self.parent.read_callback)
			while True:
				try:
					timer = threading.Timer(10, self.__alarm_handler)
					temp=self.fin.read(self.chars)
					if not temp: self.sout.append("")
					if not temp: break
					self.sender.emit("z_signal", temp)
					timer.cancel()
				except Exception, e:
					if not str(e) == 'timeout':  # something else went wrong ..
						pass
						#raise # got the timeout exception from alarm .. proc is hung; kill it
					break
					
		def __alarm_handler(self):
			print "Process read timeout exception"
			raise Exception("timeout")

		def get_output(self):
			return self.sout
				
		def reset(self):
			self.sout = []
			#self.sout = ""
		
	def __init__(self, args=None, bufsize=0, executable=None, stdin=None, stdout=None, stderr=None, preexec_fn=None, close_fds=False, shell=False, cwd=None, env=None, universal_newlines=False, startupinfo=None, creationflags=0, threaded=True, read=80):
		subprocess.Popen.__init__(self,args=args, bufsize=bufsize, executable=executable, stdin=stdin, stdout=stdout, stderr=stderr, preexec_fn=preexec_fn, close_fds=close_fds, shell=shell, cwd=cwd, env=env, universal_newlines=universal_newlines, startupinfo=startupinfo, creationflags=creationflags)
		
		self.sout = []
		self.lock = threading.Lock()
		
		if not threaded:
			pass
		else:
			try:
				gobject.type_register(self.Sender)
				gobject.signal_new("z_signal", self.Sender, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (object,))
			except:
				print "Error registering z_signal"
			
			self.out_pipe, self.err_pipe = self.PipeThread(self, self.stdout, read), self.PipeThread(self, self.stderr)
			self.out_pipe.start(), self.err_pipe.start()
	
	def read_callback(self, object, data):
		self.__set_data(data)
		#print "Data Received:", data
	
	def __set_data(self, data):
		
		self.lock.acquire()
		self.sout.append(data)
		self.lock.release()
		
	def __get_data(self):
		self.lock.acquire()
		out = self.sout
		self.sout = []
		self.lock.release()
		return out
	
	def is_data(self):
		self.lock.acquire()
		value = self.sout
		self.lock.release()
		if len(value) > 0:
			return True
		return False
	
	def recv_some(self):
		"""
		Returns a copy of the lists holding stdout and stderr
		Before returning it clears the original lists
		"""

		out = self.__get_data()
		time.sleep(0.02)
		return out #[out, err]


	def set_priority(self, pid=None, priority=0):

		"""
		Set the Priority of a Windows Process.  Priority is a value between 0-5 where
		2 is normal priority.  Defaults to lowest Priority.
		"""
		priority_classes=[win32process.IDLE_PRIORITY_CLASS,
						  win32process.BELOW_NORMAL_PRIORITY_CLASS,
						  win32process.NORMAL_PRIORITY_CLASS,
						  win32process.ABOVE_NORMAL_PRIORITY_CLASS,
						  win32process.HIGH_PRIORITY_CLASS,
						  win32process.REALTIME_PRIORITY_CLASS]
		if pid == None:
			pid=self.pid
		handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
		win32process.SetPriorityClass(handle, priority_classes[priority])
