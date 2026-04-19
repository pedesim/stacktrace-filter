# Traceback Matcher

The **matcher** module lets you define named pattern rules and test tracebacks against them.

## MatchRule fields

| Field | Type | Description |
|---|---|---|
| `name` | str | Rule identifier |
| `exc_type_pattern` | str \| None | Regex matched against exception type |
| `exc_message_pattern` | str \| None | Regex matched against exception message |
| `filename_pattern` | str \| None | Regex matched against any frame filename |
| `min_depth` | int \| None | Minimum number of frames required |

## Python API

```python
from stacktrace_filter.matcher import MatchRule, apply_rules, filter_tracebacks

rules = [
    MatchRule(name="db_error", exc_type_pattern="OperationalError", filename_pattern=r"db/"),
    MatchRule(name="deep_error", min_depth=10),
]

result = apply_rules(tb, rules)
if result.matched:
    print("Matched:", result.matched_rules)
```

## CLI

```
stacktrace-matcher [file] --rules rules.json [--only-matched]
```

### rules.json format

```json
[
  {
    "name": "db_error",
    "exc_type_pattern": "OperationalError",
    "filename_pattern": "db/"
  }
]
```

### Options

- `file` — path to traceback file; omit to read from stdin
- `--rules` — path to JSON rules file (required)
- `--only-matched` — suppress output when no rules match
