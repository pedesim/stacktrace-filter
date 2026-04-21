# stacktrace-filter: inspector

The **inspector** module extracts and reports key facts about a single Python
traceback, giving you a quick overview without reading every frame.

## Python API

```python
from stacktrace_filter.parser import parse
from stacktrace_filter.inspector import inspect, format_inspection

with open("traceback.txt") as fh:
    tb = parse(fh.read())

result = inspect(tb)
print(format_inspection(result, color=True))
```

### `InspectionResult` attributes

| Attribute | Type | Description |
|---|---|---|
| `exc_type` | `str` | Exception class name |
| `exc_message` | `str` | Exception message |
| `total_frames` | `int` | Total number of frames |
| `user_frames` | `int` | Frames from user code |
| `stdlib_frames` | `int` | Frames from the standard library |
| `library_frames` | `int` | Frames from third-party packages |
| `user_ratio` | `float` | Fraction of user frames (0–1) |
| `has_user_code` | `bool` | `True` when at least one user frame exists |
| `deepest_user_frame` | `Frame \| None` | Innermost user frame |
| `unique_files` | `list[str]` | Deduplicated list of filenames |
| `unique_functions` | `list[str]` | Deduplicated list of function names |

## CLI

```
usage: python -m stacktrace_filter.inspector_cli [-h] [--no-color] [--json] [file]
```

### Examples

```bash
# Inspect from stdin
python -m stacktrace_filter.inspector_cli < traceback.txt

# Inspect a file, no colour
python -m stacktrace_filter.inspector_cli traceback.txt --no-color

# Machine-readable JSON output
python -m stacktrace_filter.inspector_cli traceback.txt --json
```

### JSON output shape

```json
{
  "exc_type": "ZeroDivisionError",
  "exc_message": "division by zero",
  "total_frames": 2,
  "user_frames": 2,
  "stdlib_frames": 0,
  "library_frames": 0,
  "user_ratio": 1.0,
  "deepest_user_frame": {
    "filename": "/home/user/utils.py",
    "lineno": 5,
    "function": "compute"
  },
  "unique_files": ["/home/user/app.py", "/home/user/utils.py"],
  "unique_functions": ["run", "compute"]
}
```
