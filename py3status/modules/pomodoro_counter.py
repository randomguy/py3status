#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Display pomodoro count. Depends on  simple_pomodoro.

A complementary widget for simple_pomodoro. It will parse the contents of
~/.pomodoro.log (written by simple_pomodoro) and display the number of
pomodoros completed today.

Configuration parameters:
    {output_format} use the status string placeholders below

Format of status string placeholders:
    {symbol} use a an icon font and pango markup for best results
    {today} pomodoros logged since today 6AM
    {week} same since monday 6AM
    {month} same since this months 1st 6AM

@author <randomguy>
@license BSD
"""
from datetime import datetime, timedelta
from os import path


class Py3status:
    output_format = u'{today} w:{week}'
    symbol = u"<span font='Material Design Icons 12'></span>"

    def _parse_and_truncate_log(self):
        self.today = 0
        self.week = 0
        self.month = 0
        log_lines = []
        with open(path.join(path.expanduser("~"), '.pomodoro.log'), 'r') as fd:
            threshold_today = datetime.today().replace(hour=6, minute=0, second=0)
            threshold_week = threshold_today - timedelta(days=datetime.today().isoweekday() % 7)
            threshold_month = threshold_today.replace(day=1)
            for line in fd:
                pom_time = datetime.strptime(line.strip(), '[%Y-%m-%d %H:%M:%S]')
                if pom_time > threshold_today:
                    self.today += 1
                if pom_time > threshold_week:
                    self.week += 1
                if pom_time > threshold_month:
                    self.month += 1
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
                'full_text': self.output_format.format(**self.__dict__)}
