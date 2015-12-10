from gi.repository import Gtk, Pango


class TermGUI(Gtk.Window):
    def __init__(self, io=None, *args, **kwargs):
        super(TermGUI, self).__init__(*args, **kwargs)

        self.set_name('portflakes')

        # build gui
        self.mbox = Gtk.VBox()
        self.add(self.mbox)

        top = MultiFormatViewer()
        bottom = Gtk.Button(label="bottom")

        self.mbox.pack_start(top, True, True, 0)
        self.mbox.pack_start(bottom, False, True, 0)

        self.connect("delete-event", Gtk.main_quit)

        # connect to io
        if io:
            io.connect('data-received', lambda _, d: top.append_incoming(d))
            io.connect('data-sent', lambda _, d: top.append_outgoing(d))


class DataView(Gtk.TextView):
    def __init__(self, buffer=None, *args, **kwargs):
        super(DataView, self).__init__(*args, **kwargs)

        if buffer:
            self.set_buffer(buffer)

        self._style()

    def _style(self):
        self.modify_font(Pango.FontDescription('Monospace'))
        self.set_wrap_mode(Gtk.WrapMode.CHAR)

    def append_incoming(self, data):
        tb = self.get_buffer()
        tb.insert(tb.get_end_iter(), repr(data))

    def append_outgoing(self, data):
        tb = self.get_buffer()
        tb.insert(tb.get_end_iter(), repr(data))


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

    def append_incoming(self, data):
        tb = self.get_buffer()
        pos = tb.get_end_iter()

        for c in data:
            # printable range
            if 32 <= c < 127:
                tb.insert(pos, chr(c))
                continue

            fmt = self.map.get(c, None)

            if fmt:
                tb.insert_with_tags(pos, *fmt)
                continue

            tb.insert_with_tags(pos, r'\x{:x}'.format(c), self.tag_non_ascii)


class HexView(DataView):
    def _style(self):
        super(HexView, self)._style()
        self.set_wrap_mode(Gtk.WrapMode.WORD)

    def append_incoming(self, data):
        tb = self.get_buffer()
        pos = tb.get_end_iter()

        for c in data:
            tb.insert(pos, '{:02x} '.format(c))


class MultiFormatViewer(Gtk.Notebook):
    def __init__(self, *args, **kwargs):
        super(MultiFormatViewer, self).__init__(*args, **kwargs)

        self.view_ascii = ASCIIView()
        self.view_hex = HexView()

        self.append_page(self.view_ascii, Gtk.Label('ASCII'))
        self.append_page(self.view_hex, Gtk.Label('Hex'))

    def append_incoming(self, data):
        self.view_ascii.append_incoming(data)
        self.view_hex.append_incoming(data)
