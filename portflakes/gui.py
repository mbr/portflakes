from gi.repository import Gtk, Pango


class TermGUI(Gtk.Window):
    def __init__(self, *args, **kwargs):
        super(TermGUI, self).__init__(*args, **kwargs)

        # storage for input data
        self.buffer = bytearray("Hel<b>l</b>\r\no, world\n\x12".encode(
            'ascii'))

        # build gui
        self.mbox = Gtk.VBox()
        self.add(self.mbox)

        top = MultiFormatViewer()
        top.set_data(self.buffer)
        bottom = Gtk.Button(label="bottom")

        self.mbox.pack_start(top, True, True, 0)
        self.mbox.pack_start(bottom, False, True, 0)

        self.connect("delete-event", Gtk.main_quit)


class DataView(Gtk.TextView):
    def __init__(self, buffer=None, *args, **kwargs):
        super(DataView, self).__init__(*args, **kwargs)

        if buffer:
            self.set_buffer(buffer)

        self._style()

    def _style(self):
        self.modify_font(Pango.FontDescription('Monospace'))

    def set_data(self, data):
        self._data = data
        self._update()

    def _update(self):
        s = repr(self._data)
        self.get_buffer().set_text(s)


class ASCIIView(DataView):
    def __init__(self, *args, **kwargs):
        super(ASCIIView, self).__init__(*self, **kwargs)

        # create tags
        tb = self.get_buffer()
        self.tag_non_ascii = tb.create_tag('non_ascii', foreground='#cc0000')
        self.tag_nl = tb.create_tag('nl', foreground='#777')

        self.map = {
            0x09: (r'\t', self.tag_non_ascii),
            0x0a: ('\\n\n', self.tag_nl),
            0x0d: (r'\r', self.tag_nl),
        }

    def _update(self):
        tb = self.get_buffer()

        # empty
        tb.delete(tb.get_start_iter(), tb.get_end_iter())

        pos = tb.get_start_iter()

        for c in self._data:
            # printable range
            if 32 <= c < 127:
                tb.insert(pos, chr(c))
                continue

            fmt = self.map.get(c, None)

            if fmt:
                print(fmt)
                tb.insert_with_tags(pos, *fmt)
                continue

            tb.insert_with_tags(pos, r'\x{:x}'.format(c), self.tag_non_ascii)


class MultiFormatViewer(Gtk.Notebook):
    def __init__(self, *args, **kwargs):
        super(MultiFormatViewer, self).__init__(*args, **kwargs)

        self.view_ascii = ASCIIView()
        self.view_hex = DataView()

        self.append_page(self.view_ascii, Gtk.Label('ASCII'))
        self.append_page(self.view_hex, Gtk.Label('Hex'))

    def set_data(self, data):
        self.view_ascii.set_data(data)
        self.view_hex.set_data(data)
