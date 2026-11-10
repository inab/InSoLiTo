"""The files of one downloaded workflow: .nf sources, includes, bin/ scripts and configs."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .groovy import Span, close_of, scan, string_literals
from .process import ProcessInfo, read_process

Kind = Literal["process", "workflow"]


class Source:
    """One .nf file: its processes, workflows and includes."""

    def __init__(self, path: Path, root: Path) -> None:
        self.path = path
        self.rel = str(path.relative_to(root))
        self.clean, self.code = scan(path.read_text(errors="replace"))
        self.processes: dict[str, Span] = {}  # name -> body span
        self.workflows: dict[str | None, Span] = {}  # None is the unnamed entry workflow
        self.includes: dict[str, tuple[str, str]] = {}  # name used here -> (name defined there, include path)
        self.blocks: list[Span] = []  # whole process and workflow blocks
        self._find_blocks()
        self._find_includes()

    def _find_blocks(self) -> None:
        for m in re.finditer(r"\b(process|workflow)\s+(\w+)?\s*\{|\bworkflow\s*\{", self.code):
            if any(a <= m.start() < b for a, b in self.blocks) or self.code[m.start() - 1 : m.start()] == ".":
                continue
            open_at = m.end() - 1
            close_at = close_of(self.code, open_at)
            self.blocks.append((m.start(), close_at + 1))
            kind, name = (m.group(1), m.group(2)) if m.group(1) else ("workflow", None)
            body = (open_at + 1, close_at)
            if kind == "process" and name:
                self.processes[name] = body
            elif kind == "workflow":
                self.workflows[name] = body

    def _string_variables(self) -> dict[str, str]:
        """`def subworkflowsDir = "${baseDir}/../x"` or `= file("...")`: string variables, for include paths."""
        found = re.findall(r"^\s*(?:def\s+)?(\w+)\s*=\s*(?:file\(\s*)?['\"]([^'\"\n]*)['\"]", self.clean, re.M)
        return {name: value for name, value in found if name not in ("projectDir", "baseDir", "moduleDir")}

    def _find_includes(self) -> None:
        variables = self._string_variables()
        # `include { A; B as C } from '...'` (names and `as` may span lines), and the early `include A from '...'`
        for m in re.finditer(r"\binclude\s*(?:\{([^}]*)\}|(\w+(?:\s+as\s+\w+)?))\s*from\s*", self.code):
            line = self.clean[m.end() : m.end() + 300].split("\n")[0]
            literals = string_literals(line)
            if not literals:
                continue
            target = re.sub(r"\$\{?(\w+)\}?", lambda v: variables.get(v.group(1), v.group(0)), literals[0])
            if re.match(r"\s*\w+\s*\+", line):  # `from PROJECT_DIR + '/x.nf'` (a variable set to projectDir)
                target = "$projectDir" + target
            for item in re.finditer(r"(\w+)(?:\s+as\s+(\w+))?", m.group(1) or m.group(2)):
                self.includes[item.group(2) or item.group(1)] = (item.group(1), target)

    def body(self, span: Span, *, clean: bool = False) -> str:
        return (self.clean if clean else self.code)[span[0] : span[1]]


@dataclass(slots=True)
class ConfigRule:
    """A `withName:` or `withLabel:` block of a config file that sets container or conda."""

    kind: str  # withName | withLabel
    selector: str  # a regular expression, `!` negates it
    values: dict[str, list[str]]  # container / conda -> expressions

    def matches(self, names: list[str], labels: list[str]) -> bool:
        candidates = labels if self.kind == "withLabel" else names
        try:
            hit = any(re.fullmatch(self.selector.lstrip("!"), c) for c in candidates)
        except re.error:
            return False
        return hit != self.selector.startswith("!")


class Pipeline:
    """All sources of one downloaded workflow, with lookups shared by the DSL1 and DSL2 parts."""

    def __init__(self, root: Path, excluded_tools: frozenset[str] = frozenset()) -> None:
        self.root = root
        self.excluded_tools = excluded_tools  # executables that never become tool nodes (pigz, bgzip, ...)
        self.sources: dict[Path, Source] = {}
        for path in sorted(root.rglob("*.nf")):
            if path.is_file():
                self.sources[path] = Source(path, root)
        self.bin_names: set[str] = set()
        self.bin_files: dict[str, Path] = {}
        for path in (root / "bin").rglob("*") if (root / "bin").is_dir() else []:
            if path.is_file():
                self.bin_names.add(path.name)  # exact names: bin/diamond.sh is not the `diamond` tool
                self.bin_files.setdefault(path.name, path)
        self.params: dict[str, str] = {}
        self.config_rules: list[ConfigRule] = []
        self._read_configs()
        self.warnings: list[str] = []
        self._info_cache: dict[tuple[Path, str], ProcessInfo] = {}

    def warn(self, message: str) -> None:
        if message not in self.warnings:
            self.warnings.append(message)

    # ---- names -------------------------------------------------------------

    def resolve(self, source: Source, name: str) -> tuple[Kind, Source, str] | None:
        """(kind, file, defined name) of a process or workflow name used in source, or None."""
        if name in source.processes:
            return "process", source, name
        if name in source.workflows and name:
            return "workflow", source, name
        if name not in source.includes:
            return None
        original, target = source.includes[name]
        if target.startswith("plugin/") or target.endswith((".groovy", ".config")):
            return None  # plugins and function libraries (`lib/utils.groovy`) hold no processes
        path = self.include_file(source, target)
        if path is None:
            self.warn(f"include not found: {target} (from {source.rel})")
            return None
        found = self.sources[path]
        if original in found.processes:
            return "process", found, original
        if original in found.workflows:
            return "workflow", found, original
        return None

    def include_file(self, source: Source, target: str) -> Path | None:
        """The .nf file an include path points to, or None."""
        m = re.match(r"\$\{?(projectDir|baseDir|moduleDir)\}?/?", target)
        if not m:
            folders, rest = [source.path.parent], target
        elif m.group(1) == "moduleDir":
            folders, rest = [source.path.parent], target[m.end() :]
        else:  # the folder of the main script: usually the top folder, but mop_preprocess/mop_preprocess.nf exists
            folders, rest = [self.root, source.path.parent], target[m.end() :]
        for folder in folders:
            base = (folder / rest).resolve()
            for candidate in (base, base.with_name(base.name + ".nf"), base / "main.nf"):
                if candidate.is_file() and candidate in self.sources:
                    return candidate
        return None

    # ---- configs -----------------------------------------------------------

    def _read_configs(self) -> None:
        """params with string values, and withName/withLabel rules that set container or conda."""
        files = list(self.root.glob("*.config")) + list(self.root.glob("conf/**/*.config"))
        for path in files:
            clean, code = scan(path.read_text(errors="replace"))
            for m in re.finditer(r"\bparams\s*\{", code):
                block = clean[m.end() : close_of(code, m.end() - 1)]
                for k, v in re.findall(r"^\s*(\w+)\s*=\s*['\"]([^'\"\n]*)['\"]", block, re.M):
                    self.params.setdefault(k, v)
            for k, v in re.findall(r"\bparams\.(\w+)\s*=\s*['\"]([^'\"\n]*)['\"]", clean):
                self.params.setdefault(k, v)
            for m in re.finditer(r"\b(withName|withLabel)\s*:\s*", code):
                brace = code.find("{", m.end())
                if brace < 0:
                    continue
                selector = clean[m.end() : brace].strip().strip("'\"")
                block = clean[brace + 1 : close_of(code, brace)]
                values = {}
                for key in ("container", "conda"):
                    found = re.findall(rf"\b{key}\s*=\s*(.+)", block)
                    if found:
                        values[key] = found
                if values:
                    self.config_rules.append(ConfigRule(m.group(1), selector, values))

    def config_values(self, key: str, names: list[str], labels: list[str]) -> list[str]:
        """The `key` expressions (container or conda) that config rules set for a process."""
        return [
            value
            for rule in self.config_rules
            if key in rule.values and rule.matches(names, labels)
            for value in rule.values[key]
        ]

    # ---- process information -----------------------------------------------

    def process_info(self, source: Source, name: str) -> ProcessInfo:
        key = (source.path, name)
        if key not in self._info_cache:
            self._info_cache[key] = read_process(self, source, name)
        return self._info_cache[key]
