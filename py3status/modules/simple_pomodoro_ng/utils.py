#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
from time import time
from threading import Timer


class PomodoroLogger():

    def __init__(self, log_path):
        self._log_file = open(log_path, 'a')

    def __exit__(self, exc_type, exc_value, traceback):
        self._log_file.close()

    def completed_pomodoro(self):
        self._log_file.write('{}\n'.format(
            datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')))
        self._log_file.flush()


class TimeleftTimer(Timer):

    def __init__(self, interval, *args, **kwargs):
        super().__init__(interval, *args, **kwargs)
        self._target_time = time() + interval

    @property
    def time_left(self):
        if self.is_active:
            return self._target_time - time()
        else:
            return None

    @property
    def is_active(self):
        return self._target_time > time()
