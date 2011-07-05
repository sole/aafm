import os
import re
import subprocess
import time

class Aafm:
	def __init__(self, adb='adb', host_cwd=None, device_cwd='/'):
		self.adb = adb
		self.host_cwd = host_cwd
		self.device_cwd = device_cwd


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
		return self.parse_device_list( self.device_list_files(self.device_cwd) )


	def device_list_files(self, device_dir):
		command = '%s shell ls -la "%s"' % (self.adb, device_dir)
		lines = self.execute(command)
		return lines


	def parse_device_list(self, lines):
		entries = {}
		pattern = re.compile(r"^(?P<permissions>[drwx\-]+) (?P<owner>\w+)\W+(?P<group>[\w_]+)\W*(?P<size>\d+)?\W+(?P<datetime>\d{4}-\d{2}-\d{2} \d{2}:\d{2}) (?P<name>.+)$")

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
				timestamp = time.mktime((time.strptime(match.group('datetime'), "%Y-%m-%d %H:%M")))
				
				is_directory = permissions.startswith('d')

				entries[filename] = { 'is_directory': is_directory, 'size': fsize, 'timestamp': timestamp }

			else:
				print filename, "wasn't matched, please report to the developer!"

		return entries


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
			self.execute( '%s shell mkdir "%s" ' % (self.adb, directory ) )
		else:
			print 'invalid directory name', directory
	
	
	def device_delete_item(self, path):

		if self.is_device_file_a_directory(path):
			entries = self.parse_device_list(self.device_list_files(path))

			for filename, entry in entries.iteritems():
				entry_full_path = os.path.join(path, filename)
				self.device_delete_item(entry_full_path)

			# finally delete the directory itself
			self.execute('%s shell rmdir "%s"' % (self.adb, path))

		else:
			self.execute('%s shell rm "%s"' % (self.adb, path))





