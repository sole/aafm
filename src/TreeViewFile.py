import gtk
import gobject
import MultiDragTreeView

""" A sort of TreeView container that serves for showing file listings """
class TreeViewFile:

	def __init__(self, pixbufDir, pixbufFile):
		
		self.pixbufDirectory = pixbufDir
		self.pixbufFile = pixbufFile
		# GOTCHA: Number of columns in the store *MUST* match the number of values
		# added in loadData
		self.tree_store = gtk.TreeStore(gobject.TYPE_BOOLEAN, str, str, str, str, str, str)
		self.tree_view = MultiDragTreeView.MultiDragTreeView(self.tree_store)
		self.tree_view.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
		self.scrolled_window = gtk.ScrolledWindow()
		self.scrolled_window.add_with_viewport(self.tree_view)
		self.scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		
		# TYPE
		type_col = gtk.TreeViewColumn('')
		self.tree_view.append_column(type_col)
		
		type_col_renderer_pixbuf = gtk.CellRendererPixbuf()
		type_col.pack_start(type_col_renderer_pixbuf, expand=True)
		# GOTCHA Func must be set AFTER the renderer is packed into the column
		type_col.set_cell_data_func(type_col_renderer_pixbuf, self.render_dir_or_file)

		# NAME
		name_col = gtk.TreeViewColumn('File name')
		self.tree_view.append_column(name_col)
		
		name_col_renderer_text = gtk.CellRendererText()
		name_col.pack_start(name_col_renderer_text, expand=True)
		name_col.add_attribute(name_col_renderer_text, 'text', 1)
		name_col.set_sort_column_id(1)
		self.tree_view.set_search_column(1)
		
		# SIZE
		size_col = gtk.TreeViewColumn('Size')
		self.tree_view.append_column(size_col)
		
		size_col_renderer = gtk.CellRendererText()
		size_col.pack_start(size_col_renderer, expand=True)
		size_col.add_attribute(size_col_renderer, 'text', 2)
		size_col.set_sort_column_id(2)

		# TIMESTAMP
		time_col = gtk.TreeViewColumn('Date modified')
		self.tree_view.append_column(time_col)

		time_col_renderer = gtk.CellRendererText()
		time_col.pack_start(time_col_renderer, expand=True)
		time_col.add_attribute(time_col_renderer, 'text', 3)
		time_col.set_sort_column_id(3)

		# PERMISSIONS
		perm_col = gtk.TreeViewColumn('Permissions')
		self.tree_view.append_column(perm_col)

		perm_col_renderer = gtk.CellRendererText()
		perm_col.pack_start(perm_col_renderer, expand=True)
		perm_col.add_attribute(perm_col_renderer, 'text', 4)
		perm_col.set_sort_column_id(4)

		# OWNER
		own_col = gtk.TreeViewColumn('Owner')
		self.tree_view.append_column(own_col)

		own_col_renderer = gtk.CellRendererText()
		own_col.pack_start(own_col_renderer, expand=True)
		own_col.add_attribute(own_col_renderer, 'text', 5)
		own_col.set_sort_column_id(5)

		# GROUP
		group_col = gtk.TreeViewColumn('Group')
		self.tree_view.append_column(group_col)

		group_col_renderer = gtk.CellRendererText()
		group_col.pack_start(group_col_renderer, expand=True)
		group_col.add_attribute(group_col_renderer, 'text', 6)
		group_col.set_sort_column_id(6)


	def render_dir_or_file(self, tree_view_column, cell, model, iter):
		isDir = model.get_value(iter, 0)
		if isDir:
			pixbuf = self.pixbufDirectory
		else:
			pixbuf = self.pixbufFile

		cell.set_property('pixbuf', pixbuf)


	def get_view(self):
		return self.scrolled_window

	def get_tree(self):
		return self.tree_view


	def load_data(self, data):
		self.tree_store.clear()

		for row in data:
			if row['size'] == 0:
				size = ''
			else:
				size = str(row['size'])

			rowIter = self.tree_store.append(None, [ row['directory'], row['name'], size, row['timestamp'], row['permissions'], row['owner'], row['group'] ])


