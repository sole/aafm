import gtk
import gobject

""" A sort of TreeView container that serves for showing file listings """
class TreeViewFile:

	def __init__(self, pixbufDir, pixbufFile):
		
		self.pixbufDirectory = pixbufDir
		self.pixbufFile = pixbufFile
		# GOTCHA: Number of columns in the store *MUST* match the number of values
		# added in loadData
		self.tree_store = gtk.TreeStore(gobject.TYPE_BOOLEAN, str, str)
		self.tree_view = gtk.TreeView(self.tree_store)
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
			rowIter = self.tree_store.append(None, [ row['directory'], row['name'], size ])


