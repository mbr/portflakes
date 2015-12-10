import click
from gi.repository import Gtk

from .gui import TermGUI


@click.command('hts-miniterm')
def cli():
    mw = TermGUI()
    mw.show_all()
    Gtk.main()
