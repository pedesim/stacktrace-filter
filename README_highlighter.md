# stacktrace-highlight

A CLI tool that applies ANSI syntax highlighting to raw Python traceback text.

## Usage

```
stacktrace-highlight [file] [--no-color] [--exception-only]
```

### Arguments

| Argument | Description |
|---|---|
| `file` | Path to a traceback file. Reads from **stdin** if omitted. |
| `--no-color` | Disable ANSI colour output. |
| `--exception-only` | Only highlight the final exception line; pass all other lines through unchanged. |

## Examples

### Highlight a traceback from a file

```bash
stacktrace-highlight traceback.txt
```

### Pipe from another command

```bash
python myapp.py 2>&1 | stacktrace-highlight
```

### Disable colours (e.g. for log files)

```bash
stacktrace-highlight traceback.txt --no-color
```

### Only highlight the exception line

```bash
stacktrace-highlight traceback.txt --exception-only
```

## Highlighting rules

- Lines starting with `  File ` are treated as **frame lines** and highlighted
  using `highlight_line` (keywords, numbers, strings, comments).
- Lines that look like an exception (`ExcType: message`) are highlighted using
  `highlight_exception_line` (bold red exception type).
- All other lines (e.g. `Traceback (most recent call last):`, source snippets)
  are passed through unchanged.

## Integration

`stacktrace-highlight` uses the same `highlight_line` and
`highlight_exception_line` functions as the main `stacktrace-filter` formatter,
so the colour scheme is consistent across the whole toolchain.
