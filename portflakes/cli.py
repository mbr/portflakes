import click
from gi.repository import Gtk

from .io import RandomDataGenerator
from .gui import TermGUI


@click.command('portflakes')
def cli():
    io_thread = RandomDataGenerator()
    mw = TermGUI(io=io_thread)

    io_thread.start_daemon()
    mw.show_all()
    Gtk.main()
