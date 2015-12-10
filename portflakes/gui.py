from gi.repository import Gtk, Pango, GObject

from .util import parse_8bit


class TermGUI(Gtk.Window):
    def __init__(self, io=None, *args, **kwargs):
        super(TermGUI, self).__init__(*args, **kwargs)

        self.set_name('portflakes')

        # build gui
        self.mbox = Gtk.VBox()
        self.add(self.mbox)

        top = MultiFormatViewer()
        bottom = DataEntry()

        self.mbox.pack_start(top, True, True, 0)
        self.mbox.pack_start(bottom, False, True, 0)

        self.connect('delete-event', Gtk.main_quit)

        # connect to io
        if io:
            io.connect('data-received', lambda _, d: top.append(d, 'in'))
            io.connect('data-sent', lambda _, d: top.append(d, 'out'))

            bottom.connect('data-entered', lambda _, d: io.send_data(d))


class EightBitEntry(Gtk.Entry):
    __gsignals__ = {'bytes-entered': (GObject.SIGNAL_RUN_FIRST, None,
                                      (object, )), }

    def __init__(self, *args, **kwargs):
        super(EightBitEntry, self).__init__(*args, **kwargs)

        self.connect('activate', self._on_activate)

    def _on_activate(self, *args):
        try:
            raw = parse_8bit(self.get_text())
        except UnicodeEncodeError as e:
            char = e.args[1]

            dlg = Gtk.MessageDialog(
                self.get_toplevel(), Gtk.DialogFlags.MODAL,
                Gtk.MessageType.ERROR, Gtk.ButtonsType.OK,
                'Cannot encode {}. Escape non-ascii characters using \\x'
                .format(char))
            dlg.run()
            dlg.destroy()
            return
        except Exception as e:
            dlg = Gtk.MessageDialog(self.get_toplevel(), Gtk.DialogFlags.MODAL,
                                    Gtk.MessageType.ERROR, Gtk.ButtonsType.OK,
                                    str(e))
            dlg.run()
            dlg.destroy()
            return

        # we got valid, sendable raw input! hooray
        self.emit('bytes-entered', raw)
        self.set_text('')


class DataEntry(Gtk.Notebook):
    __gsignals__ = {'data-entered': (GObject.SIGNAL_RUN_FIRST, None,
                                     (object, )), }

    def __init__(self, *args, **kwargs):

        super(DataEntry, self).__init__(*args, **kwargs)

        entry = EightBitEntry()
        self.append_page(entry, Gtk.Label('Direct entry'))

        entry.connect('bytes-entered',
                      lambda _, d: self.emit('data-entered', d))


class DataView(Gtk.TextView):
    def __init__(self, buffer=None, *args, **kwargs):
        super(DataView, self).__init__(*args, **kwargs)

        if buffer:
            self.set_buffer(buffer)

        self._style()

        tb = self.get_buffer()
        self.tag_incoming = tb.create_tag('incoming', foreground='#aa3')
        self.tag_outgoing = tb.create_tag('outgoing', foreground='#88f')

    def _style(self):
        ctx = self.get_style_context()
        ctx.add_class('data_view')

        style_provider = Gtk.CssProvider()
        css = b"""
        GtkTextView.data_view {
            background-color: #222;
            color: #eee;
        }
        """

        style_provider.load_from_data(css)
        ctx.add_provider(style_provider,
                         Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.modify_font(Pango.FontDescription('Monospace'))
        self.set_wrap_mode(Gtk.WrapMode.CHAR)

    def append(self, data, direction):
        tb = self.get_buffer()
        tb.insert_with_tags(tb.get_end_iter(), repr(data), self.tag_incoming if
                            direction == 'in' else self.tag_outgoing)


class ASCIIView(DataView):
    def __init__(self, *args, **kwargs):
        super(ASCIIView, self).__init__(*self, **kwargs)

        # create tags
        tb = self.get_buffer()
        self.tag_non_ascii = tb.create_tag('non_ascii', background='#333')
        self.tag_nl = tb.create_tag('nl', background='#000')

        self.map = {
            0x09: (r'\t', self.tag_non_ascii),
            0x0a: ('\\n\n', self.tag_nl),
            0x0d: (r'\r', self.tag_nl),
        }

    def append(self, data, direction):
        tb = self.get_buffer()
        pos = tb.get_end_iter()

        for c in data:
            tags = [self.tag_incoming if direction == 'in' else
                    self.tag_outgoing]

            # printable range
            if 32 <= c < 127:
                buf = chr(c)
            elif c in self.map:
                fmt = self.map[c]
                buf = fmt[0]
                tags.extend(fmt[1:])
            else:
                buf = r'\x{:x}'.format(c)
                tags.append(self.tag_non_ascii)

            tb.insert_with_tags(pos, buf, *tags)


class HexView(DataView):
    def __init__(self, *args, **kwargs):
        super(HexView, self).__init__(*args, **kwargs)

        tb = self.get_buffer()
        self.tag_incoming = tb.create_tag('incoming_bg', background='#660')
        self.tag_outgoing = tb.create_tag('outgoing_bg', background='#338')

    def _style(self):
        super(HexView, self)._style()
        self.set_wrap_mode(Gtk.WrapMode.WORD)

    def append(self, data, direction):
        tb = self.get_buffer()
        pos = tb.get_end_iter()

        for c in data:
            tb.insert_with_tags(pos, '{:02x} '.format(c), self.tag_incoming if
                                direction == 'in' else self.tag_outgoing)


class MultiFormatViewer(Gtk.Notebook):
    def __init__(self, *args, **kwargs):
        super(MultiFormatViewer, self).__init__(*args, **kwargs)

        self.view_ascii = ASCIIView()
        self.view_hex = HexView()

        self.append_page(self.view_ascii, Gtk.Label('ASCII'))
        self.append_page(self.view_hex, Gtk.Label('Hex'))

    def append(self, data, direction):
        self.view_ascii.append(data, direction)
        self.view_hex.append(data, direction)
