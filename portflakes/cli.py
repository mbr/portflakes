import click
from gi.repository import Gtk, GLib

from .io import RandomDataGenerator
from .gui import TermGUI


@click.command('portflakes')
def cli():
    mw = TermGUI()
    gen = RandomDataGenerator()
    gen.start_thread()
    gen.connect('data-received', lambda s, d: print('-> {!r} {!r}'.format
        (s, d)))
    mw.show_all()
    Gtk.main()
