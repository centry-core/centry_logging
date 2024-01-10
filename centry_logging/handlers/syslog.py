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

""" Handler """

import socket
import logging
import logging.handlers


class SysLogHandler(logging.handlers.SysLogHandler):
    """ Log handler - send logs to syslog """

    def __init__(self, settings):
        address = (
            settings.get("address", "localhost"),
            settings.get("port", 514)
        )
        facility = settings.get("facility", "user")
        socktype = socket.SOCK_DGRAM if settings.get("socktype", "udp").lower() == "udp" \
            else socket.SOCK_STREAM
        #
        super().__init__(
            address=address,
            facility=facility,
            socktype=socktype,
        )
