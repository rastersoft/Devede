#!/usr/bin/python

import os
from glob import glob
from distutils.core import setup
from distutils import dep_util

def get_mopath(pofile):
	# Function to determine right locale path for a .po file
	lang = os.path.basename(pofile)[:-3] # len('.po') == 3
	modir = os.path.join('locale', lang, 'LC_MESSAGES') # e.g. locale/fr/LC_MESSAGES/
	mofile = os.path.join(modir, 'devede.mo') # e.g. locale/fr/LC_MESSAGES/devede.mo
	return modir, mofile

def get_data_files():
	data_files = [
		(os.path.join('share', 'applications'), ['devede.desktop']),
		(os.path.join('share', 'pixmaps'), ['devede.svg']),
		(os.path.join('share', 'devede'), glob("interface/*")),
		(os.path.join('share', 'devede'), glob('pixmaps/*g')),
		(os.path.join('share', 'devede'), ['devede.svg']),
		(os.path.join('share', 'devede'), ['devedesans.ttf']),
		(os.path.join('share', 'devede', 'backgrounds'), glob('pixmaps/backgrounds/*')),
		(os.path.join('share', 'doc', 'devede', 'html'), glob('docs/html/*'))
	]

	for pofile in [f for f in os.listdir('po') if f.endswith('.po')]:
		pofile = os.path.join('po', pofile) # po/fr.po
		modir, mofile = get_mopath(pofile)
		target = os.path.join('share', modir) # share/locale/fr/LC_MESSAGES/
		data_files.append((target, [mofile]))

	return data_files

def get_py_modules():
	return [i.replace(".py","") for i in glob("devede_*.py")]

def compile_translations():
	for pofile in [f for f in os.listdir('po') if f.endswith('.po')]:
		pofile = os.path.join('po', pofile)
		modir, mofile = get_mopath(pofile)

		# create an architecture for these locales
		if not os.path.isdir(modir):
			os.makedirs(modir)

		if not os.path.isfile(mofile) or dep_util.newer(pofile, mofile):
			print 'compiling %s' % mofile
			# msgfmt.make(pofile, mofile)
			os.system("msgfmt \"" + pofile + "\" -o \"" + mofile + "\"")
		else:
			print 'skipping %s - up to date' % mofile

compile_translations()

setup(
	name = 'devede',
	version = '3.22.0',
	author = "Sergio Costas",
	author_email = "raster@rastersoft.com",
	url = "http://www.rastersoft.com/programas/devede.html",
	license = 'GPL-3',
	py_modules = get_py_modules(),
	scripts=['devede'],
	data_files = get_data_files()
)
