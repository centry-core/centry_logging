#!/usr/bin/python3
# coding=utf-8

#   Copyright 2024 getcarrier.io
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

""" Tools """

import time
import threading


class PeriodicFlush(threading.Thread):  # pylint: disable=R0903
    """ Flush logger time to time """

    def __init__(self, handler, interval=30):
        super().__init__(daemon=True)
        #
        self.interval = interval
        self.handlers = handler
        #
        if not isinstance(self.handlers, list):
            self.handlers = [self.handlers]

    def run(self):
        """ Run handler thread """
        while True:
            time.sleep(self.interval)
            #
            for handler in self.handlers:
                try:
                    handler.flush()
                except:  # pylint: disable=W0702
                    pass  # Just ignore
