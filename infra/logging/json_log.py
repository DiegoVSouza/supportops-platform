"""One JSON object per log line, for the uvicorn services."""

import json
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record):
        entry = {
            'time': datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        if record.exc_info:
            entry['exception'] = record.exc_info[0].__name__
        return json.dumps(entry, ensure_ascii=False)
