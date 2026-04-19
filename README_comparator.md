# stacktrace-compare

Compare two Python tracebacks and produce a similarity score.

## Usage

```
stacktrace-compare LEFT RIGHT [--no-color] [--score-only]
```

### Arguments

| Argument | Description |
|---|---|
| `LEFT` | Path to first traceback file (or `-` for stdin) |
| `RIGHT` | Path to second traceback file |
| `--no-color` | Disable ANSI colour output |
| `--score-only` | Print only the numeric overall score (0.0 – 1.0) |

## Scoring

The overall score is computed as:

```
score = frame_similarity * 0.6
      + exc_type_match   * 0.3
      + exc_msg_match    * 0.1
```

`frame_similarity` is the Jaccard index of the frame sets (keyed by
`filename:lineno:function`).

## Example

```
$ stacktrace-compare tb1.txt tb2.txt
exc_type match : ✔
exc_msg  match : ✘
frame similarity: 66.67%
overall score   : 0.7000
```

## Python API

```python
from stacktrace_filter.parser import parse
from stacktrace_filter.comparator import compare, format_comparison

left  = parse(open("tb1.txt").read())
right = parse(open("tb2.txt").read())
result = compare(left, right)
print(result.overall_score)
print(format_comparison(result))
```
