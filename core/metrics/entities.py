from __future__ import annotations  # FUTURE IMPORT

# ^ Syntax: must be at top of file.
#   Semantics: store type annotations as strings (lazy), avoiding circular-import issues
#   and speeding imports. Lets you reference types before they're defined.

from dataclasses import dataclass  # import the dataclass decorator

# ^ Semantics: @dataclass auto-generates __init__, __repr__, __eq__, etc. for simple "record" classes.

from datetime import date  # import the 'date' type (calendar day)

# ^ Semantics: we'll annotate a field with this, e.g., when the price was recorded.

from typing import List  # generic List type for type hints (List[T])

# ^ Semantics: static typing only; does not affect runtime behavior.


@dataclass(frozen=True)  # declare a dataclass; frozen=True makes instances immutable & hashable
class SeriesPoint:
    when: date  # field 'when' must be a datetime.date (syntax: name: type)
    value: float  # field 'value' must be a float number


Series = List[SeriesPoint]  # type alias: 'Series' means 'List of SeriesPoint'
# ^ Semantics: improves readability of function signatures elsewhere (domain-friendly name).
