# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""

from collections import defaultdict, namedtuple
from typing import Dict, List, Sequence, Tuple

NOT_BOT = 0
BOT = 1
MAX_JSON_INT = (2**53) - 1
MIN_JSON_INT = -MAX_JSON_INT
