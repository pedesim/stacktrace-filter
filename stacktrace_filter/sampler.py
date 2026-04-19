"""Rate-based traceback sampler: keep only a fraction of tracebacks."""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from typing import List, Optional

from stacktrace_filter.parser import Traceback


@dataclass
class SamplerConfig:
    rate: float = 1.0          # fraction to keep, 0.0–1.0
    seed: Optional[int] = None # set for deterministic sampling
    deterministic: bool = False # use fingerprint-based determinism


@dataclass
class SampleResult:
    kept: List[Traceback] = field(default_factory=list)
    dropped: int = 0

    @property
    def total(self) -> int:
        return len(self.kept) + self.dropped

    @property
    def keep_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return len(self.kept) / self.total


def _tb_hash(tb: Traceback) -> float:
    """Deterministic float in [0, 1) derived from traceback content."""
    key = tb.exc_type + tb.exc_message + "".join(
        f.filename + str(f.lineno) for f in tb.frames
    )
    digest = hashlib.md5(key.encode(), usedforsecurity=False).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def sample(
    tracebacks: List[Traceback],
    config: Optional[SamplerConfig] = None,
) -> SampleResult:
    """Return a SampleResult keeping approximately config.rate fraction."""
    if config is None:
        config = SamplerConfig()

    rate = max(0.0, min(1.0, config.rate))
    if rate == 1.0:
        return SampleResult(kept=list(tracebacks), dropped=0)
    if rate == 0.0:
        return SampleResult(kept=[], dropped=len(tracebacks))

    rng = random.Random(config.seed)
    result = SampleResult()

    for tb in tracebacks:
        if config.deterministic:
            value = _tb_hash(tb)
        else:
            value = rng.random()

        if value < rate:
            result.kept.append(tb)
        else:
            result.dropped += 1

    return result


def format_sample_result(result: SampleResult) -> str:
    lines = [
        f"Sampled {result.total} tracebacks:",
        f"  kept:    {len(result.kept)}",
        f"  dropped: {result.dropped}",
        f"  rate:    {result.keep_rate:.2%}",
    ]
    return "\n".join(lines)
