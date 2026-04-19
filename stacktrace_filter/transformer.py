"""Transform tracebacks by applying a sequence of mutation functions."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, List, Optional
from stacktrace_filter.parser import Traceback, Frame

TransformFn = Callable[[Traceback], Traceback]


@dataclass
class TransformPipeline:
    steps: List[TransformFn] = field(default_factory=list)

    def add(self, fn: TransformFn) -> "TransformPipeline":
        self.steps.append(fn)
        return self

    def run(self, tb: Traceback) -> Traceback:
        for step in self.steps:
            tb = step(tb)
        return tb


@dataclass
class TransformResult:
    original: Traceback
    transformed: Traceback
    steps_applied: int

    @property
    def frame_delta(self) -> int:
        return len(self.transformed.frames) - len(self.original.frames)


def drop_frames(predicate: Callable[[Frame], bool]) -> TransformFn:
    """Return a transform that removes frames matching *predicate*."""
    def _transform(tb: Traceback) -> Traceback:
        kept = [f for f in tb.frames if not predicate(f)]
        return Traceback(frames=kept, exception=tb.exception)
    return _transform


def limit_frames(max_frames: int, keep: str = "last") -> TransformFn:
    """Return a transform that caps the frame list to *max_frames*."""
    def _transform(tb: Traceback) -> Traceback:
        frames = tb.frames
        if len(frames) > max_frames:
            frames = frames[-max_frames:] if keep == "last" else frames[:max_frames]
        return Traceback(frames=frames, exception=tb.exception)
    return _transform


def relabel_frames(mapping: dict) -> TransformFn:
    """Return a transform that rewrites filenames according to *mapping*."""
    def _transform(tb: Traceback) -> Traceback:
        new_frames = []
        for f in tb.frames:
            filename = mapping.get(f.filename, f.filename)
            new_frames.append(Frame(filename=filename, lineno=f.lineno,
                                    function=f.function, source=f.source))
        return Traceback(frames=new_frames, exception=tb.exception)
    return _transform


def transform(tb: Traceback, pipeline: TransformPipeline) -> TransformResult:
    result = pipeline.run(tb)
    return TransformResult(
        original=tb,
        transformed=result,
        steps_applied=len(pipeline.steps),
    )
