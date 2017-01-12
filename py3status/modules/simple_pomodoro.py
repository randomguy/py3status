#!/usr/bin/env python
# -*- coding: utf-8 -*-

# See https://github.com/ultrabug/py3status/wiki/Write-your-own-modules
#
# NOTE: py3status will NOT execute:
#     - methods starting with '_'
#     - methods decorated by @property and @staticmethod
#
# NOTE: reserved method names:
#     - 'kill' method for py3status exit notification
#     - 'on_click' method for click events from i3bar (read below please)
#
"""
WIP Pomodoro technique timer for py3status.

Another pomodoro timer with simpler UI

Configuration parameters:
    TODO
Format of status string placeholders:
    {output} output of this module

@author <Eduard Mai> <eduard.mai@posteo.de>
@license BSD
"""

from threading import Timer
from time import time
import logging
from abc import ABCMeta, abstractmethod

CACHE_FOREVER = -1
POMODORO_DURATION_SEC = 5 * 3
BREAK_DURATION_SEC = 5
FULL_BAR = "<span font='Material Design Icons 12'>■■■■■</span>"

logging.basicConfig(filename='example.log',
                    level=logging.DEBUG,
                    format='%(asctime)s|l.%(lineno)3d|%(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')


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


class State:
    __metaclass__ = ABCMeta

    def __init__(self, module):
        self._module = module

    @abstractmethod
    def enter(self):
        return

    @abstractmethod
    def exit(self):
        return


class TimerState(State):
    def __init__(self, module):
        self._timers = []
        super().__init__(module)

    @abstractmethod
    def exit(self):
        return

    @property
    def timers(self):
        return self._timers

    @timers.setter
    def timers(self, new_timers):
        self._timers = new_timers

    @property
    def future_timers(self):
        for timer in self.timers:
            if timer.is_active:
                yield timer

    def enter(self, duration):
        if not self.timers or not any(self.future_timers):
            self.timers = self._module._init_timers(duration)
            self._module.full_text = FULL_BAR
        else:
            self._module.full_text = self._old_text
            for timer in self.future_timers:
                timer.start()
        self._module.py3.update()


class StatePauseWorking(State):
    def enter(self):
        self._module.full_text = "<span font='Material Design Icons 12'></span> paused"
        self._module.update_bar()


class StateWorking(TimerState):
    def enter(self):
        super().enter(POMODORO_DURATION_SEC)

    def exit(self):
        self._old_text = self._module.full_text
        stopped_timers = []
        for timer in self.future_timers:
            timer.cancel()
            new = TimeleftTimer(timer.time_left, timer.function, timer.args)
            stopped_timers.append(new)
        self.timers = stopped_timers


class StateWaitForStart(State):
    def enter(self):
        self._module.full_text = "start <span font='Material Design Icons 12'></span>"
        self._module.update_bar()


class StateWaitForBreak(State):
    def enter(self):
        self._module.full_text = 'start break'


class StateTakingBreak(TimerState):
    def enter(self):
        super().enter(BREAK_DURATION_SEC)


class Py3status:
    # available configuration parameters
    cache_timeout = 10

    def __init__(self):
        wait_for_start = StateWaitForStart(self)
        working = StateWorking(self)
        pause_working = StatePauseWorking(self)
        wait_for_break = StateWaitForBreak(self)
        taking_break = StateTakingBreak(self)

        # define state transitions with dict(s)
        self._on_click_transitions = {
            wait_for_start: working,
            working: pause_working,
            pause_working: working,
            wait_for_break: taking_break}

        self._on_timer_transitions = {
            working: wait_for_break,
            taking_break: wait_for_start}

        self._state = wait_for_start
        self._state.enter()

    @property
    def full_text(self):
        return self._full_text

    @full_text.setter
    def full_text(self, new_text):
        self._full_text = new_text

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_state):
        self._state = new_state

    def _enter_next_state_on_timer(self):
        logging.debug('SWITCHING STATE VIA TIMER!')
        self._state = self._on_timer_transitions[self._state]
        self._state.enter()
        self.py3.update()

    def _enter_next_state_on_click(self):
        logging.debug('key on onclick transition:\n%s', self._state)
        self._state.exit()
        try:
            self._state = self._on_click_transitions[self._state]
        except KeyError:
            # Stay in the same state, as now following state was defined
            pass
        else:
            self._state.enter()
            self.update_bar()

    def _update_widget(self, text, cached_until):
        """ This is executed via TimeleftTimer instances"""
        self.full_text = text
        self.py3.update()

    def _init_timers(self, duration_in_seconds):
        """ This method will create 5 timers each firing after a fifth of
        duration_in_seconds """
        timer_interval = duration_in_seconds / 5
        timers = []
        text = FULL_BAR
        for i in range(1, 5):
            timer = TimeleftTimer(i * timer_interval,
                                  self._update_widget,
                                  [text.replace('■', '□', i), time() + i*timer_interval])
            timer.start()
            timers.append(timer)
        last = TimeleftTimer(duration_in_seconds, self._enter_next_state_on_timer)
        last.start()
        timers.append(last)
        return timers

    def kill(self, i3s_output_list, i3s_config):
        """
        This method will be called upon py3status exit.
        """
        pass

    def on_click(self, i3s_output_list, i3s_config, event):
        self._enter_next_state_on_click()
        self.update_bar()

    def update_bar(self):
        logging.debug('Executing update_bar.')
        response = {
            'cached_until': CACHE_FOREVER,
            'markup': 'pango',
            'full_text': self.full_text
        }
        return response


if __name__ == "__main__":
    """
    Test this module by calling it directly.
    This SHOULD work before contributing your module please.
    """
    from time import sleep
    x = Py3status()
    config = {
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
        'color_good': '#00FF00'
    }
    while True:
        print(x.update_bar())
        sleep(3)
# vim: expandtab
