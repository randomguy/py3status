#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WIP a simple widget to display daily pomodoro count

A complementary widget for simple_pomodoro. It will parse the contents of
~/.pomodoro.log and display the number of pomodoros completed today.

Configuration parameters:
    TODO
Format of status string placeholders:
    {output} output of this module

@author <Eduard Mai> <eduard.mai@posteo.de>
@license BSD
"""
from datetime import datetime
from os import path


class Py3status:
    def _parse_and_truncate_log(self):
        self._today = 0
        log_lines = []
        with open(path.join(path.expanduser("~"), '.pomodoro.log'), 'r') as fd:
            threshold = datetime.today().replace(hour=6, minute=0, second=0)
            for line in fd:
                pom_time = datetime.strptime(line.strip(), '[%Y-%m-%d %H:%M:%S]')
                if pom_time > threshold:
                    self._today += 1
                    log_lines.append(line)
        # Only write back lines with times over threshold. This will truncate
        # the log so it won't grow infinitely
        with open(path.join(path.expanduser("~"), '.pomodoro.log'), 'w') as fd:
            fd.writelines(log_lines)

    def on_click(self, i3s_output_list, i3s_config, event):
        pass

    def update_output(self):
        self._parse_and_truncate_log()
        return {
                'cached_until': self.py3.CACHE_FOREVER,
                'full_text': str(self._today)
        }
