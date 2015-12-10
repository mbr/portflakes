import click
from gi.repository import Gtk

from .io import Echo
from .gui import TermGUI


@click.command('portflakes')
def cli():
    io_thread = Echo()
    mw = TermGUI(io=io_thread)

    io_thread.start_daemon()
    mw.show_all()
    Gtk.main()
