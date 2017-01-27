#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pomodoro technique timer for py3status.

A pomodoro timer with simple and low distraction UI. It uses i3-nagbar for noti-
fications.

Mouse button 1 toggles next phase.
Mouse button 2 resets the timer to wait for the begin of a pomodoro.

Configuration parameters:
    {break_duration_minutes} Sets the timespan for the break after a pomodoro,
         5min default.
    {work_duration_minutes} Sets the timespan for a pomodoro, 25min recommended.
    {empty_bar_segment} A single char displayed for an empty segment during
        work and brak phases.
    {full_bar_segment} Same as above for the full segment of the bar.

Format of status string placeholders:
    None as of now.

Color options:
    None as of now.

config example:
simple_pomodoro {
    # From Material Design Icons font
    empty_bar_segment = ''
    full_bar_segment = ''
    # more agressive timings
    work_duration_minutes = 30
    break_duration_minutes = 3
}

@author <Eduard Mai> <eduard.mai@posteo.de>
@license BSD
"""
from os import path
from .utils import PomodoroLogger, TimeleftTimer
from .states import StateWaitForStart, StateWorking, StatePauseWorking
from .states import StateWaitForBreak, StateTakingBreak, TimerState

POMODORO_LOG_PATH = path.join(path.expanduser('~'), '.pomodoro.log')


class Py3status:
    empty_bar_segment = ""
    full_bar_segment = ""
    break_duration_minutes = 5
    work_duration_minutes = 25

    def __init__(self):
        self._initial_state()
        self._pomdoro_log = PomodoroLogger(POMODORO_LOG_PATH)

    def _initial_state(self):
        wait_for_start = StateWaitForStart(self)
        working = StateWorking(self)
        pause_working = StatePauseWorking(self)
        wait_for_break = StateWaitForBreak(self)
        taking_break = StateTakingBreak(self)

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
        self._state = self._on_timer_transitions[self._state]
        self._state.enter()
        self.py3.update()

    def _enter_next_state_on_click(self):
        self._state.exit()
        try:
            self._state = self._on_click_transitions[self._state]
        except KeyError:
            # Stay in the same state, as now following state was defined
            pass
        else:
            self._state.enter()
            self.update_output()

    def _update_widget(self, text):
        """ This is executed via TimeleftTimer instances """
        self.full_text = text
        self.py3.update()

    def _init_timers(self, duration_minutes):
        """ Create 5 timers each firing after a fifth of duration_minutes """
        timer_interval = duration_minutes / 5
        timers = []
        for i in range(1, 5):
            widget_text = (5 * self.full_bar_segment).replace(
                self.full_bar_segment, self.empty_bar_segment, i)
            timer = TimeleftTimer(
                        i * timer_interval * 60,
                        self._update_widget,
                        [widget_text])
            timer.start()
            timers.append(timer)
        last = TimeleftTimer(duration_minutes * 60, self._enter_next_state_on_timer)
        last.start()
        timers.append(last)
        return timers

    def on_click(self, i3s_output_list, i3s_config, event):
        if event['button'] == 1:
            self._enter_next_state_on_click()
        elif event['button'] == 2:
            # reset state machine
            if isinstance(self.state, TimerState):
                self.state.cancel_future_timers()
            self._initial_state()

    def update_output(self):
        response = {
            'cached_until': self.py3.CACHE_FOREVER,
            'markup': 'pango',
            'full_text': self.full_text
        }
        return response
