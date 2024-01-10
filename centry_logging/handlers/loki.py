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

import time
import logging
import traceback

from ..emitters.loki import CarrierLokiLogEmitter
from ..tools.flush import PeriodicFlush


class CarrierLokiLogHandler(logging.Handler):
    """ Log handler - send logs to storage """

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        #
        self.emitter = CarrierLokiLogEmitter(
            loki_push_url=self.settings.get("url"),
            loki_user=self.settings.get("user", None),
            loki_password=self.settings.get("password", None),
            loki_token=self.settings.get("token", None),
            default_labels=self.settings.get("labels", {}),
            verify=self.settings.get("verify", False),
            # retries=3,
            # retry_delay=0.5,
            # timeout=15,
        )

    def handleError(self, record):
        """ Handle error while logging """
        super().handleError(record)
        self.emitter.disconnect()

    def emit(self, record):
        try:
            record_ts = int(record.created * 1000000000)
            record_data = self.format(record)
            #
            additional_labels = {}
            if self.settings.get("include_level_name", True):
                additional_labels["level"] = record.levelname
            if self.settings.get("include_logger_name", True):
                additional_labels["logger"] = record.name
            #
            self.emitter.emit_line(record_ts, record_data, additional_labels)
        except:  # pylint: disable=W0702
            # In this case we should NOT use logging to log logging error. Only print()
            print("[FATAL] Exception during sending logs")
            traceback.print_exc()


class CarrierLokiBufferedLogHandler(logging.handlers.BufferingHandler):
    """ Log handler - buffer and send logs to storage """

    def __init__(self, settings):
        super().__init__(settings.get("buffer_capacity", 100))
        self.settings = settings
        #
        self.emitter = CarrierLokiLogEmitter(
            loki_push_url=self.settings.get("url"),
            loki_user=self.settings.get("user", None),
            loki_password=self.settings.get("password", None),
            loki_token=self.settings.get("token", None),
            default_labels=self.settings.get("labels", {}),
            verify=self.settings.get("verify", False),
            # retries=3,
            # retry_delay=0.5,
            # timeout=15,
        )
        #
        self.last_flush = 0.0
        self.flush_locked = self.settings.get("flush_locked", True)
        PeriodicFlush(self, self.settings.get("buffer_flush_deadline", 30)).start()

    def handleError(self, record):
        """ Handle error while logging """
        super().handleError(record)
        self.emitter.disconnect()

    def shouldFlush(self, record):
        """ Check if we need to flush messages """
        return \
            (len(self.buffer) >= self.capacity) or \
            (time.time() - self.last_flush) >= self.settings.get("buffer_flush_interval", 10)

    def flush(self):
        self.acquire()
        try:
            log_records = []
            while self.buffer:
                record = self.buffer.pop(0)
                record_ts = int(record.created * 1000000000)
                record_data = self.format(record)
                # TODO: batches with different stream labels (a.k.a. multiple streams support)
                log_records.append([f"{record_ts}", record_data])
            #
            if self.flush_locked and log_records:
                self.emitter.emit_batch(log_records)
        except:  # pylint: disable=W0702
            # In this case we should NOT use logging to log logging error. Only print()
            if self.flush_locked:
                print("[FATAL] Exception during sending logs")
            else:
                print("[FATAL] Exception during formatting logs")
            traceback.print_exc()
        finally:
            self.release()
            self.last_flush = time.time()
        #
        if not self.flush_locked:
            try:
                if log_records:
                    self.emitter.emit_batch(log_records)
            except:  # pylint: disable=W0702
                # In this case we should NOT use logging to log logging error. Only print()
                print("[FATAL] Exception during sending logs")
                traceback.print_exc()
