import click

import serial
from .io import Echo, RandomDataGenerator, SerialIO
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


@cli.command('open')
@click.argument('dev', type=click.Path(exists=True, dir_okay=False))
@click.option('--baudrate', '-b', type=int)
@click.option('--bytesize', '-B', type=int)
@click.option('--parity',
              '-p',
              type=click.Choice(['none', 'even', 'odd', 'mark', 'space']))
@click.option('--stopbits', '-s', type=click.Choice(['1', '1.5', '2']))
@click.option('--xonxoff', is_flag=True, default=False)
@click.option('--rts', is_flag=True, default=False)
@click.option('--dsr', is_flag=True, default=False)
def open_serial_device(dev, baudrate, bytesize, parity, stopbits, rts, dsr,
                       xonxoff):
    sargs = {'port': dev}

    if baudrate is not None:
        sargs['baudrate'] = baudrate

    if bytesize is not None:
        sargs['bytesize'] = bytesize

    if parity:
        sargs['parity'] = getattr(serial, 'PARITY_' + parity.upper())

    if stopbits:
        sargs['stopbits'] = {
            '1': serial.STOPBITS_ONE,
            '1.5': serial.STOPBITS_ONE_POINT_FIVE,
            '2': serial.STOPBITS_TWO
        }

    sargs['rtscts'] = rts
    sargs['dsrdtr'] = dsr
    sargs['xonxoff'] = xonxoff

    ser = serial.Serial(**sargs)
    assert ser.isOpen()
    click.echo(ser)

    run_gui(SerialIO.new_and_start(ser))
