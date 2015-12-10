import os
import time
import threading

from gi.repository import GObject, GLib


class BackgroundIO(GObject.GObject):
    __gsignals__ = {'data-received': (GObject.SIGNAL_RUN_FIRST, None,
                                      (object, ))}

    def start_thread(self):
        self._thread = threading.Thread(target=self._run_thread)
        self._thread.daemonize = True
        self._thread.start()

    def _run_thread(self):
        raise NotImplementedError()


class RandomDataGenerator(BackgroundIO):
    def _run_thread(self):
        while True:
            time.sleep(1)
            data = os.urandom(2)
            GLib.idle_add(self.emit, 'data-received', data)
