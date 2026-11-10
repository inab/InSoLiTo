"""DSL1 pipelines: processes linked by channel names (`into` -> top-level aliases -> `from`)."""

import re
from pathlib import Path

from .graph import Graph
from .groovy import IDENT, KEYWORDS, flat_statement_spans
from .sources import Pipeline, Source

Channel = tuple[Path, str, int]  # (file, channel name, version)


class _Channels:
    """Channel names are reused (`.into { ch_reads; ch_other }` after reading ch_reads), so every
    assignment makes a new version of the name, and a reference means the latest version before it."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.version: dict[str, int] = {}

    def current(self, name: str) -> Channel:
        return self.path, name, self.version.get(name, 0)

    def define(self, name: str) -> Channel:
        self.version[name] = self.version.get(name, 0) + 1
        return self.current(name)


def _top_level(source: Source) -> str:
    """The code of source outside process and workflow blocks (blocks blanked, positions kept)."""
    top = list(source.code)
    for a, b in source.blocks:
        top[a:b] = [c if c == "\n" else " " for c in top[a:b]]
    return "".join(top)


def _statement_targets(item: str) -> list[str]:
    """Channel names a top-level statement assigns: `.set { x }`, `.into { a; b }`, `x = ...`."""
    targets = re.findall(r"\.set\s*\{\s*(\w+)\s*\}", item)
    for group in re.findall(r"\.into\s*[{(]([^})]*)[})]", item):
        targets += re.findall(r"\w+", group)
    m = re.match(r"(?:def\s+)?(\w+)\s*=(?!=)", item)
    if m:
        targets.append(m.group(1))
    return targets


def dsl1_graph(pipe: Pipeline, graph: Graph) -> None:
    """Add the processes of all DSL1 files and the edges between them to graph."""
    links: dict[Channel, set[Channel]] = {}
    consumers: dict[Channel, set[str]] = {}
    outputs: list[tuple[str, Channel]] = []
    for source in pipe.sources.values():
        infos = {name: pipe.process_info(source, name) for name in source.processes}
        if not any(i.into or i.takes_from for i in infos.values()):
            continue
        top = _top_level(source)
        events = [(source.processes[name][0], "process", name) for name in infos]
        events += [(a, "statement", top[a:b].strip()) for a, b in flat_statement_spans(top)]
        channels = _Channels(source.path)
        for _, kind, item in sorted(events):
            if kind == "process":
                graph.add_node(item, source, item)
                for ch in infos[item].takes_from:
                    consumers.setdefault(channels.current(ch), set()).add(item)
                outputs += [(item, channels.define(ch)) for ch in infos[item].into]
                continue
            targets = _statement_targets(item)
            sources = [channels.current(s) for s in set(IDENT.findall(item)) - set(targets) - KEYWORDS]
            # `ch = ch.map{}` reads the old version of ch
            sources += [channels.current(t) for t in targets if re.search(rf"(?<![\w.]){t}\s*\.", item)]
            for target in [channels.define(t) for t in targets]:
                for src in sources:
                    links.setdefault(src, set()).add(target)
    for producer, channel in outputs:
        seen, todo = {channel}, [channel]
        while todo:
            current = todo.pop()
            for consumer in consumers.get(current, ()):
                if graph.connect([(producer, channel[1])], consumer):
                    pipe.warn(f"left out {producer} -> {consumer}: it would close a cycle (channel name reused)")
            for nxt in links.get(current, ()):
                if nxt not in seen:
                    seen.add(nxt)
                    todo.append(nxt)
