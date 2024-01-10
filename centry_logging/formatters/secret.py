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

""" Formatter """

import re
import logging

from ..internal import constants


class SecretFormatter(logging.Formatter):
    """ Formatter to hide secrets in logs """

    def __init__(  # pylint: disable=R0913
            self,
            fmt=constants.LOG_FORMAT, datefmt=constants.LOG_DATE_FORMAT,
            style='%', validate=True, *, defaults=None,
            secrets=None,
            secrets_formatter=constants.DEFAULT_SECRETS_FORMATTER,
            secrets_replacer=constants.DEFAULT_SECRETS_REPLACER,
    ):
        super().__init__(
            fmt=fmt, datefmt=datefmt, style=style, validate=validate, defaults=defaults
        )
        #
        self.secrets = set()
        self.update_secrets(secrets)
        #
        try:
            self.formatter = getattr(self, secrets_formatter)
        except AttributeError:
            self.formatter = self.replacer_re
        #
        self.replacer = secrets_replacer
        self.restricted_stop_words = {'', self.replacer}

    def update_secrets(self, secrets):
        """ Update secret list """
        #
        if secrets is None:
            return
        #
        if isinstance(secrets, self.__class__):
            self.secrets.update(secrets.secrets)
        #
        elif isinstance(secrets, logging.Handler):
            if isinstance(secrets.formatter, self.__class__):
                self.secrets.update(secrets.formatter.secrets)
        #
        elif isinstance(secrets, logging.Logger):
            for item in secrets.handlers:
                if isinstance(item.formatter, self.__class__):
                    self.secrets.update(item.formatter.secrets)
        #
        else:  # list / iterable
            self.secrets.update(set(map(str, secrets)))
        #
        self.__censor_stop_words()

    def __censor_stop_words(self) -> None:
        for i in self.restricted_stop_words:
            try:
                self.secrets.remove(i)
            except KeyError:
                ...

    @property
    def re_pattern(self):
        """ Regex pattern """
        return re.compile(r'\b(?:{})\b'.format('|'.join(map(re.escape, self.secrets))))  # pylint: disable=C0209

    def replacer_re(self, text: str) -> str:
        """ Replacer method: replaces only separate words """
        return re.sub(self.re_pattern, self.replacer, text)

    def replacer_iter(self, text: str) -> str:
        """ Replacer method: replaces every occurrence """
        for i in self.secrets:
            text = text.replace(i, self.replacer)
        #
        return text

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        #
        if not self.secrets:
            return formatted
        #
        return self.formatter(formatted)
