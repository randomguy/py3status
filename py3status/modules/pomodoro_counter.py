#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Display pomodoro count. Depends on  simple_pomodoro.

A complementary widget for simple_pomodoro. It will parse the contents of
~/.pomodoro.log (written by simple_pomodoro) and display the number of
pomodoros completed today.

Configuration parameters:
    TODO
Format of status string placeholders:
    {output} output of this module

@author <randomguy>
@license BSD
"""
from datetime import datetime, timedelta
from os import path

# POMODORO_SYMBOL = u"<span font='Material Design Icons 12'></span>"
POMODORO_SYMBOL = u"<span font='Material Design Icons 12'></span>"


class Py3status:
    def _parse_and_truncate_log(self):
        self._today = 0
        self._week = 0
        self._month = 0
        log_lines = []
        with open(path.join(path.expanduser("~"), '.pomodoro.log'), 'r') as fd:
            threshold_today = datetime.today().replace(hour=6, minute=0, second=0)
            threshold_week = threshold_today - timedelta(days=datetime.today().isoweekday() % 7)
            threshold_month = threshold_today.replace(day=1)
            for line in fd:
                pom_time = datetime.strptime(line.strip(), '[%Y-%m-%d %H:%M:%S]')
                if pom_time > threshold_today:
                    self._today += 1
                if pom_time > threshold_week:
                    self._week += 1
                if pom_time > threshold_month:
                    self._month += 1
                else:
                    # older than a month, will be dropped
                    continue
                log_lines.append(line)
        # Only write back lines with times over threshold. This will truncate
        # the log so it won't grow infinitely
        with open(path.join(path.expanduser("~"), '.pomodoro.log'), 'w') as fd:
            fd.writelines(log_lines)

    def update_output(self):
        self._parse_and_truncate_log()
        return {
                'cached_until': self.py3.CACHE_FOREVER,
                'markup': 'pango',
                'full_text': '{} {} {} {}'.format(
                    POMODORO_SYMBOL, self._today, self._week, self._month)
        }
