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

""" Emitter """


class EventNodeLogEmitter:  # pylint: disable=R0902
    """ Emit logs via started EventNode """

    def __init__(self, event_node, default_labels=None):
        self.event_node = event_node
        self.default_labels = default_labels if default_labels is not None else {}

    def emit(self, log_line, log_time, additional_labels=None):
        """ Emit log line """
        log_labels = self.default_labels
        if additional_labels is not None:
            log_labels.update(additional_labels)
        #
        data = {
            "records": [{
                "line": log_line,
                "time": log_time,
                "labels": log_labels,
            }],
        }
        #
        self.event_node.emit("log_data", data)

    def emit_batch(self, batch_data):
        """ Emit log lines """
        data = {
            "records": [],
        }
        #
        for item in batch_data:
            log_line = item["line"]
            log_time = item["time"]
            log_labels = self.default_labels
            #
            additional_labels = item.get("labels", None)
            if additional_labels is not None:
                log_labels.update(additional_labels)
            #
            data["records"].append({
                "line": log_line,
                "time": log_time,
                "labels": log_labels,
            })
        #
        self.event_node.emit("log_data", data)
