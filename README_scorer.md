# stacktrace-scorer

Score and rank Python tracebacks by relevance.

## Overview

`stacktrace-scorer` analyses one or more tracebacks and assigns each a
numerical relevance score based on three signals:

| Signal | Description | Default weight |
|--------|-------------|----------------|
| `user_ratio` | Fraction of frames that belong to user code (not stdlib/site-packages) | 0.5 |
| `depth` | Normalised stack depth (deeper = potentially more interesting) | 0.3 |
| `exc_type` | Exception type severity (e.g. `MemoryError` → 1.0, warnings → 0.2) | 0.2 |

The final score is a weighted sum in the range `[0, 1]`.

## Usage

```bash
# From stdin
cat traceback.txt | stacktrace-scorer

# From a file
stacktrace-scorer traceback.txt

# Show only top 5 results
stacktrace-scorer --top 5 traceback.txt

# Disable colour output
stacktrace-scorer --no-color traceback.txt

# Tune weights
stacktrace-scorer --weight-user 0.7 --weight-depth 0.2 --weight-exc 0.1 traceback.txt
```

## Output

```
[1] score=0.7250  ValueError: oops
     user=1.00  depth=0.04  exc=0.50
```

## Python API

```python
from stacktrace_filter.parser import parse
from stacktrace_filter.scorer import score_traceback, score_all, format_scored

tb = parse(open("traceback.txt").read())
scored = score_traceback(tb)
print(scored.score, scored.breakdown)
```
