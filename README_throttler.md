# stacktrace-filter: throttler

The **throttler** module suppresses repeated tracebacks that exceed a configurable rate limit, helping reduce noise in high-volume log streams.

## Concepts

- **Window**: a rolling time window (seconds) within which occurrences are counted.
- **Max**: maximum allowed occurrences of the same traceback fingerprint within the window.
- Tracebacks are identified by their `Fingerprint.full` hash (see `fingerprint.py`).

## Python API

```python
from stacktrace_filter.throttler import Throttler, ThrottlerConfig

cfg = ThrottlerConfig(max_per_window=5, window_seconds=30.0)
t = Throttler(cfg)

for tb in stream:
    result = t.check(tb)
    if result.allowed:
        print(format_traceback(tb))
```

### `throttle()` convenience function

```python
from stacktrace_filter.throttler import throttle
kept = throttle(list_of_tracebacks, config)
```

## CLI

```
usage: stf-throttle [-h] [--max N] [--window SECS] [--format {plain,json}] [--no-color] [file]
```

### Examples

```bash
# Keep at most 3 occurrences of each unique traceback per 60 s
cat app.log | stf-throttle --max 3 --window 60

# Output as JSON
stf-throttle --max 1 --format json app.log
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--max N` | `10` | Max occurrences per window |
| `--window SECS` | `60.0` | Window size in seconds |
| `--format` | `plain` | Output format (`plain` or `json`) |
| `--no-color` | off | Disable ANSI color |
