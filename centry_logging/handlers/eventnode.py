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
import importlib

from ..emitters.eventnode import EventNodeLogEmitter
from ..tools.flush import PeriodicFlush


def make_event_node(settings):
    """ Make EventNode instance """
    node_params = settings.copy()
    #
    node_type = node_params.pop("type")
    node_kwargs = node_params
    #
    node_cls = getattr(importlib.import_module("arbiter.eventnode"), node_type)
    node_obj = node_cls(**node_kwargs)
    #
    return node_obj


class EventNodeLogHandler(logging.Handler):
    """ Log handler - send logs to storage """

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        #
        self.event_node = make_event_node(settings.get("event_node"))
        self.event_node.start()
        #
        self.emitter = EventNodeLogEmitter(
            event_node=self.event_node,
            default_labels=self.settings.get("labels", {}),
        )

    def close(self):
        """ Clean-up resources """
        self.event_node.stop()
        super().close()

    def emit(self, record):
        try:
            log_line = self.format(record)
            log_time = record.created
            #
            additional_labels = {}
            if self.settings.get("include_level_name", True):
                additional_labels["level"] = record.levelname
            if self.settings.get("include_logger_name", True):
                additional_labels["logger"] = record.name
            #
            self.emitter.emit(log_line, log_time, additional_labels)
        except:  # pylint: disable=W0702
            # In this case we should NOT use logging to log logging error. Only print()
            print("[FATAL] Exception during sending logs")
            traceback.print_exc()


class EventNodeBufferedLogHandler(logging.handlers.BufferingHandler):
    """ Log handler - buffer and send logs to storage """

    def __init__(self, settings):
        super().__init__(settings.get("buffer_capacity", 100))
        self.settings = settings
        #
        self.event_node = make_event_node(settings.get("event_node"))
        self.event_node.start()
        #
        self.emitter = EventNodeLogEmitter(
            event_node=self.event_node,
            default_labels=self.settings.get("labels", {}),
        )
        #
        self.last_flush = 0.0
        self.flush_locked = self.settings.get("flush_locked", True)
        PeriodicFlush(self, self.settings.get("buffer_flush_deadline", 30)).start()

    def close(self):
        """ Clean-up resources """
        self.event_node.stop()
        super().close()

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
                #
                log_line = self.format(record)
                log_time = record.created
                #
                additional_labels = {}
                if self.settings.get("include_level_name", True):
                    additional_labels["level"] = record.levelname
                if self.settings.get("include_logger_name", True):
                    additional_labels["logger"] = record.name
                #
                log_records.append({
                    "line": log_line,
                    "time": log_time,
                    "labels": additional_labels,
                })
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
