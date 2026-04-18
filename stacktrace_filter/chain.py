"""Support for chained exceptions (__ cause__ / __context__)."""
from dataclasses import dataclass, field
from typing import List, Optional
from stacktrace_filter.parser import Traceback, parse


CHAINED_CAUSE_HEADER = "The above exception was the direct cause of the following exception:"
CHAINED_CONTEXT_HEADER = "During handling of the above exception, another exception occurred:"


@dataclass
class ChainedTraceback:
    tracebacks: List[Traceback] = field(default_factory=list)
    links: List[str] = field(default_factory=list)  # header between each pair


def split_chained(text: str):
    """Split raw traceback text on chained exception headers.

    Returns a list of (header_or_None, raw_block) tuples.
    """
    import re
    pattern = re.compile(
        r"(?P<header>"
        + re.escape(CHAINED_CAUSE_HEADER)
        + r"|"
        + re.escape(CHAINED_CONTEXT_HEADER)
        + r")"
    )
    parts = pattern.split(text)
    # parts: [block0, header1, block1, header2, block2, ...]
    result = []
    it = iter(parts)
    first = next(it, None)
    if first is not None:
        result.append((None, first.strip()))
    while True:
        header = next(it, None)
        if header is None:
            break
        block = next(it, "").strip()
        result.append((header.strip(), block))
    return result


def parse_chained(text: str) -> ChainedTraceback:
    """Parse a (possibly chained) traceback text into a ChainedTraceback."""
    parts = split_chained(text)
    chain = ChainedTraceback()
    for header, block in parts:
        if header:
            chain.links.append(header)
        if block:
            tb = parse(block)
            chain.tracebacks.append(tb)
    return chain
