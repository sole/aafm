import os
import re
import subprocess
import time

class Aafm:
	def __init__(self, adb='adb', host_cwd=None, device_cwd='/', device_serial=None):
		self.adb = adb
		self.host_cwd = host_cwd
		self.device_cwd = device_cwd
		self.device_serial = device_serial
		self.busybox = False
		self.connected_devices = []
		
		# The Android device should always use POSIX path style separators (/),
		# so we can happily use os.path.join when running on Linux (which is POSIX)
		# But we can't use it when running on Windows machines because they use '\\'
		# So we'll import the robust, tested and proven posixpath module,
		# instead of using an inferior poorman's replica.
		# Not sure how much of a hack is this...
		# Feel free to illuminate me if there's a better way.
		pathmodule = __import__('posixpath')
		
		self._path_join_function = pathmodule.join
		self._path_normpath_function = pathmodule.normpath
		self._path_basename_function = pathmodule.basename

		self.refresh_devices()

	def execute(self, *args):
		print "EXECUTE", args
		proc = subprocess.Popen(args, stdout=subprocess.PIPE)
		return filter(None, [line.rstrip('\r\n') for line in proc.stdout])

	def _adb(self, *args):
		if self.device_serial is not None:
			return self.execute(self.adb, '-s', self.device_serial, *args)

		return self.execute(self.adb, *args)

	def adb_shell(self, *args):
		return self._adb('shell', *args)

	def set_host_cwd(self, cwd):
		self.host_cwd = cwd
	

	def set_device_cwd(self, cwd):
		self.device_cwd = cwd

	def set_device_serial(self, serial):
		self.device_serial = serial
		self.probe_for_busybox()

	def get_device_serial(self):
		return self.device_serial

	def get_devices(self):
		return self.connected_devices

	def refresh_devices(self):
		self.connected_devices = list(self.get_connected_devices())
		if self.device_serial not in [serial for serial, name in self.connected_devices]:
			# Previously-selected device has gone, need to select a new one
			if self.connected_devices:
				self.set_device_serial(self.connected_devices[0][0])
			else:
				self.set_device_serial(None)


	def get_connected_devices(self):
		serials = [line.split(None, 1)
				for line in self.execute(self.adb, 'devices')
				if line and not line.startswith('List of devices attached')]

		for serial, kind in serials:
			build_prop = self.execute(self.adb, '-s', serial,
					'shell', 'cat', '/system/build.prop')
			props = dict(x.strip().split('=', 1) for x in build_prop if '=' in x)
			yield (serial, props.get('ro.product.model', serial))

	def get_device_file_list(self):
		return self.device_list_files_parsed(self._path_join_function(self.device_cwd, ''))

	def get_free_space(self):
		lines = self.adb_shell('df', self.device_cwd)
		if len(lines) != 2 or not lines[0].startswith('Filesystem'):
			return '-'

		splitted = lines[1].split()
		if len(splitted) != 5:
			return '-'

		mountpoint, size, used, free, blksize = splitted
		return free

	def probe_for_busybox(self):
		self.busybox = any(line.startswith('BusyBox')
				for line in self.adb_shell('ls', '--help'))

	def device_list_files_parsed(self, device_dir):
		if self.busybox:
			command = ['ls', '-l', '-A', '-e', '--color=never', device_dir]
			pattern = re.compile(r"^(?P<permissions>[dl\-][rwx\-]+)\s+(?P<hardlinks>\d+)\s+(?P<owner>[\w_]+)\s+(?P<group>[\w_]+)\s+(?P<size>\d+)\s+(?P<datetime>\w{3} \w{3}\s+\d+\s+\d{2}:\d{2}:\d{2} \d{4}) (?P<name>.+)$")
		else:
			command = ['ls', '-l', '-a', device_dir]
			pattern = re.compile(r"^(?P<permissions>[dl\-][rwx\-]+) (?P<owner>\w+)\W+(?P<group>[\w_]+)\W*(?P<size>\d+)?\W+(?P<datetime>\d{4}-\d{2}-\d{2} \d{2}:\d{2}) (?P<name>.+)$")

		entries = {}

		for line in self.adb_shell(*command):
			line = line.rstrip()
			match = pattern.match(line)
			
			if match:
				permissions = match.group('permissions')
				owner = match.group('owner')
				group = match.group('group')
				fsize = match.group('size')
				if fsize is None:
					fsize = 0
				filename = match.group('name')
				
				if self.busybox:
					date_format = "%a %b %d %H:%M:%S %Y"
				else:
					date_format = "%Y-%m-%d %H:%M"
				timestamp = time.mktime((time.strptime(match.group('datetime'), date_format)))
				
				is_directory = permissions.startswith('d')

				if permissions.startswith('l'):
					filename, target = filename.split(' -> ')
					is_directory = self.is_device_file_a_directory(target)

				entries[filename] = { 
					'is_directory': is_directory,
					'size': fsize,
					'timestamp': timestamp,
					'permissions': permissions,
					'owner': owner,
					'group': group
				}

			else:
				print line, "wasn't matched, please report to the developer!"

		return entries


	def is_device_file_a_directory(self, device_file):
		device_file = os.path.normpath(device_file)
		parent_dir = os.path.dirname(device_file)
		filename = os.path.basename(device_file)
		entries = self.device_list_files_parsed(self._path_join_function(parent_dir, ''))

		if not entries.has_key(filename):
			return False

		return entries[filename]['is_directory']

	def device_make_directory(self, directory):
		if not self.is_device_file_a_directory(directory):
			self.adb_shell('mkdir', directory)


	def device_walk(self, path):
		assert self.is_device_file_a_directory(path)

		queue = [path]
		while queue:
			dirpath = queue.pop(0)
			dirnames = []
			filenames = []

			entries = self.device_list_files_parsed(self._path_join_function(dirpath, ''))
			for filename, entry in entries.iteritems():
				if entry['is_directory']:
					entry_full_path = os.path.join(dirpath, filename)
					queue.append(entry_full_path)
					dirnames.append(filename)
				else:
					filenames.append(filename)

			yield (dirpath, dirnames, filenames)


	def device_delete_item(self, path):
		if not self.is_device_file_a_directory(path):
			yield (self.adb_shell, ('rm', path))
			return

		# TODO: Maybe we can use "rm -rf" here?
		dirs_to_remove = [path]
		for dirpath, dirnames, filenames in self.device_walk(path):
			for filename in filenames:
				yield (self.adb_shell, ('rm', os.path.join(dirpath, filename)))

			for dirname in dirnames:
				dirs_to_remove.append(os.path.join(dirpath, dirname))

		# Remove directory tree from deepest outwards
		for dirname in reversed(dirs_to_remove):
			yield (self.adb_shell, ('rmdir', dirname))


	# See  __init__ for _path_join_function definition
	def device_path_join(self, a, *p):
		return self._path_join_function(a, *p)

	# Again, see __init_ for how _path_normpath_function is defined
	def device_path_normpath(self, path):
		return self._path_normpath_function(path)

	# idem
	def device_path_basename(self, path):
		return self._path_basename_function(path)


	def make_relative_path(self, old_root, new_root, path):
		"""
		>>> make_relative_path('/foo', '/bar', '/foo/123')
		'/bar/123'
		>>> make_relative_path('/foo', '/bar/hi', '/foo')
		'/bar/hi'
		"""
		assert not old_root.endswith('/') and not new_root.endswith('/') and path.startswith(old_root)
		return os.path.normpath(os.path.join(new_root, path[len(old_root)+1:]))


	def generate_copy_to_host_tasks(self, device_file, host_directory):
		device_file = os.path.normpath(device_file)

		# If device_file is a file, we simply need to copy it around
		if not self.is_device_file_a_directory(device_file):
			yield (self.host_make_directory, (host_directory,))
			yield (self.copy_file_to_host, (device_file, os.path.join(host_directory, os.path.basename(device_file))))
			return

		# Otherwise we walk the directory tree and add mkdir/copy commands as needed
		target_dir = os.path.join(host_directory, os.path.basename(device_file))
		yield (self.host_make_directory, (target_dir,))

		for dirpath, dirnames, filenames in self.device_walk(device_file):
			host_path = self.make_relative_path(device_file, target_dir, dirpath)

			for dirname in dirnames:
				yield (self.host_make_directory, (os.path.join(host_path, dirname),))

			for filename in filenames:
				yield (self.copy_file_to_host, (os.path.join(dirpath, filename), os.path.join(host_path, filename)))


	def host_make_directory(self, path):
		if not os.path.exists(path):
			os.makedirs(path)


	def copy_file_to_host(self, device_file, host_file):
		assert os.path.exists(os.path.dirname(host_file))
		self._adb('pull', device_file, host_file)


	def copy_file_to_device(self, host_file, device_file):
		assert self.is_device_file_a_directory(os.path.dirname(device_file))
		# TODO: # We only copy if the dst file is older or different in size
		#if device_entries[ entry ]['timestamp'] >= os.path.getmtime( src_file ) or device_entries[ entry ]['size'] == os.path.getsize( src_file ):
		self._adb('push', host_file, device_file)


	def generate_copy_to_device_tasks(self, host_file, device_directory):
		host_file = os.path.normpath(host_file)

		if os.path.isfile(host_file):
			yield (self.device_make_directory, (device_directory,))
			yield (self.copy_file_to_device, (host_file, os.path.join(device_directory, os.path.basename(host_file))))
			return

		target_dir = os.path.join(device_directory, os.path.basename(host_file))
		yield (self.device_make_directory, (target_dir,))

		for dirpath, dirnames, filenames in os.walk(host_file):
			device_path = self.make_relative_path(host_file, target_dir, dirpath)

			for dirname in dirnames:
				yield (self.device_make_directory, (os.path.join(device_path, dirname),))

			for filename in filenames:
				yield (self.copy_file_to_device, (os.path.join(dirpath, filename), os.path.join(device_path, filename)))


	def device_rename_item(self, device_src_path, device_dst_path):
		items = self.device_list_files_parsed(os.path.dirname(device_dst_path))
		filename = os.path.basename(device_dst_path)
		print filename

		if items.has_key(filename):
			print 'Filename %s already exists' % filename
			return

		self.adb_shell('mv', device_src_path, device_dst_path)
