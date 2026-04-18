"""Configuration dataclass for stacktrace-filter output options."""

from dataclasses import dataclass, field


@dataclass
class FilterConfig:
    """Controls how tracebacks are formatted."""

    color: bool = True
    """Emit ANSI colour codes."""

    show_stdlib: bool = False
    """Show stdlib frames rather than collapsing them."""

    show_site_packages: bool = False
    """Show third-party frames rather than collapsing them."""

    collapse_label: str = "  ... {n} frame(s) hidden ..."
    """Template for the collapse summary line; ``{n}`` is replaced by the count."""

    max_source_width: int = 120
    """Truncate source-line display to this many characters."""

    extra_hidden_paths: list[str] = field(default_factory=list)
    """Additional path substrings whose frames should be collapsed."""

    def should_hide(self, filename: str) -> bool:
        """Return True when *filename* matches a user-supplied hidden path."""
        return any(p in filename for p in self.extra_hidden_paths)

    def collapse_message(self, n: int) -> str:
        return self.collapse_label.format(n=n)
