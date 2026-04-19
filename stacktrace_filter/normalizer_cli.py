"""CLI entry point for the normalizer."""
from __future__ import annotations

import argparse
import json
import sys

from .io_utils import read_source
from .parser import parse
from .normalizer import normalize


def build_normalizer_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog='stf-normalize',
        description='Normalize a Python traceback for comparison or storage.',
    )
    p.add_argument('file', nargs='?', help='Input file (default: stdin)')
    p.add_argument(
        '--format',
        choices=['json', 'text'],
        default='json',
        help='Output format (default: json)',
    )
    return p


def _render_text(ntb) -> str:
    lines = []
    lines.append('Traceback (most recent call last):')
    for f in ntb.frames:
        lines.append(f'  File "{f.filename}", line {f.lineno}, in {f.name}')
        if f.line:
            lines.append(f'    {f.line}')
    lines.append(f'{ntb.exc_type}: {ntb.exc_message}')
    return '\n'.join(lines)


def _render_json(ntb) -> str:
    data = {
        'exc_type': ntb.exc_type,
        'exc_message': ntb.exc_message,
        'frames': [
            {'filename': f.filename, 'lineno': f.lineno, 'name': f.name, 'line': f.line}
            for f in ntb.frames
        ],
    }
    return json.dumps(data, indent=2)


def main(argv=None) -> None:
    parser = build_normalizer_parser()
    args = parser.parse_args(argv)

    try:
        text = read_source(args.file)
    except FileNotFoundError as exc:
        print(f'error: {exc}', file=sys.stderr)
        sys.exit(1)

    tb = parse(text)
    ntb = normalize(tb)

    if args.format == 'json':
        print(_render_json(ntb))
    else:
        print(_render_text(ntb))
