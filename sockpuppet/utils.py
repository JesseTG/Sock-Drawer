# -*- coding: utf-8 -*-
"""Helper utilities and decorators."""

from collections import defaultdict, namedtuple
from typing import Dict, List, Sequence, Tuple

from flask import flash


def flash_errors(form, category='warning'):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            flash('{0} - {1}'.format(getattr(form, field).label.text, error), category)


NOT_BOT = 0
BOT = 1
