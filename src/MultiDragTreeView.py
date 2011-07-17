import gtk
import gobject
import pango

""" This class is taken (with some edits) from the excellent QuodLibet project:
	code.google.com/p/quodlibet/

	QuodLibet is licensed under the GPL v2 License:
	http://www.gnu.org/licenses/old-licenses/gpl-2.0.html
"""

class MultiDragTreeView(gtk.TreeView):
    """TreeView with multirow drag support:
    * Selections don't change until button-release-event...
    * Unless they're a Shift/Ctrl modification, then they happen immediately
    * Drag icons include 3 rows/2 plus a "and more" count"""

    def __init__(self, *args):
        super(MultiDragTreeView, self).__init__(*args)
        self.connect_object(
            'button-press-event', MultiDragTreeView.__button_press, self)
        self.connect_object(
            'button-release-event', MultiDragTreeView.__button_release, self)
        self.connect_object('drag-begin', MultiDragTreeView.__begin, self)
        self.__pending_event = None

    def __button_press(self, event):
        if event.button == 1: return self.__block_selection(event)

    def __block_selection(self, event):
        x, y = map(int, [event.x, event.y])
        try: path, col, cellx, celly = self.get_path_at_pos(x, y)
        except TypeError: return True
        self.grab_focus()
        selection = self.get_selection()
        if ((selection.path_is_selected(path)
            and not (event.state & (gtk.gdk.CONTROL_MASK|gtk.gdk.SHIFT_MASK)))):
            self.__pending_event = [x, y]
            selection.set_select_function(lambda *args: False)
        elif event.type == gtk.gdk.BUTTON_PRESS:
            self.__pending_event = None
            selection.set_select_function(lambda *args: True)

    def __button_release(self, event):
        if self.__pending_event:
            selection = self.get_selection()
            selection.set_select_function(lambda *args: True)
            oldevent = self.__pending_event
            self.__pending_event = None
            if oldevent != [event.x, event.y]: return True
            x, y = map(int, [event.x, event.y])
            try: path, col, cellx, celly = self.get_path_at_pos(x, y)
            except TypeError: return True
            self.set_cursor(path, col, 0)

    def __begin(self, ctx):
        model, paths = self.get_selection().get_selected_rows()
        MAX = 3
        if paths:
            icons = map(self.create_row_drag_icon, paths[:MAX])
            height = (
                sum(map(lambda s: s.get_size()[1], icons))-2*len(icons))+2
            width = max(map(lambda s: s.get_size()[0], icons))
            final = gtk.gdk.Pixmap(icons[0], width, height)
            gc = gtk.gdk.GC(final)
            gc.copy(self.style.fg_gc[gtk.STATE_NORMAL])
            gc.set_colormap(self.window.get_colormap())
            count_y = 1
            for icon in icons:
                w, h = icon.get_size()
                final.draw_drawable(gc, icon, 1, 1, 1, count_y, w-2, h-2)
                count_y += h - 2
            if len(paths) > MAX:
                count_y -= h - 2
                bgc = gtk.gdk.GC(final)
                bgc.copy(self.style.base_gc[gtk.STATE_NORMAL])
                final.draw_rectangle(bgc, True, 1, count_y, w-2, h-2)
				# WARNING -- modified from original!
				# Not using i18n so taking out the initial underscore for translations ;)
                more = ("and %d more...") % (len(paths) - MAX + 1) # _("and %d more...") % (len(paths) - MAX + 1)
                layout = self.create_pango_layout(more)
                attrs = pango.AttrList()
                attrs.insert(pango.AttrStyle(pango.STYLE_ITALIC, 0, len(more)))
                layout.set_attributes(attrs)
                layout.set_width(pango.SCALE * (w - 2))
                lw, lh = layout.get_pixel_size()
                final.draw_layout(gc, (w-lw)//2, count_y + (h-lh)//2, layout)

            final.draw_rectangle(gc, False, 0, 0, width-1, height-1)
            self.drag_source_set_icon(final.get_colormap(), final)
        else:
            gobject.idle_add(ctx.drag_abort, gtk.get_current_event_time())
            self.drag_source_set_icon_stock(gtk.STOCK_MISSING_IMAGE)

