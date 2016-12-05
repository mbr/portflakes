import sys
from itertools import product
import json
import re
import time
from xml.etree import ElementTree as ET

import click
import serial
from .io import Echo, RandomDataGenerator, SerialIO
from .gui import run_gui
from .util import parse_8bit, decode_8bit

PARITIES = ['none', 'even', 'odd', 'mark', 'space']


@click.group()
def cli():
    pass


@cli.command(help='Open pseudo-device that echos back info')
def echo():
    run_gui(Echo.new_and_start())


@cli.command(help='Open pseudo-device producing random bytes')
@click.option('--delay', '-d', type=float, default=0.5)
def random(delay):
    run_gui(RandomDataGenerator.new_and_start(delay))


@cli.command('open', help='Show GUI on given serial device')
@click.argument('dev', type=click.Path(exists=True, dir_okay=False))
@click.option('--baudrate', '-b', type=int)
@click.option('--bytesize', '-B', type=int)
@click.option('--parity', '-p', type=click.Choice(PARITIES))
@click.option('--stopbits', '-s', type=click.Choice(['1', '1.5', '2']))
@click.option('--xonxoff', is_flag=True, default=False)
@click.option('--rts', is_flag=True, default=False)
@click.option('--dsr', is_flag=True, default=False)
@click.option('--seq', '-S', multiple=True, type=click.File())
def open_serial_device(dev, baudrate, bytesize, parity, stopbits, rts, dsr,
                       xonxoff, seq):
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

    seqs = [json.load(s) for s in seq]

    run_gui(SerialIO.new_and_start(ser), seqs)


@cli.command('try', help='Try multiple configurations, waiting for data')
@click.argument('dev', type=click.Path(exists=True, dir_okay=False))
@click.option('--send', '-s', type=parse_8bit)
@click.option('--expect', '-e', type=parse_8bit)
@click.option('--timeout', '-t', type=float, default=0.25)
@click.option('--delay', '-d', type=float, default=0.25)
def find_settings(dev, send, expect, timeout, delay):
    params = ([9600],
              [8],
              PARITIES,
              [serial.STOPBITS_ONE, serial.STOPBITS_ONE_POINT_FIVE,
               serial.STOPBITS_TWO],
              (False, True),
              (False, True),
              (False, True), )
    cs = product(*params)
    for baudrate, bytesize, parity, stopbits, xonxoff, rts, dsr in cs:
        sargs = {
            'port': dev,
            'baudrate': baudrate,
            'bytesize': bytesize,
            'parity': getattr(serial, 'PARITY_' + parity.upper()),
            'stopbits': stopbits,
            'xonxoff': xonxoff,
            'rtscts': rts,
            'dsrdtr': dsr,
            'timeout': timeout,
        }

        try:
            ser = serial.Serial(**sargs)
        except Exception as e:
            click.echo('Ignoring exception {}'.format(e))

        if send is not None:
            click.echo('Sending {!r}...'.format(send), nl=False)
            assert len(send) == ser.write(send)
            click.echo('OK')

        if not expect:
            click.echo('Waiting for any response from {}...'.format(dev),
                       nl=False)
            resp = ser.read()

            if not resp:
                click.echo('timeout')
            else:
                click.echo('OK')
                break
        else:
            raise NotImplementedError()
    else:
        click.echo('No settings matched')
        sys.exit(2)

    time.sleep(delay)

    click.echo('Settings:\n{}'.format(sargs))


@cli.command('convert-hts', help='Read .hts file')
@click.argument('htsfile', type=click.File())
def convert_hts(htsfile):
    BYTE_REGEX = re.compile(r'h\[([A-Za-z0-9]{2})\]$')

    root = ET.parse(htsfile).getroot()
    items = []

    for item in root.iter('SequenceItem'):
        name = item.attrib['name']

        seq = item.find('sequence').attrib['value'].split(' ')
        val = []
        for byte in seq:
            m = BYTE_REGEX.match(byte)
            if not m:
                raise ValueError('Cannot parse {!r}'.format(byte))

            val.append(int(m.group(1), 16))

        items.append((name, decode_8bit(bytes(val))))

    # FIXME: ini format probably better, can save one per device
    click.echo(json.dumps(items, indent=2))
