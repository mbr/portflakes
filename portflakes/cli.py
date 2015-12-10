import click

from .io import Echo, RandomDataGenerator
from .gui import run_gui


@click.group()
def cli():
    pass


@cli.command()
def echo():
    run_gui(Echo.new_and_start())


@cli.command()
def random():
    run_gui(RandomDataGenerator.new_and_start())
