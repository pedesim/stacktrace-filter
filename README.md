# stacktrace-filter

A CLI tool to collapse and highlight relevant lines in Python tracebacks.

---

## Installation

```bash
pip install stacktrace-filter
```

Or install from source:

```bash
git clone https://github.com/yourname/stacktrace-filter.git
cd stacktrace-filter
pip install .
```

---

## Usage

Pipe any Python traceback output directly into `stacktrace-filter`:

```bash
python my_script.py 2>&1 | stacktrace-filter
```

Or filter a saved traceback file:

```bash
stacktrace-filter traceback.log
```

**Example output:**

```
Traceback (most recent call last):
  ... (5 lines collapsed)
  File "my_script.py", line 42, in process_data   ◄ relevant
    result = parse(value)
  File "my_script.py", line 17, in parse           ◄ relevant
    raise ValueError(f"Invalid value: {value}")
ValueError: Invalid value: None
```

Lines from third-party libraries and the standard library are collapsed by default, keeping the focus on your own code.

### Options

| Flag | Description |
|------|-------------|
| `--show-all` | Disable collapsing, show full traceback |
| `--no-color` | Disable colored output |
| `--project-root PATH` | Set the root path of your project (default: current directory) |

---

## License

MIT © 2024 yourname