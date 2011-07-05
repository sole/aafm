#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import os

from TreeViewFile import TreeViewFile
from Aafm import Aafm


class Aafm_GUI:
	def __init__(self):
		
		# The super core
		self.aafm = Aafm('adb', os.getcwd(), '/mnt/sdcard/')

		self.basedir = os.path.dirname(os.path.abspath(__file__))

		builder = gtk.Builder()
		builder.add_from_file(os.path.join(self.basedir, "data/glade/interface.xml"))
		builder.connect_signals({ "on_window_destroy" : gtk.main_quit })
		self.window = builder.get_object("window")

		imageDir = gtk.Image()
		imageDir.set_from_file(os.path.join(self.basedir, './data/icons/folder.png'))
		imageFile = gtk.Image()
		imageFile.set_from_file(os.path.join(self.basedir, './data/icons/file.png'))
		
		# Host and device TreeViews
		self.host_treeViewFile = TreeViewFile(imageDir.get_pixbuf(), imageFile.get_pixbuf())
		self.host_treeViewFile.get_tree().connect('row-activated', self.host_navigate_callback)
		hostFrame = builder.get_object('frameHost')
		hostFrame.get_child().add(self.host_treeViewFile.get_view())

		self.device_treeViewFile = TreeViewFile(imageDir.get_pixbuf(), imageFile.get_pixbuf())
		self.device_treeViewFile.get_tree().connect('row-activated', self.device_navigate_callback)
		deviceFrame = builder.get_object('frameDevice')
		deviceFrame.get_child().add(self.device_treeViewFile.get_view())
		self.device_treeViewFile.get_tree().connect('button_press_event', self.on_device_tree_view_contextual_menu)

		# Progress bar
		self.progress_bar = builder.get_object('progressBar')

		# Some more subtle details...
		self.window.set_title("Android ADB file manager")
		#self.adb = 'adb'
		self.host_cwd = os.getcwd()
		self.device_cwd = '/mnt/sdcard/'

		self.refresh_host_files()
		self.refresh_device_files()

		# And we're done!
		self.window.show_all()


	def host_navigate_callback(self, widget, path, view_column):
		
		row = path[0]
		model = widget.get_model()
		iter = model.get_iter(row)
		is_dir = model.get_value(iter, 0)
		name = model.get_value(iter, 1)

		if is_dir:
			self.host_cwd = os.path.normpath(os.path.join(self.host_cwd, name))
			self.aafm.set_host_cwd(self.host_cwd)
			self.refresh_host_files()


	def device_navigate_callback(self, widget, path, view_column):

		row = path[0]
		model = widget.get_model()
		iter = model.get_iter(row)
		is_dir = model.get_value(iter, 0)
		name = model.get_value(iter, 1)

		if is_dir:
			self.device_cwd = os.path.normpath(os.path.join(self.device_cwd, name))
			self.aafm.set_device_cwd(self.device_cwd)
			self.refresh_device_files()

	
	def refresh_host_files(self):
		self.host_treeViewFile.load_data(self.dir_scan_host(self.host_cwd))


	def refresh_device_files(self):
		self.device_treeViewFile.load_data(self.dir_scan_device(self.device_cwd))


	""" Walks through a directory and return the data in a tree-style list 
		that can be used by the TreeViewFile """
	def dir_scan_host(self, directory):
		output = []

		root, dirs, files = next(os.walk(directory))

		dirs.sort()
		files.sort()

		output.append({'directory': True, 'name': '..', 'size': 0})

		for d in dirs:
			output.append({'directory': True, 'name': d, 'size': 0})

		for f in files:
			size = os.path.getsize(os.path.join(directory, f))
			output.append({'directory': False, 'name': f, 'size': size})

		return output

	""" Like dir_scan_host, but in the connected Android device """
	def dir_scan_device(self, directory):
		output = []
		
		entries = self.aafm.get_device_file_list()

		dirs = []
		files = []

		for filename, entry in entries.iteritems():
			if entry['is_directory']:
				dirs.append(filename)
			else:
				files.append(filename)

		dirs.sort()
		files.sort()

		output.append({'directory': True, 'name': '..', 'size': 0})

		for d in dirs:
			output.append({'directory': True, 'name': d, 'size': 0})

		for f in files:
			size = int(entries[f]['size'])
			output.append({'directory': False, 'name': f, 'size': size})

		return output

	def on_device_tree_view_contextual_menu(self, widget, event):
		if event.button == 3:
			builder = gtk.Builder()
			builder.add_from_file(os.path.join(self.basedir, "data/glade/menu_contextual_device.xml"))
			menu = builder.get_object("menu")
			builder.connect_signals({
				'on_menuDeviceDeleteItem_activate': self.on_device_delete_item_callback,
				'on_menuDeviceCreateDirectory_activate': self.on_device_create_directory_callback
			})

			menu.popup(None, None, None, event.button, event.time)
			return True
		
		# don't consume the event
		return False

	def on_device_delete_item_callback(self, widget):
		print 'delete', self, widget


	def on_device_create_directory_callback(self, widget):
		print 'create directory', self, widget

	def die_callback(self, widget, data=None):
		self.destroy(widget, data)


	def destroy(self, widget, data=None):
		gtk.main_quit()


	def main(self):
		gtk.main()


if __name__ == '__main__':
	gui = Aafm_GUI()
	gui.main()
