"""DSL2 pipelines: evaluate workflow bodies, every expression becomes the producers it carries."""

import re
from dataclasses import dataclass, field
from typing import Final

from .graph import Graph, Producers
from .groovy import CONTROL, IDENT, brace_blocks, close_of, section_text, sections, split_top, statements
from .sources import Pipeline, Source

MAX_DEPTH: Final = 20  # subworkflow nesting, beyond this it is probably a loop
WORKFLOW_LABELS: Final = ["take", "main", "emit", "publish"]
OUT_REFERENCE: Final = re.compile(r"\s*\.\s*out\b(?:\s*\.\s*(\w+)|\s*\[\s*(\d+)\s*\])?")


@dataclass(slots=True)
class Outputs:
    """The outputs of a called process or workflow: all of them, by emit name, and the emit order."""

    all: Producers = field(default_factory=set)
    by_emit: dict[str, Producers] = field(default_factory=dict)
    order: list[str] = field(default_factory=list)  # for .out[i]

    def merge(self, other: "Outputs") -> None:
        """Called again (e.g. in another if/else branch): keep both."""
        self.all |= other.all
        for emit, producers in other.by_emit.items():
            self.by_emit[emit] = self.by_emit.get(emit, set()) | producers

    def get(self, emit: str | None, index: str | None) -> Producers:
        """The producers of `.out`, `.out.name` or `.out[i]`."""
        if index is not None and int(index) < len(self.order):
            emit = self.order[int(index)]
        return self.by_emit.get(emit, self.all) if emit else self.all


@dataclass(slots=True)
class Scope:
    """The state while evaluating one inlined workflow body."""

    source: Source
    prefix: str  # node name prefix, e.g. `MAIN:SUB:`
    depth: int
    env: dict[str, Producers] = field(default_factory=dict)  # variables -> producers
    outs: dict[str, Outputs] = field(default_factory=dict)  # called names -> their outputs


class Dsl2:
    """Evaluate DSL2 workflow bodies: every expression becomes the set of (producer node, channel) it carries."""

    def __init__(self, pipe: Pipeline, graph: Graph) -> None:
        self.pipe, self.graph = pipe, graph

    def run_workflow(
        self, source: Source, name: str | None, prefix: str, inputs: list[Producers], depth: int = 0
    ) -> Outputs:
        """Inline a workflow; return its emits."""
        if depth > MAX_DEPTH:
            self.pipe.warn(f"workflow nesting too deep at {prefix}")
            return Outputs()
        code = source.body(source.workflows[name])
        parts = sections(code, WORKFLOW_LABELS, "main")
        scope = Scope(source=source, prefix=prefix, depth=depth)
        takes = [s.split()[0] for s in statements(section_text(code, parts, "take")) if s.split()]
        for k, take in enumerate(takes):
            scope.env[take] = set(inputs[k]) if k < len(inputs) else set()
        self.run_statements(section_text(code, parts, "main"), scope)
        emits = Outputs()
        for stmt in statements(section_text(code, parts, "emit")):
            m = re.match(r"(\w+)\s*=(?!=)\s*(.*)", stmt, re.S)
            if m:
                emit, value = m.group(1), self.evaluate(m.group(2), scope)
            else:
                names = re.findall(r"\w+", stmt)
                emit, value = (names[-1] if names else stmt), self.evaluate(stmt, scope)
            emits.by_emit[emit] = emits.by_emit.get(emit, set()) | value
            emits.all |= value
        emits.order = list(emits.by_emit)
        return emits

    def run_statements(self, code: str, scope: Scope) -> None:
        for stmt in statements(code):
            if CONTROL.match(stmt):
                self.run_branches(stmt, scope)
            else:
                self.run_statement(stmt, scope)

    def run_branches(self, stmt: str, scope: Scope) -> None:
        """if/else (and loops, try/catch): run every branch on its own copy of the variables, then merge.
        The values from before stay possible unless the chain ends in a plain `else`."""
        rest = CONTROL.sub("", stmt, count=1).lstrip()
        if rest.startswith("("):
            rest = rest[close_of(rest, 0) + 1 :]
        blocks, pos, has_else = [], 0, False
        for start, end in brace_blocks(rest):
            has_else = re.fullmatch(r"\s*else\s*", rest[pos : start - 1]) is not None
            blocks.append(rest[start:end])
            pos = end + 1
        if not blocks:  # `if (x) FOO(ch)` without braces
            blocks = [rest]
        before, results = scope.env, []
        for block in blocks:
            scope.env = {k: set(v) for k, v in before.items()}
            self.run_statements(block, scope)
            results.append(scope.env)
        if not has_else or not stmt.lstrip().startswith("if"):
            results.append(before)
        merged: dict[str, Producers] = {}
        for env in results:
            for k, v in env.items():
                merged.setdefault(k, set()).update(v)
        scope.env = merged

    def run_statement(self, stmt: str, scope: Scope) -> None:
        targets = re.findall(r"\.set\s*\{\s*(\w+)\s*\}", stmt)
        stmt = re.sub(r"\.set\s*\{\s*\w+\s*\}", "", stmt)
        m = re.match(r"(?:def\s+)?(\(\s*[\w\s,]+\)|\w+)\s*=(?!=)\s*(.*)", stmt, re.S)
        if m:
            targets += re.findall(r"\w+", m.group(1))
            stmt = m.group(2)
        value = self.evaluate(stmt, scope)
        for target in targets:
            if target != "def":
                scope.env[target] = set(value)  # reassignment replaces; branches are merged in run_branches

    def evaluate(self, expr: str, scope: Scope) -> Producers:
        """Producers carried by an expression; calls inside it are run (and add nodes and edges)."""
        pipes = split_top(expr, "|")
        if len(pipes) > 1:
            return self._pipe(pipes, scope)
        value: Producers = set()
        i = 0
        while m := IDENT.search(expr, i):
            name, i = m.group(1), m.end()
            after = expr[i:]
            call = re.match(r"\s*([({])", after)  # `PROC(ch)`, or the closure form `PROC { ch }`
            out = OUT_REFERENCE.match(after)
            if call and self.pipe.resolve(scope.source, name):
                open_at = i + call.end() - 1
                close_at = close_of(expr, open_at)
                args = expr[open_at + 1 : close_at]
                lines = statements(args) if call.group(1) == "{" else [args]  # a block has one argument per line
                value |= self.call(name, [a for line in lines for a in self._arguments(line, scope)], scope)
                i = close_at + 1
            elif out:
                value |= self._out_reference(name, out, scope)
                i += out.end()
            elif name in scope.env:
                value |= scope.env[name]
            elif (
                call
                and call.group(1) == "("
                and re.fullmatch(r"[A-Z][A-Z0-9_]+", name)
                and len(name) > 2
                and not re.search(r"\bnew\s+$", expr[: m.start()])
            ):  # `new URL(...)` is a Java class
                self.pipe.warn(f"call of unknown {name}() in {scope.source.rel}")
        return value

    def _arguments(self, args: str, scope: Scope) -> list[Producers]:
        return [self.evaluate(a, scope) for a in split_top(args, ",")] if args.strip() else []

    def _pipe(self, pipes: list[str], scope: Scope) -> Producers:
        """`ch | PROC | OTHER(x)`: each process or workflow gets the value of the left side as first input."""
        value = self.evaluate(pipes[0], scope)
        for segment in pipes[1:]:
            m = re.match(r"\s*(\w+)\s*(\((.*)\))?\s*$", segment, re.S)
            if m and self.pipe.resolve(scope.source, m.group(1)):
                extra = self._arguments(m.group(3), scope) if m.group(3) else []
                value = self.call(m.group(1), [value, *extra], scope)
            else:
                value = value | self.evaluate(segment, scope)
        return value

    def _out_reference(self, name: str, out: re.Match[str], scope: Scope) -> Producers:
        """`NAME.out`, `NAME.out.emit` or `NAME.out[i]`."""
        if name in scope.outs:
            return scope.outs[name].get(out.group(1), out.group(2))
        if name not in scope.env:
            self.pipe.warn(
                f"{name}.out used before {name} is called, or {name} is unknown "
                f"(in {scope.prefix or 'entry workflow'}, {scope.source.rel})"
            )
        return set()

    def call(self, name: str, values: list[Producers], scope: Scope) -> Producers:
        """Run a process or workflow call: add the node and its input edges, or inline the workflow."""
        resolved = self.pipe.resolve(scope.source, name)
        if resolved is None:
            return set()
        kind, source, defined = resolved
        if kind == "process":
            node = scope.prefix + name
            self.graph.add_node(node, source, defined)
            for v in values:
                for producer in self.graph.connect(v, node):
                    self.pipe.warn(f"left out {producer} -> {node}: it would close a cycle (alternative branches)")
            emits = self.pipe.process_info(source, defined).emits
            outs = Outputs(
                all={(node, e) for e in emits} or {(node, "out")}, by_emit={e: {(node, e)} for e in emits}, order=emits
            )
        else:
            outs = self.run_workflow(source, defined, scope.prefix + name + ":", values, scope.depth + 1)
        if name in scope.outs:
            scope.outs[name].merge(outs)
        else:
            scope.outs[name] = outs
        return outs.all
