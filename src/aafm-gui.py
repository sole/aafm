#!/usr/bin/env python2

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import os
import shutil
import socket
import datetime
import stat
import pwd
import grp
import urllib

if os.name == 'nt':
	import win32api
	import win32con
	import win32security

from TreeViewFile import TreeViewFile
from Aafm import Aafm


class Aafm_GUI:

	QUEUE_ACTION_COPY_TO_DEVICE = 'copy_to_device'
	QUEUE_ACTION_COPY_FROM_DEVICE = 'copy_from_device'
	QUEUE_ACTION_CALLABLE = 'callable'
	QUEUE_ACTION_MOVE_IN_DEVICE = 'move_in_device'
	QUEUE_ACTION_MOVE_IN_HOST = 'move_in_host'

	# These constants are for dragging files to Nautilus
	XDS_ATOM = gtk.gdk.atom_intern("XdndDirectSave0")
	TEXT_ATOM = gtk.gdk.atom_intern("text/plain")
	XDS_FILENAME = 'whatever.txt'

	def __init__(self):
		
		# The super core
		self.aafm = Aafm('adb', os.getcwd(), '/mnt/sdcard/')
		self.queue = []

		self.basedir = os.path.dirname(os.path.abspath(__file__))
		
		if os.name == 'nt':
			self.get_owner = self._get_owner_windows
			self.get_group = self._get_group_windows
		else:
			self.get_owner = self._get_owner
			self.get_group = self._get_group

		# Build main window from XML
		builder = gtk.Builder()
		builder.add_from_file(os.path.join(self.basedir, "data/glade/interface.xml"))
		builder.connect_signals({ "on_window_destroy" : gtk.main_quit })
		self.window = builder.get_object("window")

		imageDir = gtk.Image()
		imageDir.set_from_file(os.path.join(self.basedir, './data/icons/folder.png'))
		imageFile = gtk.Image()
		imageFile.set_from_file(os.path.join(self.basedir, './data/icons/file.png'))
		
		# Show hidden files and folders
		self.showHidden = False

		showHidden = builder.get_object('showHidden')
		showHidden.connect('toggled', self.on_toggle_hidden)

		# Refresh view
		refreshView = builder.get_object('refreshView')
		refreshView.connect('activate', self.refresh_all)

		itemQuit = builder.get_object('itemQuit')
		itemQuit.connect('activate', gtk.main_quit)

		self.menuDevices = builder.get_object('menuDevices')
		self.refresh_menu_devices()

		# Host and device TreeViews
		
		# HOST
		self.host_treeViewFile = TreeViewFile(imageDir.get_pixbuf(), imageFile.get_pixbuf())
		
		hostFrame = builder.get_object('frameHost')
		hostFrame.get_child().add(self.host_treeViewFile.get_view())
		
		hostTree = self.host_treeViewFile.get_tree()
		hostTree.connect('row-activated', self.host_navigate_callback)
		hostTree.connect('button_press_event', self.on_host_tree_view_contextual_menu)
	
		host_targets = [
			('DRAG_SELF', gtk.TARGET_SAME_WIDGET, 0),
			('ADB_text', 0, 1),
			('text/plain', 0, 2)
		]

		hostTree.enable_model_drag_dest(
			host_targets,
			gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE
		)
		hostTree.connect('drag-data-received', self.on_host_drag_data_received)

		hostTree.enable_model_drag_source(
			gtk.gdk.BUTTON1_MASK,
			host_targets,
			gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE
		)
		hostTree.connect('drag_data_get', self.on_host_drag_data_get)
		
		self.hostFrame = hostFrame
		self.hostName = socket.gethostname()


		# DEVICE
		self.device_treeViewFile = TreeViewFile(imageDir.get_pixbuf(), imageFile.get_pixbuf())
		
		deviceFrame = builder.get_object('frameDevice')
		deviceFrame.get_child().add(self.device_treeViewFile.get_view())

		deviceTree = self.device_treeViewFile.get_tree()
		deviceTree.connect('row-activated', self.device_navigate_callback)
		deviceTree.connect('button_press_event', self.on_device_tree_view_contextual_menu)

		device_targets = [
			('DRAG_SELF', gtk.TARGET_SAME_WIDGET, 0),
			('ADB_text', 0, 1),
			('XdndDirectSave0', 0, 2),
			('text/plain', 0, 3)
		]

		deviceTree.enable_model_drag_dest(
			device_targets,
			gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE
		)
		deviceTree.connect('drag-data-received', self.on_device_drag_data_received)
		
		deviceTree.enable_model_drag_source(
			gtk.gdk.BUTTON1_MASK,
			device_targets,
			gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE
		)
		deviceTree.connect('drag-data-get', self.on_device_drag_data_get)
		deviceTree.connect('drag-begin', self.on_device_drag_begin)
		
		self.deviceFrame = deviceFrame


		# Progress bar
		self.progress_bar = builder.get_object('progressBar')

		# Some more subtle details...
		self.window.set_title("Android ADB file manager")
		#self.adb = 'adb'
		self.host_cwd = os.getcwd()
		self.aafm.set_device_cwd('/mnt/sdcard/')

		self.refresh_all()

		# Make both panels equal in size (at least initially)
		panelsPaned = builder.get_object('panelsPaned')
		self.window.show_all()
		panelsPaned.set_position(panelsPaned.get_allocation().width / 2)

		# And we're done!
		self.window.show_all()

	def refresh_menu_devices(self, widget=None):
		before = self.aafm.get_device_serial()
		self.aafm.refresh_devices()
		selected = self.aafm.get_device_serial()
		if before != selected:
			self.aafm.set_device_cwd('/mnt/sdcard/')
			self.refresh_device_files()

		def on_menu_item_toggled(item, serial):
			if item.get_active():
				self.aafm.set_device_serial(serial)
				self.aafm.set_device_cwd('/mnt/sdcard/')
				self.refresh_device_files()

		menu = self.menuDevices
		submenu = gtk.Menu()
		group = None
		for serial, name in self.aafm.get_devices():
			item = gtk.RadioMenuItem(group, '%s (%s)' % (name, serial))
			if serial == selected:
				item.set_active(True)

			item.connect('toggled', on_menu_item_toggled, serial)
			if group is None:
				group = item
			submenu.append(item)
		if group is None:
			item = gtk.MenuItem('No devices found')
			item.set_sensitive(False)
			submenu.append(item)
		submenu.append(gtk.SeparatorMenuItem())
		item = gtk.MenuItem('Refresh device list')
		item.connect('activate', self.refresh_menu_devices)
		submenu.append(item)
		menu.set_submenu(submenu)
		menu.show_all()



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
			self.aafm.set_device_cwd(self.aafm.device_path_normpath(self.aafm.device_path_join(self.aafm.device_cwd, name)))
			self.refresh_device_files()

	def refresh_all(self, widget=None):
		self.refresh_host_files()
		self.refresh_device_files()
	
	def refresh_host_files(self):
		self.host_treeViewFile.load_data(self.dir_scan_host(self.host_cwd))
		self.hostFrame.set_label('%s:%s' % (self.hostName, self.host_cwd))


	def refresh_device_files(self):
		self.device_treeViewFile.load_data(self.dir_scan_device(self.aafm.device_cwd))
		self.deviceFrame.set_label('%s:%s (%s free)' % ('device', self.aafm.device_cwd, self.aafm.get_free_space()))


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

		if not self.showHidden:
			files = [f for f in files if not f[0] == '.']
			dirs = [d for d in dirs if not d[0] == '.']

		dirs.sort()
		files.sort()

		output.append({'directory': True, 'name': '..', 'size': 0, 'timestamp': '',
				'permissions': '',
				'owner': '',
				'group': ''})

		for d in dirs:
			path = os.path.join(directory, d)
			output.append({
				'directory': True,
				'name': d,
				'size': 0,
				'timestamp': self.format_timestamp(os.path.getmtime(path)),
				'permissions': self.get_permissions(path),
				'owner': self.get_owner(path),
				'group': self.get_group(path)
			})

		for f in files:
			path = os.path.join(directory, f)

			try:
				size = os.path.getsize(path)
				output.append({
					'directory': False,
					'name': f,
					'size': size,
					'timestamp': self.format_timestamp(os.path.getmtime(path)),
					'permissions': self.get_permissions(path),
					'owner': self.get_owner(path),
					'group': self.get_group(path)
				})
			except OSError:
				pass

		return output

	""" The following three methods are probably NOT the best way of doing things.
	At least according to all the warnings that say os.stat is very costly
	and should be cached."""
	def get_permissions(self, filename):
		st = os.stat(filename)
		mode = st.st_mode
		permissions = ''

		bits = [ 
			stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR,
			stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP,
			stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH
		]

		attrs = ['r', 'w', 'x']

		for i in range(0, len(bits)):
			bit = bits[i]
			attr = attrs[i % len(attrs)]

			if bit & mode:
				permissions += attr
			else:
				permissions += '-'

		return permissions

	def _get_owner(self, filename):
		st = os.stat(filename)
		uid = st.st_uid
		try:
			user = pwd.getpwuid(uid)[0]
		except KeyError:
			print ('unknown uid %d for file %s' % (uid, filename))
			user = 'unknown'
		return user
		
	def _get_owner_windows(self, filename):
		sd = win32security.GetFileSecurity(filename, win32security.OWNER_SECURITY_INFORMATION)
		owner_sid = sd.GetSecurityDescriptorOwner()
		name, domain, type = win32security.LookupAccountSid(None, owner_sid)
		return name

	def _get_group(self, filename):
		st = os.stat(filename)
		gid = st.st_gid
		try:
			groupname = grp.getgrgid(gid)[0]
		except KeyError:
			print ('unknown gid %d for file %s' % (gid, filename))
			groupname = 'unknown'
		return groupname
	
	def _get_group_windows(self, filename):
		return ""


	def format_timestamp(self, timestamp):
		d = datetime.datetime.fromtimestamp(timestamp)
		return d.strftime(r'%Y-%m-%d %H:%M')

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

		if not self.showHidden:
			files = [f for f in files if not f[0] == '.']
			dirs = [d for d in dirs if not d[0] == '.']

		dirs.sort()
		files.sort()

		output.append({'directory': True, 'name': '..', 'size': 0, 'timestamp': '', 'permissions': '', 'owner': '', 'group': ''})

		for d in dirs:
			output.append({
				'directory': True,
				'name': d,
				'size': 0,
				'timestamp': self.format_timestamp(entries[d]['timestamp']), 
				'permissions': entries[d]['permissions'],
				'owner': entries[d]['owner'],
				'group': entries[d]['group']
			})

		for f in files:
			size = int(entries[f]['size'])
			output.append({
				'directory': False,
				'name': f,
				'size': size,
				'timestamp': self.format_timestamp(entries[f]['timestamp']),
				'permissions': entries[f]['permissions'],
				'owner': entries[f]['owner'],
				'group': entries[f]['group']
			})

		return output


	def on_toggle_hidden(self, widget):
		self.showHidden = widget.get_active()

		self.refresh_all()

	def on_host_tree_view_contextual_menu(self, widget, event):
		if event.button == 3: # Right click
			builder = gtk.Builder()
			builder.add_from_file(os.path.join(self.basedir, 'data/glade/menu_contextual_host.xml'))
			menu = builder.get_object('menu')
			builder.connect_signals({
				'on_menuHostCopyToDevice_activate': self.on_host_copy_to_device_callback,
				'on_menuHostCreateDirectory_activate': self.on_host_create_directory_callback,
				'on_menuHostRefresh_activate': self.on_host_refresh_callback,
				'on_menuHostDeleteItem_activate': self.on_host_delete_item_callback,
				'on_menuHostRenameItem_activate': self.on_host_rename_item_callback
			})

			# Ensure only right options are available
			num_selected = len(self.get_host_selected_files())
			has_selection = num_selected > 0

			menuCopy = builder.get_object('menuHostCopyToDevice')
			menuCopy.set_sensitive(has_selection)

			menuDelete = builder.get_object('menuHostDeleteItem')
			menuDelete.set_sensitive(has_selection)

			menuRename = builder.get_object('menuHostRenameItem')
			menuRename.set_sensitive(num_selected == 1)	

			menu.popup(None, None, None, event.button, event.time)
			return True
		
		# Not consuming the event
		return False

	# Copy to device
	def on_host_copy_to_device_callback(self, widget):
		for row in self.get_host_selected_files():
			src = os.path.join(self.host_cwd, row['filename'])
			self.add_to_queue(self.QUEUE_ACTION_COPY_TO_DEVICE, src, self.aafm.device_cwd)
		self.process_queue()

	
	# Create host directory
	def on_host_create_directory_callback(self, widget):
		directory_name = self.dialog_get_directory_name()

		if directory_name is None:
			return

		full_path = os.path.join(self.host_cwd, directory_name)
		if not os.path.exists(full_path):
			os.mkdir(full_path)
			self.refresh_host_files()


	def on_host_refresh_callback(self, widget):
		self.refresh_host_files()


	def on_host_delete_item_callback(self, widget):
		selected = self.get_host_selected_files()
		items = []
		for item in selected:
			items.append(item['filename'])
			
		result = self.dialog_delete_confirmation(items)

		if result == gtk.RESPONSE_OK:
			for item in items:
				full_item_path = os.path.join(self.host_cwd, item)
				self.delete_item(full_item_path)
				self.refresh_host_files()

	def delete_item(self, path):
		if os.path.isfile(path):
			os.remove(path)
		else:
			shutil.rmtree(path)

	def on_host_rename_item_callback(self, widget):
		old_name = self.get_host_selected_files()[0]['filename']
		new_name = self.dialog_get_item_name(old_name)

		if new_name is None:
			return

		full_src_path = os.path.join(self.host_cwd, old_name)
		full_dst_path = os.path.join(self.host_cwd, new_name)

		shutil.move(full_src_path, full_dst_path)
		self.refresh_host_files()

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

		result = self.dialog_delete_confirmation(items)

		if result == gtk.RESPONSE_OK:
			for item in items:
				full_item_path = self.aafm.device_path_join(self.aafm.device_cwd, item)
				for func, args in self.aafm.device_delete_item(full_item_path):
					self.add_to_queue(self.QUEUE_ACTION_CALLABLE, func, args)
				self.add_to_queue(self.QUEUE_ACTION_CALLABLE, self.refresh_device_files, ())
				self.process_queue()
		else:
			print('no no')


	def dialog_delete_confirmation(self, items):
		items.sort()
		joined = ', '.join(items)
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
		return result

	def on_device_create_directory_callback(self, widget):
		directory_name = self.dialog_get_directory_name()

		# dialog was cancelled
		if directory_name is None:
			return

		full_path = self.aafm.device_path_join(self.aafm.device_cwd, directory_name)
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
		selected = self.get_device_selected_files()
		task = self.copy_from_device_task(selected)
		gobject.idle_add(task.next)


	def copy_from_device_task(self, rows):
		for row in rows:
			filename = row['filename']

			full_device_path = self.aafm.device_path_join(self.aafm.device_cwd, filename)
			full_host_path = self.host_cwd

			self.add_to_queue(self.QUEUE_ACTION_COPY_FROM_DEVICE, full_device_path, full_host_path)

		self.process_queue()
		yield False

	def on_device_rename_item_callback(self, widget):
		old_name = self.get_device_selected_files()[0]['filename']
		new_name = self.dialog_get_item_name(old_name)

		if new_name is None:
			return

		full_src_path = self.aafm.device_path_join(self.aafm.device_cwd, old_name)
		full_dst_path = self.aafm.device_path_join(self.aafm.device_cwd, new_name)

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
			self.progress_bar.set_text("Ready")
			self.progress_bar.pulse()
		else:
			self.progress_bar.set_fraction(value)

			self.progress_bar.set_text("%d%%" % (value * 100))

		if value >= 1:
			self.progress_bar.set_text("Done")
			self.progress_bar.set_fraction(0)

		# Make sure the GUI has some cycles for processing events
		while gtk.events_pending():
			gtk.main_iteration(False)


	def on_host_drag_data_get(self, widget, context, selection, target_type, time):
		data = '\n'.join(['file://' + urllib.quote(os.path.join(self.host_cwd, item['filename'])) for item in self.get_host_selected_files()])
		
		selection.set(selection.target, 8, data)

	
	def on_host_drag_data_received(self, tree_view, context, x, y, selection, info, timestamp):
		data = selection.data
		type = selection.type
		drop_info = tree_view.get_dest_row_at_pos(x, y)
		destination = self.host_cwd
		
		if drop_info:
			model = tree_view.get_model()
			path, position = drop_info
			
			if position in [ gtk.TREE_VIEW_DROP_INTO_OR_BEFORE, gtk.TREE_VIEW_DROP_INTO_OR_AFTER ]:
				iter = model.get_iter(path)
				is_directory = model.get_value(iter, 0)
				name = model.get_value(iter, 1)

				# If dropping over a folder, copy things to that folder
				if is_directory:
					destination = os.path.join(self.host_cwd, name)

		for line in [line.strip() for line in data.split('\n')]:
			if line.startswith('file://'):
				source = urllib.unquote(line.replace('file://', '', 1))

				if type == 'DRAG_SELF':
					self.add_to_queue(self.QUEUE_ACTION_MOVE_IN_HOST, source, destination)
				elif type == 'ADB_text':
					self.add_to_queue(self.QUEUE_ACTION_COPY_FROM_DEVICE, source, destination)

		self.process_queue()



	def on_device_drag_begin(self, widget, context):
		
		context.source_window.property_change(self.XDS_ATOM, self.TEXT_ATOM, 8, gtk.gdk.PROP_MODE_REPLACE, self.XDS_FILENAME)
	

	def on_device_drag_data_get(self, widget, context, selection, target_type, time):
		
		if selection.target == 'XdndDirectSave0':
			type, format, destination_file = context.source_window.property_get(self.XDS_ATOM, self.TEXT_ATOM)

			if destination_file.startswith('file://'):
				destination = os.path.dirname(urllib.unquote(destination_file).replace('file://', '', 1))
				for item in self.get_device_selected_files():
					self.add_to_queue(self.QUEUE_ACTION_COPY_FROM_DEVICE, self.aafm.device_path_join(self.aafm.device_cwd, item['filename']), destination)

				self.process_queue()
			else:
				print("ERROR: Destination doesn't start with file://?!!?")


		else:
			selection.set(selection.target, 8, '\n'.join(['file://' + urllib.quote(self.aafm.device_path_join(self.aafm.device_cwd, item['filename'])) for item in self.get_device_selected_files()]))
	

	def on_device_drag_data_received(self, tree_view, context, x, y, selection, info, timestamp):

		data = selection.data
		type = selection.type
		drop_info = tree_view.get_dest_row_at_pos(x, y)
		destination = self.aafm.device_cwd
		
		# When dropped over a row
		if drop_info:
			model = tree_view.get_model()
			path, position = drop_info
			
			if position in [ gtk.TREE_VIEW_DROP_INTO_OR_BEFORE, gtk.TREE_VIEW_DROP_INTO_OR_AFTER ]:
				iter = model.get_iter(path)
				is_directory = model.get_value(iter, 0)
				name = model.get_value(iter, 1)

				# If dropping over a folder, copy things to that folder
				if is_directory:
					destination = self.aafm.device_path_join(self.aafm.device_cwd, name)

		if type == 'DRAG_SELF':
			if self.aafm.device_cwd != destination:
				for line in [line.strip() for line in data.split('\n')]:
					if line.startswith('file://'):
						source = urllib.unquote(line.replace('file://', '', 1))
						if source != destination:
							name = self.aafm.device_path_basename(source)
							self.add_to_queue(self.QUEUE_ACTION_MOVE_IN_DEVICE, source, os.path.join(destination, name))
		else:
			# COPY stuff
			for line in [line.strip() for line in data.split('\n')]:
				if line.startswith('file://'):
					source = urllib.unquote(line.replace('file://', '', 1))
					self.add_to_queue(self.QUEUE_ACTION_COPY_TO_DEVICE, source, destination)
		
		self.process_queue()


	def add_to_queue(self, action, src_file, dst_path):
		self.queue.append([action, src_file, dst_path])
	

	def process_queue(self):
		task = self.process_queue_task()
		gobject.idle_add(task.next)
	
	def process_queue_task(self):
		completed = 0
		self.update_progress()

		while len(self.queue) > 0:
			item = self.queue.pop(0)
			action, src, dst = item

			if action == self.QUEUE_ACTION_COPY_TO_DEVICE:
				for func, args in self.aafm.generate_copy_to_device_tasks(src, dst):
					self.add_to_queue(self.QUEUE_ACTION_CALLABLE, func, args)
				self.add_to_queue(self.QUEUE_ACTION_CALLABLE, self.refresh_device_files, ())
			elif action == self.QUEUE_ACTION_COPY_FROM_DEVICE:
				for func, args in self.aafm.generate_copy_to_host_tasks(src, dst):
					self.add_to_queue(self.QUEUE_ACTION_CALLABLE, func, args)
				self.add_to_queue(self.QUEUE_ACTION_CALLABLE, self.refresh_host_files, ())
			elif action == self.QUEUE_ACTION_CALLABLE:
				src(*dst)
			elif action == self.QUEUE_ACTION_MOVE_IN_DEVICE:
				self.aafm.device_rename_item(src, dst)
				self.refresh_device_files()
			elif action == self.QUEUE_ACTION_MOVE_IN_HOST:
				shutil.move(src, dst)
				self.refresh_host_files()

			completed += 1
			self.update_progress(float(completed) / float(completed + len(self.queue)))

			yield True

		yield False



	def die_callback(self, widget, data=None):
		self.destroy(widget, data)


	def destroy(self, widget, data=None):
		gtk.main_quit()


	def main(self):
		gtk.main()


if __name__ == '__main__':
	gui = Aafm_GUI()
	gui.main()
