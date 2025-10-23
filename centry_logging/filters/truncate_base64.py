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

"""
Base64 content sanitization filter for logging.
Truncates long base64-encoded data in log messages to keep logs readable.

Messages logged at levels below DEBUG (e.g., custom TRACE level) will show
full base64 content without truncation, while DEBUG and above are sanitized.
"""

import re
import logging


class Base64SanitizationFilter(logging.Filter):
    """
    Logging filter that truncates base64-encoded content in log messages.

    This filter detects data URIs containing base64-encoded content
    (commonly used for embedded images) and replaces long base64 strings
    with truncated versions to prevent log flooding while maintaining
    readability.

    Messages logged at levels below DEBUG (e.g., a custom TRACE level)
    will NOT be sanitized, allowing full base64 visibility for deep
    debugging scenarios.

    Example:
        data:image/png;base64,iVBORw0KGgoAAAANSUhEUg... (very long)

        Becomes:
        data:image/png;base64,iVBORw0KGgoAAAANSU...[base64 truncated]

    Usage in log configuration:
        {
            "filters": [
                {
                    "type": "centry_logging.filters.truncate_base64."
                            "Base64SanitizationFilter",
                    "settings": {
                        "max_base64_chars": 20
                    }
                }
            ]
        }
    """

    def __init__(self, max_base64_chars=20, name=''):
        """
        Initialize the Base64 sanitization filter.

        Args:
            max_base64_chars: Maximum number of base64 characters to
                show before truncation (default: 20)
            name: Filter name (optional, for logging.Filter compatibility)
        """
        super().__init__(name=name)
        self.max_base64_chars = max_base64_chars
        # Pre-compile regex pattern for better performance
        # Matches: data:image/<type>;base64,<base64-data>
        # Only matches base64 strings longer than 20 characters
        self.base64_pattern = re.compile(
            r'data:image/[^;]+;base64,[A-Za-z0-9+/]{20,}[=]*'
        )

    def _sanitize_base64_url(self, url):
        """
        Sanitize a single base64 data URL by truncating the base64 portion.

        Args:
            url: Data URL string containing base64 content

        Returns:
            str: URL with base64 data truncated if exceeds max_base64_chars
        """
        if ';base64,' in url:
            prefix, base64_data = url.split(';base64,', 1)
            if len(base64_data) > self.max_base64_chars:
                truncated = base64_data[:self.max_base64_chars]
                truncated_data = truncated + "...[base64 truncated]"
                return f"{prefix};base64,{truncated_data}"
        return url

    def filter(self, record):
        """
        Filter method called for each log record.
        Sanitizes base64 content in log messages.

        Messages with levelno < DEBUG (e.g., custom TRACE level) are NOT
        sanitized, allowing full base64 visibility for deep debugging.

        Args:
            record: LogRecord instance

        Returns:
            bool: Always True (we modify but don't filter out records)
        """
        try:
            # Skip sanitization for messages below DEBUG level
            # (e.g., custom TRACE level for deep debugging)
            if record.levelno < logging.DEBUG:
                return True

            # Only process string messages
            # (f-strings, formatted strings, direct strings)
            # We don't try to serialize objects - that's the
            # responsibility of the caller
            if hasattr(record, 'msg') and isinstance(record.msg, str):
                # Use regex substitution to replace all base64 data URLs
                record.msg = self.base64_pattern.sub(
                    lambda match: self._sanitize_base64_url(
                        match.group(0)
                    ),
                    record.msg
                )
        except Exception:
            # If anything goes wrong, don't break logging - just pass
            # through unchanged. This ensures logging continues to work
            # even if sanitization fails
            pass

        return True
