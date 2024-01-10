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

import json
import gzip
import time

import requests  # pylint: disable=E0401


class CarrierLokiLogEmitter:  # pylint: disable=R0902
    """ Emit logs to Loki """

    def __init__(  # pylint: disable=R0913
            self, loki_push_url,
            loki_user=None, loki_password=None, loki_token=None,
            default_labels=None,
            verify=True, retries=3, retry_delay=0.5, timeout=15,
            use_gzip=False,
        ):
        self.loki_push_url = loki_push_url
        self.loki_user = loki_user
        self.loki_password = loki_password
        self.loki_token = loki_token
        #
        self.default_labels = default_labels if default_labels is not None else {}
        #
        self.verify = verify
        self.retries = retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        #
        self.use_gzip = use_gzip
        #
        self._connection = None

    def connect(self):
        """ Get connection object """
        if self._connection is not None:
            return self._connection
        #
        self._connection = requests.Session()
        #
        if self.loki_user is not None and self.loki_password is not None:
            self._connection.auth = (self.loki_user, self.loki_password)
        if self.loki_token is not None:
            self._connection.headers.update({
                "Authorization": f"Bearer {self.loki_token}",
            })
        #
        self._connection.headers.update({
            "Content-Type": "application/json",
        })
        #
        if self.use_gzip:
            self._connection.headers.update({
                "Content-Encoding": "gzip",
            })
        #
        return self._connection

    def disconnect(self):
        """ Destroy connection object """
        if self._connection is not None:
            try:
                self._connection.close()
            except:  # pylint: disable=W0702
                pass
            self._connection = None

    def post_data(self, data):
        """ Do a POST to Loki """
        for _ in range(self.retries):
            try:
                connection = self.connect()
                #
                payload = json.dumps(data)
                if self.use_gzip:
                    payload = gzip.compress(payload.encode("utf-8"))
                #
                response = connection.post(
                    self.loki_push_url, data=payload, verify=self.verify, timeout=self.timeout,
                )
                response.raise_for_status()
                return response
            except:  # pylint: disable=W0702
                self.disconnect()
                time.sleep(self.retry_delay)
        #
        raise RuntimeError("Retries exceeded")

    def emit_line(self, unix_epoch_in_nanoseconds, log_line, additional_labels=None):
        """ Emit log line """
        labels = self.default_labels
        if additional_labels is not None:
            labels.update(additional_labels)
        #
        data = {
            "streams": [
                {
                    "stream": labels,
                    "values": [
                        [f"{unix_epoch_in_nanoseconds}", log_line],
                    ]
                }
            ]
        }
        #
        self.post_data(data)

    def emit_batch(self, batch_data, additional_labels=None):
        """ Emit log line """
        labels = self.default_labels
        if additional_labels is not None:
            labels.update(additional_labels)
        #
        data = {
            "streams": [
                {
                    "stream": labels,
                    "values": batch_data,
                }
            ]
        }
        #
        self.post_data(data)
        #
        # TODO: batches with different stream labels (a.k.a. multiple streams support)
