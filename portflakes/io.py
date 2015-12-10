import os
import time
import threading

from gi.repository import GObject, GLib


class BackgroundIO(GObject.GObject):
    __gsignals__ = {'data-received': (GObject.SIGNAL_RUN_FIRST, None,
                                      (object, )),
                    'data-sent': (GObject.SIGNAL_RUN_FIRST, None,
                                  (object, )), }

    def start_daemon(self):
        self._receive_thread = threading.Thread(
            target=self._run_receive_thread)
        self._receive_thread.daemon = True

        self._send_thread = threading.Thread(target=self._run_send_thread)
        self._send_thread.daemon = True

        self._receive_thread.start()
        self._send_thread.start()

    def _run_receive_thread(self):
        raise NotImplementedError()

    def _run_send_thread(self):
        raise NotImplementedError()


class RandomDataGenerator(BackgroundIO):
    def _run_send_thread(self):
        while True:
            data = b'ABC\n\x12'
            GLib.idle_add(self.emit, 'data-sent', data)
            time.sleep(1)

    def _run_receive_thread(self):
        while True:
            data = os.urandom(2)
            GLib.idle_add(self.emit, 'data-received', data)
            time.sleep(1)
