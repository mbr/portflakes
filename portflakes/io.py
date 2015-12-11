import os
import time
import threading
from queue import Queue

from gi.repository import GObject, GLib


class BackgroundIO(GObject.GObject):
    __gsignals__ = {'data-received': (GObject.SIGNAL_RUN_FIRST, None,
                                      (object, )),
                    'data-sent': (GObject.SIGNAL_RUN_FIRST, None,
                                  (object, )), }

    def __init__(self, *args, **kwargs):
        super(BackgroundIO, self).__init__(*args, **kwargs)
        self._send_queue = Queue()

    @property
    def name(self):
        return self.__class__.__name__

    def start_daemon(self):
        self._receive_thread = threading.Thread(
            target=self._run_receive_thread)
        self._receive_thread.daemon = True

        self._send_thread = threading.Thread(target=self._run_send_thread)
        self._send_thread.daemon = True

        self._receive_thread.start()
        self._send_thread.start()

    def send_data(self, data):
        self._send_queue.put(data)

    def _run_receive_thread(self):
        raise NotImplementedError()

    def _run_send_thread(self):
        raise NotImplementedError()

    @classmethod
    def new_and_start(cls, *args, **kwargs):
        instance = cls(*args, **kwargs)
        instance.start_daemon()
        return instance


class RandomDataGenerator(BackgroundIO):
    def __init__(self, delay, *args, **kwargs):
        super(RandomDataGenerator, self).__init__(*args, **kwargs)
        self.delay = delay

    def _run_send_thread(self):
        while True:
            data = b'ABC\n\x12'
            GLib.idle_add(self.emit, 'data-sent', data)
            time.sleep(self.delay)

    def _run_receive_thread(self):
        while True:
            data = os.urandom(2)
            GLib.idle_add(self.emit, 'data-received', data)
            time.sleep(self.delay)


class Echo(BackgroundIO):
    def _run_send_thread(self):
        while True:
            data = self._send_queue.get()

            GLib.idle_add(self.emit, 'data-sent', data)

            # receive right away
            GLib.idle_add(self.emit, 'data-received', data)

    def _run_receive_thread(self):
        pass


class SerialIO(BackgroundIO):
    def __init__(self, ser, *args, **kwargs):
        super(SerialIO, self).__init__(*args, **kwargs)
        self.ser = ser

    @property
    def name(self):
        return self.ser.port

    def _run_send_thread(self):
        while True:
            data = self._send_queue.get()

            idx = 0
            while idx != len(data):
                bytes_sent = self.ser.write(data[idx:])
                idx += bytes_sent
                GLib.idle_add(self.emit, 'data-sent', data)

    def _run_receive_thread(self):
        while True:
            data = self.ser.read()
            GLib.idle_add(self.emit, 'data-received', data)
