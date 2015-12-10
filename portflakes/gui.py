from gi.repository import Gtk, Pango, GObject, Gio

from .util import parse_8bit


def run_gui(io, seqs=[]):
    mw = TermGUI(io=io)

    for seq in seqs:
        mw.load_sequences(seq)

    mw.show()

    Gtk.main()


class TermGUI(Gtk.Window):
    def __init__(self, io=None, *args, **kwargs):
        super(TermGUI, self).__init__(*args, **kwargs)

        self.set_name('portflakes')
        self.sequence_model = Gtk.ListStore(str, str)

        # build gui
        root = Gtk.VBox()
        self.add(root)

        # header
        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.props.title = 'portflakes: {}'.format(io.name)

        seq_button = Gtk.Button()
        seq_icon = Gio.ThemedIcon(name="folder")
        seq_image = Gtk.Image.new_from_gicon(seq_icon, Gtk.IconSize.BUTTON)
        seq_button.add(seq_image)
        header.pack_end(seq_button)

        root.pack_start(header, False, True, 0)

        # ibox: displays input/output and entry
        ibox = Gtk.VBox()

        viewer = MultiFormatViewer()
        entry = DataEntry()

        ibox.pack_start(viewer, True, True, 0)
        ibox.pack_start(entry, False, True, 0)

        # sequence tree
        ftree = SequenceTree(self.sequence_model)
        ftree.set_size_request(150, 0)
        ftree_scroll = Gtk.ScrolledWindow()
        ftree_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        ftree_scroll.add(ftree)
        seq_button.connect(
            'clicked',
            lambda _: ftree_scroll.set_visible(not ftree_scroll.get_visible()))

        # center box
        mbox = Gtk.Box()
        mbox.pack_start(ibox, True, True, 0)
        mbox.pack_start(ftree_scroll, False, True, 0)
        root.pack_start(mbox, True, True, 0)

        self.connect('delete-event', Gtk.main_quit)

        # connect to io
        if io:
            io.connect('data-received', lambda _, d: viewer.append(d, 'in'))
            io.connect('data-sent', lambda _, d: viewer.append(d, 'out'))
            ftree.connect('send-sequence', lambda _, d: io.send_data(d))

            entry.connect('data-entered', lambda _, d: io.send_data(d))

        self.show_all()
        ftree_scroll.hide()

    def load_sequences(self, seqs):
        for row in seqs:
            self.sequence_model.append(row)


class SequenceTree(Gtk.VBox):
    __gsignals__ = {'send-sequence': (GObject.SIGNAL_RUN_FIRST, None,
                                      (object, )), }

    def __init__(self, model, *args, **kwargs):
        super(SequenceTree, self).__init__(*args, **kwargs)

        self.view = Gtk.TreeView(model)
        self.view.set_model(model)

        col_name = Gtk.TreeViewColumn('Command')
        col_sequence = Gtk.TreeViewColumn('Sequence')

        r_name = Gtk.CellRendererText()
        r_sequence = Gtk.CellRendererText()

        col_name.pack_start(r_name, True)
        col_name.add_attribute(r_name, 'text', 0)

        col_sequence.pack_start(r_sequence, True)
        col_sequence.add_attribute(r_sequence, 'text', 1)

        self.view.append_column(col_name)
        self.view.append_column(col_sequence)

        self.pack_start(self.view, True, True, 0)

        send_button = Gtk.Button('Send sequence')
        send_button.connect('clicked', self._on_send_button_clicked)

        self.pack_start(send_button, False, True, 0)

    def _on_send_button_clicked(self, _):
        sel = self.view.get_selection()

        if sel:
            seq = sel.get_selected_rows()[0][0][1]
            self.emit('send-sequence', parse_8bit(seq))


class CellRendererButton(Gtk.CellRenderer):
    pass


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


class EightBitInput(Gtk.HBox):
    __gsignals__ = {'bytes-entered': (GObject.SIGNAL_RUN_FIRST, None,
                                      (object, )), }

    def __init__(self, *args, **kwargs):
        super(EightBitInput, self).__init__(*args, **kwargs)

        self.entry = EightBitEntry()
        self.combo = Gtk.ComboBoxText()
        self.combo.append_text('')
        self.combo.append_text(r'\r\n')
        self.combo.append_text(r'\n')
        self.combo.append_text(r'\r')

        self.combo.set_active(1)

        self.pack_start(self.entry, True, True, 0)
        self.pack_start(self.combo, False, True, 0)

        self.entry.connect('bytes-entered', self._on_entered)

    def _on_entered(self, _, data):
        suffix = self.combo.get_active_text()

        if suffix:
            data = data + parse_8bit(suffix)

        self.emit('bytes-entered', data)


class DataEntry(Gtk.Notebook):
    __gsignals__ = {'data-entered': (GObject.SIGNAL_RUN_FIRST, None,
                                     (object, )), }

    def __init__(self, *args, **kwargs):

        super(DataEntry, self).__init__(*args, **kwargs)

        eight_bit = EightBitInput()
        self.append_page(eight_bit, Gtk.Label('Direct Entry'))

        eight_bit.connect('bytes-entered',
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
