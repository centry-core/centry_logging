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

""" Logging tool """

import logging
import inspect
import importlib

from logging import shutdown  # pylint: disable=W0611

from .formatters.secret import SecretFormatter
from .handlers.local import ThreadLocalHandler
from .internal import state
from .tools import patches


#
# Base helpers
#

def get_logger():
    """ Get logger for caller context """
    return logging.getLogger(
        inspect.currentframe().f_back.f_globals["__name__"]
    )


def get_outer_logger():
    """ Get logger for callers context (for use in this module) """
    return logging.getLogger(
        inspect.currentframe().f_back.f_back.f_globals["__name__"]
    )


def prepare_handler(handler):
    """ Prepare logging handler object """
    if state.formatter is not None:
        handler.setFormatter(state.formatter)
    #
    for filter_obj in state.filters:
        handler.addFilter(filter_obj)

#
# Log methods
#

def debug(msg, *args, **kwargs):
    """ Logs a message with level DEBUG """
    return get_outer_logger().debug(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    """ Logs a message with level INFO """
    return get_outer_logger().info(msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    """ Logs a message with level WARNING """
    return get_outer_logger().warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    """ Logs a message with level ERROR """
    return get_outer_logger().error(msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    """ Logs a message with level CRITICAL """
    return get_outer_logger().critical(msg, *args, **kwargs)


def log(lvl, msg, *args, **kwargs):
    """ Logs a message with integer level lvl """
    return get_outer_logger().log(lvl, msg, *args, **kwargs)


def exception(msg, *args, **kwargs):
    """ Logs a message with level ERROR inside exception handler """
    return get_outer_logger().exception(msg, *args, **kwargs)

#
# Init
#

def init(level=logging.INFO, *, config=None, force=False):  # pylint: disable=R0912,R0914
    """ Initialize logging """
    with state.lock:
        if state.initialized and not force:
            return
        #
        state.root_level = level
        state.filters.clear()
        state.handlers.clear()
        #
        # Prepare handlers according to config
        #
        if config is None or not isinstance(config, dict):
            state.formatter = SecretFormatter()
            #
            handler = logging.StreamHandler()
            #
            prepare_handler(handler)
            #
            state.handlers.append(handler)
        else:
            state.root_level = config.get("level", state.root_level)
            #
            if "formatter" in config:
                opts = config.get("formatter").copy()
                #
                formatter_pkg, formatter_name = opts.pop("type").rsplit(".", 1)
                formatter_cls = getattr(
                    importlib.import_module(formatter_pkg),
                    formatter_name
                )
                #
                state.formatter = formatter_cls(**opts)
            else:
                state.formatter = SecretFormatter()
            #
            for filter_cfg in config.get("filters", []):
                opts = filter_cfg.copy()
                #
                filter_pkg, filter_name = opts.pop("type").rsplit(".", 1)
                filter_cls = getattr(
                    importlib.import_module(filter_pkg),
                    filter_name
                )
                #
                filter_obj = filter_cls(**opts)
                state.filters.append(filter_obj)
            #
            if "handlers" not in config:
                handler = logging.StreamHandler()
                #
                prepare_handler(handler)
                #
                state.handlers.append(handler)
            #
            for handler_cfg in config.get("handlers", []):
                opts = handler_cfg.copy()
                #
                handler_pkg, handler_name = opts.pop("type").rsplit(".", 1)
                handler_cls = getattr(
                    importlib.import_module(handler_pkg),
                    handler_name
                )
                #
                handler = handler_cls(**opts)
                #
                prepare_handler(handler)
                #
                state.handlers.append(handler)
        #
        # Add local handler
        #
        local_handler = ThreadLocalHandler()
        #
        prepare_handler(local_handler)
        #
        state.handlers.append(local_handler)
        #
        # Remove existing handlers
        #
        for handler in list(logging.root.handlers):
            if state.formatter is not None and isinstance(state.formatter, SecretFormatter):
                state.formatter.update_secrets(handler)
            #
            logging.root.removeHandler(handler)
            handler.close()
        #
        # Apply new handlers
        #
        for handler in state.handlers:
            logging.root.addHandler(handler)
        #
        logging.root.setLevel(state.root_level)
        logging.raiseExceptions = False
        patches.apply()
        #
        state.initialized = True

#
# Additional methods
#

def update_secrets(secrets):
    """ Update formatter secrets """
    with state.lock:
        if state.formatter is not None and isinstance(state.formatter, SecretFormatter):
            state.formatter.update_secrets(secrets)

def flush():
    """ Flush handlers """
    for handler in list(logging.root.handlers):
        handler.flush()
