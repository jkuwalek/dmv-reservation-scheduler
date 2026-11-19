"""Strips anything shaped like an access code out of log output.

Attached once to the root logger rather than relied on at every call site, because
the one place someone forgets is the place it matters.
"""

import logging
import re

CODE_PATTERN = re.compile(r"\b[A-Za-z0-9]{3}(?:-[A-Za-z0-9]{3}){3}\b")
REPLACEMENT = "[redacted]"


class RedactAccessCodes(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = CODE_PATTERN.sub(REPLACEMENT, str(record.msg))
        if record.args:
            record.args = tuple(
                CODE_PATTERN.sub(REPLACEMENT, str(arg)) for arg in _as_tuple(record.args)
            )
        return True


def _as_tuple(args: object) -> tuple[object, ...]:
    return args if isinstance(args, tuple) else (args,)
