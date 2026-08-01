from collections.abc import Iterable, Iterator, Sequence


def round_robin(sources: Sequence[Iterable]) -> Iterator:
    """Yield one item from each source in turn until all are exhausted."""
    active = [iter(source) for source in sources]
    while active:
        remaining = []
        for source in active:
            try:
                yield next(source)
                remaining.append(source)
            except StopIteration:
                pass
        active = remaining
