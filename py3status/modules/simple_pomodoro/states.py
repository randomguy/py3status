#!/usr/bin/env python
# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod

from .utils import TimeleftTimer


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

    def cancel_future_timers(self):
        for timer in self.future_timers:
            timer.cancel()

    def enter(self, duration_minutes):
        if not self.timers or not any(self.future_timers):
            self.timers = self._module._init_timers(duration_minutes)
            self._module.full_text = 5 * self._module.full_bar_segment
        else:
            self._module.full_text = self._old_text
            for timer in self.future_timers:
                timer.start()
        self._module.py3.update()


class StatePauseWorking(State):

    def enter(self):
        self._module.full_text = "<span font='Material Design Icons 12'></span> paused"


class StateWorking(TimerState):

    def enter(self):
        super().enter(self._module.work_duration_minutes)

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


class StateWaitForBreak(State):

    def enter(self):
        # waiting for break means a pomodoro has been finished. Log pomodoro
        # completion to ~/.pomodoro.log
        self._module._pomdoro_log.completed_pomodoro()
        self._module.full_text = 'start break'
        self._module.py3.notify_user(
            'Please take a break now.', level='warning')
        self._module.py3.update(module_name='pomodoro_counter')


class StateTakingBreak(TimerState):

    def enter(self):
        super().enter(self._module.break_duration_minutes)
