import os
import re
import subprocess
import time
import pipes

class Aafm:
	def __init__(self, adb='adb', host_cwd=None, device_cwd='/'):
		self.adb = adb
		self.host_cwd = host_cwd
		self.device_cwd = device_cwd
		
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
		
		self.busybox = False
		self.probe_for_busybox()
		

	def execute(self, command):
		print "EXECUTE=", command
		process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE).stdout

		lines = []

		while True:
			line = process.readline()
			
			if not line:
				break

			lines.append(line)
		
		return lines


	def set_host_cwd(self, cwd):
		self.host_cwd = cwd
	

	def set_device_cwd(self, cwd):
		self.device_cwd = cwd


	def get_device_file_list(self):
		return self.parse_device_list( self.device_list_files( self._path_join_function(self.device_cwd, '') ) )

	def probe_for_busybox(self):
		command = '%s shell ls --help' % (self.adb)
		lines = self.execute(command)
		if len(lines) > 0 and lines[0].startswith('BusyBox'):
			print "BusyBox ls detected"
			self.busybox = True

	def device_list_files(self, device_dir):
		if self.busybox:
			command = '%s shell ls -l -A -e --color=never %s' % (self.adb, self.device_escape_path( device_dir))
		else:
			command = '%s shell ls -l -a %s' % (self.adb, self.device_escape_path(device_dir))
		lines = self.execute(command)
		return lines


	def parse_device_list(self, lines):
		entries = {}

		if self.busybox:
			pattern = re.compile(r"^(?P<permissions>[dl\-][rwx\-]+)\s+(?P<hardlinks>\d+)\s+(?P<owner>[\w_]+)\s+(?P<group>[\w_]+)\s+(?P<size>\d+)\s+(?P<datetime>\w{3} \w{3}\s+\d+\s+\d{2}:\d{2}:\d{2} \d{4}) (?P<name>.+)$")
		else:
			pattern = re.compile(r"^(?P<permissions>[dl\-][rwx\-]+) (?P<owner>\w+)\W+(?P<group>[\w_]+)\W*(?P<size>\d+)?\W+(?P<datetime>\d{4}-\d{2}-\d{2} \d{2}:\d{2}) (?P<name>.+)$")
		for line in lines:
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


	# NOTE: Currently using pipes.quote, in the future we might detect shlex.quote
	# availability and use it instead. Or not. /me is confused about python 3k
	def device_escape_path(self, path):
		return pipes.quote( path )


	def is_device_file_a_directory(self, device_file):
		parent_dir = os.path.dirname(device_file)
		filename = os.path.basename(device_file)
		lines = self.device_list_files(parent_dir)
		entries = self.parse_device_list(lines)

		if not entries.has_key(filename):
			return False

		return entries[filename]['is_directory']

	def device_make_directory(self, directory):
		pattern = re.compile(r'(\w|_|-)+')
		base = os.path.basename(directory)
		if pattern.match(base):
			self.execute( '%s shell mkdir %s' % (self.adb, self.device_escape_path( directory )) )
		else:
			print 'invalid directory name', directory
	
	
	def device_delete_item(self, path):

		if self.is_device_file_a_directory(path):
			entries = self.parse_device_list(self.device_list_files(path))

			for filename, entry in entries.iteritems():
				entry_full_path = os.path.join(path, filename)
				self.device_delete_item(entry_full_path)

			# finally delete the directory itself
			self.execute('%s shell rmdir %s' % (self.adb, self.device_escape_path(path)))

		else:
			self.execute('%s shell rm %s' % (self.adb, self.device_escape_path(path)))


	# See  __init__ for _path_join_function definition
	def device_path_join(self, a, *p):
		return self._path_join_function(a, *p)

	# Again, see __init_ for how _path_normpath_function is defined
	def device_path_normpath(self, path):
		return self._path_normpath_function(path)

	# idem
	def device_path_basename(self, path):
		return self._path_basename_function(path)


	def copy_to_host(self, device_file, host_directory):

		# We can only copy to a destination path, not to a file
		# TODO is this really needed?
		if os.path.isfile(host_directory):
			print "ERROR", host_directory, "is a file, not a directory"
			return

		if self.is_device_file_a_directory(device_file):

			# make sure host_directory exists before copying anything
			if not os.path.exists(host_directory):
				os.makedirs(host_directory)

			# Also make directory in host_directory
			dir_basename = os.path.basename( os.path.normpath( device_file ))
			final_host_directory = os.path.join( host_directory, dir_basename )
			
			if not os.path.exists( final_host_directory ):
				os.mkdir( final_host_directory )

			# copy recursively!
			entries = self.parse_device_list(self.device_list_files(device_file))

			for filename, entry in entries.iteritems():
				self.copy_to_host(os.path.join(device_file, filename), final_host_directory)
		else:
			host_file = os.path.join(host_directory, os.path.basename(device_file))
			self.execute('%s pull %s "%s"' % (self.adb, self.device_escape_path( device_file ), host_file))
	
	
	def copy_to_device(self, host_file, device_directory):

		if os.path.isfile( host_file ):

			self.execute('%s push "%s" %s' % (self.adb, host_file, self.device_escape_path( device_directory ) ) )

		else:

			normalized_directory = os.path.normpath( host_file )
			dir_basename = os.path.basename( normalized_directory )
			device_dst_dir = os.path.join( device_directory, dir_basename )

			# Ensures the directory exists beforehand
			self.device_make_directory( device_dst_dir )

			device_entries = self.parse_device_list( self.device_list_files( device_dst_dir ) )
			host_entries = os.listdir( normalized_directory )

			for entry in host_entries:

				src_file = os.path.join( normalized_directory, entry )
				
				if device_entries.has_key( entry ):
					
					# We only copy if the dst file is older or different in size
					if device_entries[ entry ]['timestamp'] >= os.path.getmtime( src_file ) or device_entries[ entry ]['size'] == os.path.getsize( src_file ):
						print "File is newer or the same, skipping"
						return

					self.copy_to_device( src_file, device_dst_dir )


	def device_rename_item(self, device_src_path, device_dst_path):
		items = self.parse_device_list(self.device_list_files(self.device_escape_path(os.path.dirname(device_dst_path))))
		filename = os.path.basename(device_dst_path)
		print filename

		if items.has_key(filename):
			print 'Filename %s already exists' % filename
			return

		self.execute('%s shell mv %s %s' % (self.adb, self.device_escape_path(device_src_path), self.device_escape_path(device_dst_path)))
