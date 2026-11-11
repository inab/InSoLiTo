"""One process: its inputs and outputs, and all information about the tools it runs."""

import fnmatch
import re
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, Final

import yaml

from .groovy import IDENT, KEYWORDS, Span, section_text, sections, statement_spans, statements, string_literals
from .shell import commands

if TYPE_CHECKING:
    from .sources import Pipeline, Source

PROCESS_LABELS: Final = ["input", "output", "when", "script", "shell", "exec", "stub"]
SCRIPT_SUFFIXES: Final = (".py", ".sh", ".pl", ".r", ".exe", ".jar")
INTO_SKIP: Final = frozenset({"mode", "flatten", "optional", "true", "false"})
META_FIELDS: Final = (
    ("identifier", "biotools_ids"),
    ("homepage", "meta_homepage"),
    ("doi", "meta_doi"),
    ("description", "meta_description"),
)

# the per-node columns of nodes.csv, in order
OUTPUT_FIELDS: Final = (
    "process",
    "file",
    "module",
    "tools",
    "executables",
    "own_scripts",
    "containers",
    "container_tools",
    "container_versions",
    "conda_packages",
    "conda_tools",
    "version_tools",
    "meta_tools",
    "biotools_ids",
    "meta_homepage",
    "meta_doi",
    "meta_description",
    "labels",
)


@dataclass(slots=True)
class Step:
    """One tool a process runs; a process running several tools becomes a chain of steps."""

    tool: str
    source: str  # where the tool name comes from: executable | meta | conda | container | process
    meta_biotools_id: str = ""  # the `biotools:` identifier meta.yml gives for this tool
    declared: str = ""  # the declared tool it belongs to (bowtie2-build -> bowtie2), for the mapping


@dataclass(slots=True)
class ProcessInfo:
    """Everything read from one process definition."""

    process: str
    file: str
    module: str = ""  # nf-core-style module path, e.g. nf-core/samtools/sort
    tools: list[str] = field(default_factory=list)  # combined best guess
    executables: list[str] = field(default_factory=list)
    own_scripts: list[str] = field(default_factory=list)
    containers: list[str] = field(default_factory=list)
    container_tools: list[str] = field(default_factory=list)
    container_versions: list[str] = field(default_factory=list)
    conda_packages: list[str] = field(default_factory=list)
    conda_tools: list[str] = field(default_factory=list)
    version_tools: list[str] = field(default_factory=list)
    meta_tools: list[str] = field(default_factory=list)
    biotools_ids: list[str] = field(default_factory=list)
    meta_homepage: list[str] = field(default_factory=list)
    meta_doi: list[str] = field(default_factory=list)
    meta_description: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    # for the graph, not written out as process columns
    emits: list[str] = field(default_factory=list)  # output names in order (for .out.name and .out[i])
    into: list[str] = field(default_factory=list)  # DSL1 output channels
    takes_from: list[str] = field(default_factory=list)  # DSL1 input channels
    meta_ids: dict[str, str] = field(default_factory=dict)  # meta.yml tool (lower case) -> biotools:ID
    steps: list[Step] = field(default_factory=list)  # the tools it runs, in script order

    def row(self) -> dict[str, str]:
        """The output columns, lists joined with ';'."""
        values = {name: getattr(self, name) for name in OUTPUT_FIELDS}
        return {name: ";".join(v) if isinstance(v, list) else v for name, v in values.items()}


def _channels(output: str, inputs: str) -> tuple[list[str], list[str], list[str]]:
    """(emit names, DSL1 `into` channels, DSL1 `from` channels) of the output and input sections."""
    emits, into, takes_from = [], [], []
    for k, stmt in enumerate(statements(output)):
        m = re.search(r"\bemit\s*:\s*(\w+)", stmt)
        emits.append(m.group(1) if m else f"out{k}")
        m = re.search(r"\binto\s+(.+)", stmt)
        if m:
            into += [x for x in re.findall(r"\b\w+\b", m.group(1)) if x not in INTO_SKIP]
    for stmt in statements(inputs):
        m = re.search(r"\bfrom\s+(.+)", stmt, re.S)
        if m:
            takes_from += [x for x in IDENT.findall(m.group(1)) if x not in KEYWORDS]
    return emits, into, takes_from


def _module(rel: str) -> str:
    """nf-core-style module path of a file under modules/, else ''."""
    path = PurePosixPath(rel)
    if "modules" not in path.parts:
        return ""
    inner = path.parts[path.parts.index("modules") + 1 :]
    return "/".join(inner[:-1]) if path.name == "main.nf" else "/".join(inner)[:-3]


def _directives(code: str, clean: str, span: Span) -> dict[str, list[str]]:
    """Directive name -> its expressions (clean text), from the part of a process before its sections."""
    directives: dict[str, list[str]] = {}
    a, b = span
    for s, e in statement_spans(code[a:b]):
        m = re.match(r"\s*(\w+)\b\s*(.*)", clean[a + s : a + e], re.S)
        if m:
            directives.setdefault(m.group(1), []).append(m.group(2))
    return directives


def _literals(pipe: "Pipeline", expr: str) -> list[str]:
    """Quoted literals of an expression, plus the config values of the `params.x` it uses."""
    return string_literals(expr) + [pipe.params.get(p, "") for p in re.findall(r"params\.(\w+)", expr)]


def _containers(info: ProcessInfo, pipe: "Pipeline", exprs: list[str]) -> None:
    """Container images, and the tool names and versions read from them."""
    images = []
    for expr in exprs:
        for literal in _literals(pipe, expr):
            images += re.findall(r"[\w.\-/:@]*[\w\-]+/[\w.\-/:@]+|^[\w.\-]+:[\w.\-]+$", literal.strip())
    info.containers = list(dict.fromkeys(i for i in images if not i.endswith(".config")))
    tools, versions = [], []
    for image in info.containers:
        tool, version = _image_tool(image)
        if tool:
            tools.append(tool)
            if version:
                versions.append(f"{tool}={version}")
    info.container_tools, info.container_versions = list(dict.fromkeys(tools)), list(dict.fromkeys(versions))


def _image_tool(image: str) -> tuple[str, str]:
    """(tool name, version) read from a container image; ('', '') for multi-tool `mulled-v2` images."""
    last = image.rstrip("/").split("/")[-1]
    tool, _, tag = last.partition(":")
    if re.search(r"\.(sif|img|simg)$", tool):  # Singularity image file: blast-2.13.0.sif
        tool = re.sub(r"\.(sif|img|simg)$", "", tool)
        m = re.match(r"(.+?)[-_]v?(\d[\w.\-]*)$", tool)
        tool, tag = (m.group(1), m.group(2)) if m else (tool, "")
    if tool.startswith("mulled-v2") or not tool:
        return "", ""
    return tool.lower(), tag.split("--")[0]


def _environment_file(path: Path) -> list[str]:
    """The dependencies listed in a conda environment.yml."""
    try:
        content = yaml.safe_load(path.read_text())
        # a git symlink (`../envs/qiime2.yml`) is stored in the crate as a file holding the target path
        if isinstance(content, str) and content.strip().endswith((".yml", ".yaml")):
            target = (path.parent / content.strip()).resolve()
            content = yaml.safe_load(target.read_text()) if target.is_file() else None
    except yaml.YAMLError:
        content = None
    deps = content.get("dependencies") or [] if isinstance(content, dict) else []
    return [d for d in deps if isinstance(d, str)]


def _conda(info: ProcessInfo, pipe: "Pipeline", source: "Source", exprs: list[str]) -> None:
    """Conda packages (inline, from params, or from environment.yml next to the module) and their names."""
    packages = []
    for expr in exprs:
        for literal in _literals(pipe, expr):
            if literal.endswith((".yml", ".yaml")):
                env = source.path.parent / PurePosixPath(literal).name
                if env.is_file():
                    packages += _environment_file(env)
            elif "${" not in literal:
                packages += literal.split()
    info.conda_packages = list(dict.fromkeys(packages))
    info.conda_tools = list(
        dict.fromkeys(re.split(r"[=<>!~ ]", p.split("::")[-1])[0].lower() for p in packages if not p.startswith("-"))
    )


def _script_texts(pipe: "Pipeline", source: "Source", script_clean: str) -> tuple[list[str], list[str]]:
    """(shell texts to read commands from, template names) of a process script."""
    texts = [m.group(2) for m in re.finditer(r"(\"\"\"|''')(.*?)\1", script_clean, re.S)]
    if not texts:
        texts = string_literals(script_clean)
    templates = []
    for template in re.findall(r"\btemplate\s*\(?\s*['\"]([^'\"]+)['\"]", script_clean):
        templates.append(PurePosixPath(template).name)
        for path in [source.path.parent / "templates" / template, pipe.root / "templates" / template]:
            if path.is_file() and path.suffix in ("", ".sh", ".bash"):
                texts.append(path.read_text(errors="replace"))
                break
    return texts, templates


def _script(info: ProcessInfo, pipe: "Pipeline", source: "Source", script_clean: str, output: str) -> None:
    """Executables, own scripts and versions.yml tools of the script (and of bin/ shell wrappers it calls)."""
    texts, templates = _script_texts(pipe, source, script_clean)
    executables, scripts, version_tools = [], [], []
    for text in texts:
        found = commands(text, pipe.bin_names)
        executables += found.executables
        scripts += found.scripts
        version_tools += found.version_tools
    for script in list(scripts):  # shell wrappers in bin/ (blast.sh): their commands are the real tools
        path = pipe.bin_files.get(script)
        if path and (path.suffix in (".sh", ".bash") or path.read_text(errors="replace").startswith("#!/bin/bash")):
            found = commands(path.read_text(errors="replace"), pipe.bin_names)
            executables += found.executables
            scripts += found.scripts
    version_tools += re.findall(r"\beval\s*\(\s*['\"]\s*([A-Za-z][\w.+-]*)", output)
    info.own_scripts = list(dict.fromkeys(templates + scripts))
    info.executables = [e for e in dict.fromkeys(executables) if e not in info.own_scripts]
    info.version_tools = list(dict.fromkeys(t.lower() for t in version_tools))


def _meta_yml(info: ProcessInfo, source: "Source") -> None:
    """Tools, bio.tools IDs, homepage, DOI and description from an nf-core-style meta.yml next to the module."""
    meta_file = source.path.parent / "meta.yml"
    if source.path.name != "main.nf" or not meta_file.is_file():
        return
    try:
        meta: Any = yaml.safe_load(meta_file.read_text()) or {}
    except yaml.YAMLError:
        meta = {}
    for entry in meta.get("tools") or [] if isinstance(meta, dict) else []:
        for tool, raw in entry.items() if isinstance(entry, dict) else [(entry, {})]:
            details = raw if isinstance(raw, dict) else {}
            info.meta_tools.append(str(tool))
            for key, name in META_FIELDS:
                value = " ".join(str(details.get(key) or "").split())
                if value and (key != "identifier" or value.startswith("biotools:")):
                    getattr(info, name).append(value)
                    if key == "identifier":
                        info.meta_ids[str(tool).lower()] = value


def _one_tool_images(info: ProcessInfo) -> list[str]:
    """Tool names of biocontainer-style images, which hold one tool (a pipeline's own image holds all of them)."""
    tools = [_image_tool(i)[0] for i in info.containers if re.search(r"biocontainers|depot\.galaxyproject\.org", i)]
    return [t for t in tools if t]


def _best_tools(info: ProcessInfo) -> list[str]:
    """The combined best guess of the tools a process runs."""
    # for a pipeline's own image (e.g. `unbequant`) the executables are the better guess than the image name
    for candidates in (
        info.meta_tools,
        info.conda_tools,
        _one_tool_images(info),
        info.version_tools,
        info.executables,
        info.container_tools,
    ):
        if candidates:
            return list(dict.fromkeys(t.lower() for t in candidates))
    return [info.process.lower()]


def _comparable(name: str) -> str:
    """A tool name for matching executables with declared tools: lower case, no suffix, no -, _ or ."""
    name = name.lower()
    for suffix in SCRIPT_SUFFIXES:
        name = name.removesuffix(suffix)
    return re.sub(r"[-_.]", "", name)


def _same_tool(executable: str, declared: str) -> bool:
    """`bowtie2-build` belongs to `bowtie2`, `bwa-mem2` to `bwa-mem2`: one name starts with the other.
    Bioconda packages may carry a group prefix: `bedGraphToBigWig` is `ucsc-bedgraphtobigwig`."""
    a, b = _comparable(executable), _comparable(declared)
    if not (a and b):
        return False
    grouped = declared.lower().split("-", 1)
    return a.startswith(b) or b.startswith(a) or (len(grouped) == 2 and _comparable(grouped[1]) == a)


def _is_excluded(name: str, excluded: frozenset[str]) -> bool:
    """Whether a tool is on the exclusion list, by name or by a glob pattern (`r-*`)."""
    name = name.lower()
    return name in excluded or any(fnmatch.fnmatchcase(name, p) for p in excluded if any(c in p for c in "*?["))


def _steps(info: ProcessInfo, excluded: frozenset[str]) -> list[Step]:
    """The tools a process runs, in script order: executables, restricted to the software the module declares."""
    executables = [e for e in info.executables if not _is_excluded(e, excluded)]
    # meta.yml often names only the main tool (bwa), the conda environment also the others (samtools)
    sources = {"meta": info.meta_tools, "conda": info.conda_tools, "container": _one_tool_images(info)}
    sources = {k: [d for d in v if not _is_excluded(d, excluded)] for k, v in sources.items()}
    declared = [d for names in sources.values() for d in names]
    if not declared:
        steps = [Step(e, "executable") for e in executables]
    else:
        steps = []
        for e in executables:
            match = next((d for d in declared if _same_tool(e, d)), None)
            if match is not None:
                meta = next((m for m in sources["meta"] if _same_tool(e, m)), "")
                steps.append(Step(e, "executable", info.meta_ids.get(meta.lower(), ""), match))
        if not steps:  # nothing in the script matches (amrfinder_update vs amrfinderplus): the declared tools
            source, names = next((k, v) for k, v in sources.items() if v)
            steps = [Step(d, source, info.meta_ids.get(d.lower(), ""), d) for d in names]
    return steps or [Step(info.process, "process")]  # only own scripts: the process stands for its tool


def read_process(pipe: "Pipeline", source: "Source", name: str) -> ProcessInfo:
    """Read one process definition of source."""
    span = source.processes[name]
    code, clean = source.body(span), source.body(span, clean=True)
    parts = sections(code, PROCESS_LABELS, "directives")

    info = ProcessInfo(process=name, file=source.rel, module=_module(source.rel))
    info.emits, info.into, info.takes_from = _channels(
        section_text(code, parts, "output"), section_text(code, parts, "input")
    )
    directives = _directives(code, clean, parts["directives"])
    info.labels = [x for expr in directives.get("label", []) for x in string_literals(expr) if x]
    names = [name, ":" + name] + [
        alias for s in pipe.sources.values() for alias, (orig, _) in s.includes.items() if orig == name
    ]
    _containers(info, pipe, directives.get("container", []) + pipe.config_values("container", names, info.labels))
    _conda(info, pipe, source, directives.get("conda", []) + pipe.config_values("conda", names, info.labels))

    # script: triple-quoted strings of script/shell (else of the whole body), plus templates
    script_clean = section_text(clean, parts, "script") + section_text(clean, parts, "shell")
    if not script_clean and "exec" not in parts:
        script_clean = clean
    _script(info, pipe, source, script_clean, section_text(clean, parts, "output"))
    _meta_yml(info, source)
    info.tools = _best_tools(info)
    info.steps = _steps(info, pipe.excluded_tools)
    return info
