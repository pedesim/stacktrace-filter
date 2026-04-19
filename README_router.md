# Traceback Router

The router module lets you dispatch tracebacks to named destinations based on configurable rules.

## Rules File

Create a JSON file with a `rules` array:

```json
{
  "rules": [
    {"destination": "auth_errors", "exc_type": "PermissionError"},
    {"destination": "db_errors", "filename_contains": "models.py"},
    {"destination": "value_errors", "exc_type": "ValueError", "exc_message": "invalid"}
  ]
}
```

Each rule may specify:
- `destination` (required): name of the target bucket
- `exc_type`: regex matched against the exception type
- `exc_message`: regex matched against the exception message (case-insensitive)
- `filename_contains`: substring matched against any frame filename

Rules are evaluated in order; the first match wins.

## CLI Usage

```bash
# Route from stdin
cat traceback.txt | python -m stacktrace_filter.router_cli rules.json

# Route from file with summary
python -m stacktrace_filter.router_cli rules.json traceback.txt --summary

# Custom default destination
python -m stacktrace_filter.router_cli rules.json --default unmatched
```

## Python API

```python
from stacktrace_filter.router import RouterConfig, RouteRule, route, route_all

config = RouterConfig(
    rules=[RouteRule(destination="db", filename_contains="models.py")],
    default_destination="other",
)

routed = route(traceback, config)
print(routed.destination)
```
