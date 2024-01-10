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

""" Tool """

import logging


def apply():
    """ Apply logging patches / caveat workarounds """
    # Disable requests/urllib3 logging
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    # Disable SSL warnings
    try:
        import urllib3  # pylint: disable=C0415,E0401
        urllib3.disable_warnings()
    except:  # pylint: disable=W0702
        pass
    #
    try:
        import requests  # pylint: disable=C0415,E0401
        requests.packages.urllib3.disable_warnings()  # pylint: disable=E1101
    except:  # pylint: disable=W0702
        pass
    # Disable additional logging
    logging.getLogger("pika").setLevel(logging.WARNING)
    logging.getLogger("paramiko.hostkeys").setLevel(logging.WARNING)
