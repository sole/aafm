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
		self.host_treeViewFile.get_tree().connect('button_press_event', self.on_host_tree_view_contextual_menu)

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


	def get_treeviewfile_selected(self, treeviewfile):
		values = []
		model, rows = treeviewfile.get_tree().get_selection().get_selected_rows()

		for row in rows:
			iter = model.get_iter(row)
			filename = model.get_value(iter, 1)
			is_directory = model.get_value(iter, 0)
			values.append({'filename': filename, 'is_directory': is_directory})

		return values


	def get_host_selected_files(self):
		return self.get_treeviewfile_selected(self.host_treeViewFile)

	def get_device_selected_files(self):
		return self.get_treeviewfile_selected(self.device_treeViewFile)


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

	def on_host_tree_view_contextual_menu(self, widget, event):
		if event.button == 3: # Right click
			builder = gtk.Builder()
			builder.add_from_file(os.path.join(self.basedir, 'data/glade/menu_contextual_host.xml'))
			menu = builder.get_object('menu')
			builder.connect_signals({
				'on_menuHostCopyToDevice_activate': self.on_host_copy_to_device_callback
			})

			# Ensure only right options are available
			num_selected = len(self.get_host_selected_files())
			has_selection = num_selected > 0

			menuCopy = builder.get_object('menuHostCopyToDevice')
			menuCopy.set_sensitive(has_selection)

			menu.popup(None, None, None, event.button, event.time)
			return True
		
		# Not consuming the event
		return False

	# Copy to device
	def on_host_copy_to_device_callback(self, widget):
		print 'copy to host'
		selected = self.get_host_selected_files()
		task = self.copy_to_device_task(selected)
		gobject.idle_add(task.next)

	def copy_to_device_task(self, rows):
		completed = 0
		total = len(rows)
		self.update_progress()

		for row in rows:
			filename = row['filename']
			full_host_path = os.path.join(self.host_cwd, filename)

			if os.path.isfile(full_host_path):
				full_device_path = self.device_cwd
			else:
				full_device_path = os.path.join(self.device_cwd, filename)

			self.aafm.copy_to_device(full_host_path, full_device_path)
			completed = completed + 1
			self.refresh_device_files()
			self.update_progress(completed * 1.0 / total)

			yield True

		yield False


	def on_device_tree_view_contextual_menu(self, widget, event):
		if event.button == 3: # Right click
			builder = gtk.Builder()
			builder.add_from_file(os.path.join(self.basedir, "data/glade/menu_contextual_device.xml"))
			menu = builder.get_object("menu")
			builder.connect_signals({
				'on_menuDeviceDeleteItem_activate': self.on_device_delete_item_callback,
				'on_menuDeviceCreateDirectory_activate': self.on_device_create_directory_callback,
				'on_menuDeviceRefresh_activate': self.on_device_refresh_callback,
				'on_menuDeviceCopyToComputer_activate': self.on_device_copy_to_computer_callback,
				'on_menuDeviceRenameItem_activate': self.on_device_rename_item_callback
			})

			# Ensure only right options are available
			num_selected = len(self.get_device_selected_files())
			has_selection = num_selected > 0
			menuDelete = builder.get_object('menuDeviceDeleteItem')
			menuDelete.set_sensitive(has_selection)
			
			menuCopy = builder.get_object('menuDeviceCopyToComputer')
			menuCopy.set_sensitive(has_selection)

			menuRename = builder.get_object('menuDeviceRenameItem')
			menuRename.set_sensitive(num_selected == 1)

			menu.popup(None, None, None, event.button, event.time)
			return True
		
		# don't consume the event, so we can still double click to navigate
		return False

	def on_device_delete_item_callback(self, widget):
		selected = self.get_device_selected_files()

		items = []

		for item in selected:
			items.append(item['filename'])

		result = self.dialog_device_delete_confirmation(items)

	def dialog_device_delete_confirmation(self, items):
		items.sort()
		joined = ', '.join(items)
		print joined
		dialog = gtk.MessageDialog(
			parent = None,
			flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
			type = gtk.MESSAGE_QUESTION,
			buttons = gtk.BUTTONS_OK_CANCEL,
			message_format = "Are you sure you want to delete %d items?" % len(items)
		)
		dialog.format_secondary_markup('%s will be deleted. This action cannot be undone.' % joined)
		dialog.show_all()
		result = dialog.run()
		
		dialog.destroy()
		
		if result == gtk.RESPONSE_OK:
			for item in items:
				full_item_path = os.path.join(self.device_cwd, item)
				self.aafm.device_delete_item(full_item_path)
				self.refresh_device_files()
		else:
			print 'no no'

	def on_device_create_directory_callback(self, widget):
		directory_name = self.dialog_get_directory_name()

		# dialog was cancelled
		if directory_name is None:
			return

		full_path = os.path.join(self.device_cwd, directory_name)
		self.aafm.device_make_directory(full_path)
		self.refresh_device_files()


	def dialog_get_directory_name(self):
		dialog = gtk.MessageDialog(
			None,
			gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
			gtk.MESSAGE_QUESTION,
			gtk.BUTTONS_OK_CANCEL,
			None)

		dialog.set_markup('Please enter new directory name:')

		entry = gtk.Entry()
		entry.connect('activate', self.dialog_response, dialog, gtk.RESPONSE_OK)

		hbox = gtk.HBox()
		hbox.pack_start(gtk.Label('Name:'), False, 5, 5)
		hbox.pack_end(entry)

		dialog.vbox.pack_end(hbox, True, True, 0)
		dialog.show_all()

		result = dialog.run()

		text = entry.get_text()
		dialog.destroy()

		if result == gtk.RESPONSE_OK:
			return text
		else:
			return None


	def dialog_response(self, entry, dialog, response):
		dialog.response(response)


	def on_device_refresh_callback(self, widget):
		self.refresh_device_files()

	def on_device_copy_to_computer_callback(self, widget):
		print 'copy to computer'
		selected = self.get_device_selected_files()
		
		task = self.copy_from_device_task(selected)
		gobject.idle_add(task.next)

	def copy_from_device_task(self, rows):
		completed = 0
		total = len(rows)

		self.update_progress()

		#while completed < total:
		for row in rows:
			#row = rows[completed]
			#iter = model.get_iter(row)
			filename = row['filename'] #model.get_value(iter, 1)
			is_directory = row['is_directory'] #model.get_value(iter, 0)

			full_device_path = os.path.join(self.device_cwd, filename)
			if is_directory:
				full_host_path = os.path.join(self.host_cwd, filename)
			else:
				full_host_path = self.host_cwd
			
			self.aafm.copy_to_host(full_device_path, full_host_path)
			completed = completed + 1
			self.refresh_host_files()
			self.update_progress(completed * 1.0 / total)

			yield True

		yield False

	def on_device_rename_item_callback(self, widget):
		old_name = self.get_device_selected_files()[0]['filename']
		new_name = self.dialog_get_item_name(old_name)

		if new_name is None:
			return

		full_src_path = os.path.join(self.device_cwd, old_name)
		full_dst_path = os.path.join(self.device_cwd, new_name)

		self.aafm.device_rename_item(full_src_path, full_dst_path)
		self.refresh_device_files()
	
	def dialog_get_item_name(self, old_name):
		dialog = gtk.MessageDialog(
			None,
			gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
			gtk.MESSAGE_QUESTION,
			gtk.BUTTONS_OK_CANCEL,
			None)

		dialog.set_markup('Please enter new name:')

		entry = gtk.Entry()
		entry.connect('activate', self.dialog_response, dialog, gtk.RESPONSE_OK)
		entry.set_text(old_name)

		hbox = gtk.HBox()
		hbox.pack_start(gtk.Label('Name:'), False, 5, 5)
		hbox.pack_end(entry)

		dialog.vbox.pack_end(hbox, True, True, 0)
		dialog.show_all()

		result = dialog.run()
		text = entry.get_text()
		dialog.destroy()
		
		if result == gtk.RESPONSE_OK:
			return text
		else:
			return None


	def update_progress(self, value = None):
		if value is None:
			self.progress_bar.set_fraction(0)
			self.progress_bar.set_text("")
			self.progress_bar.pulse()
		else:
			self.progress_bar.set_fraction(value)

			self.progress_bar.set_text("%d%%" % (value * 100))

		if value >= 1:
			self.progress_bar.set_text("Done")
			self.progress_bar.set_fraction(0)

	def die_callback(self, widget, data=None):
		self.destroy(widget, data)


	def destroy(self, widget, data=None):
		gtk.main_quit()


	def main(self):
		gtk.main()


if __name__ == '__main__':
	gui = Aafm_GUI()
	gui.main()
