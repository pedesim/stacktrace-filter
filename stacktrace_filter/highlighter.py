"""Syntax highlighting for source code lines in tracebacks."""
from __future__ import annotations

import re
from typing import Optional

# ANSI color codes
_RESET = "\033[0m"
_BOLD = "\033[1m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"
_MAGENTA = "\033[35m"

_KEYWORD_RE = re.compile(
    r"\b(if|else|elif|for|while|return|def|class|import|from|as|with|try|except|raise|pass|in|not|and|or|is|None|True|False)\b"
)
_STRING_RE = re.compile(r'(\"\"\".*?\"\"\"|\'\'\'.+?\'\'\'|\"[^\"]*\"|\' [^\']*\')', re.DOTALL)
_NUMBER_RE = re.compile(r"\b(\d+\.?\d*)\b")
_COMMENT_RE = re.compile(r"(#.*)$", re.MULTILINE)
_FUNC_RE = re.compile(r"\b([a-zA-Z_][\w]*)(?=\()")


def highlight_line(line: str, color: bool = True) -> str:
    """Apply basic syntax highlighting to a single Python source line."""
    if not color:
        return line

    result = line

    # Comments
    result = _COMMENT_RE.sub(lambda m: _CYAN + m.group(1) + _RESET, result)

    # Strings (simple, non-overlapping)
    result = _STRING_RE.sub(lambda m: _GREEN + m.group(0) + _RESET, result)

    # Keywords
    result = _KEYWORD_RE.sub(lambda m: _BOLD + _YELLOW + m.group(0) + _RESET, result)

    # Numbers
    result = _NUMBER_RE.sub(lambda m: _MAGENTA + m.group(0) + _RESET, result)

    # Function calls
    result = _FUNC_RE.sub(lambda m: _CYAN + m.group(0) + _RESET, result)

    return result


def highlight_exception_line(text: str, color: bool = True) -> str:
    """Highlight the final exception line (e.g. 'ValueError: bad input')."""
    if not color:
        return text
    match = re.match(r"^([\w.]+Error|[\w.]+Exception|[\w.]+Warning)(:.*)$", text)
    if match:
        return _BOLD + _RED + match.group(1) + _RESET + match.group(2)
    return _BOLD + _RED + text + _RESET
