# Timeline Feature

The **timeline** module lets you attach timestamps to multiple tracebacks and render them in chronological order.

## Usage

### Python API

```python
from datetime import datetime
from stacktrace_filter.parser import parse
from stacktrace_filter.timeline import build_timeline, format_timeline

tb1 = parse(open("tb1.txt").read())
tb2 = parse(open("tb2.txt").read())

tl = build_timeline(
    [tb1, tb2],
    [datetime(2024, 6, 1, 10, 0), datetime(2024, 6, 1, 9, 30)],
    labels=["worker-a", "worker-b"],
)
print(format_timeline(tl))
```

### CLI

Prepare a JSON manifest:

```json
[
  {"text": "Traceback ...\nValueError: x", "timestamp": "2024-06-01T10:00:00", "label": "job-1"},
  {"text": "Traceback ...\nRuntimeError: y", "timestamp": "2024-06-01T09:30:00"}
]
```

Then run:

```bash
stacktrace-timeline manifest.json
# or pipe from stdin
cat manifest.json | stacktrace-timeline
# disable colors
stacktrace-timeline --no-color manifest.json
# sort in descending (newest-first) order
stacktrace-timeline --reverse manifest.json
```

## Output

Entries are printed in ascending timestamp order (oldest first) by default:

```
2024-06-01 09:30:00  RuntimeError: y
2024-06-01 10:00:00 [job-1]  ValueError: x
```

Use `--reverse` to print newest entries first:

```
2024-06-01 10:00:00 [job-1]  ValueError: x
2024-06-01 09:30:00  RuntimeError: y
```

## Manifest Fields

| Field | Required | Description |
|-------|----------|-------------|
| `text` | yes | Raw traceback text to parse |
| `timestamp` | yes | ISO 8601 datetime string |
| `label` | no | Optional source label shown in brackets |
