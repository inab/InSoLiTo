"""The tools a process runs: commands in its shell script, its own scripts, and versions.yml entries."""

import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Final

# First words of script lines that are not tools worth mapping (shell builtins, coreutils, script keywords)
_SHELL_SKIP_WORDS: Final = """
    echo printf cat mkdir cp mv rm ln cd export ls touch head tail sort uniq cut grep egrep fgrep zgrep awk gawk
    sed tr wc gzip gunzip zcat tar unzip zip find xargs test true false set unset if then else elif fi for do
    done while until case esac exit return local declare readonly source . [ [[ ] ]] sleep wait date basename
    dirname readlink realpath tee paste join split chmod chown env which seq pwd md5sum sha256sum shift eval
    trap read column rev curl wget function let printenv mktemp trap ulimit hostname whoami uname nproc expr
    bc yes cmp diff comm du df file stat sync kill touch type alias shopt pushd popd getopts break continue
    in import from def print library suppressPackageStartupMessages require try except with else: end
    usr bin time sudo exec nohup command timeout parallel
"""
SHELL_SKIP: Final = frozenset(_SHELL_SKIP_WORDS.split())
# words before the actual command: `time samtools ...`, `xargs -n 1 gzip`
_WRAPPER_WORDS: Final = "time sudo exec nohup command then else do ! { ( xargs parallel env timeout srun"
WRAPPERS: Final = frozenset(_WRAPPER_WORDS.split())
_INTERPRETER_WORDS: Final = (
    "python python2 python3 Rscript R perl ruby node bash sh zsh java groovy julia pypy pypy3 mono"
)
INTERPRETERS: Final = frozenset(_INTERPRETER_WORDS.split())
SCRIPT_FILE: Final = re.compile(r"\.(py|R|r|pl|rb|js|sh|groovy|jl)$")


@dataclass(slots=True)
class Commands:
    """What a shell script runs."""

    executables: list[str] = field(default_factory=list)
    scripts: list[str] = field(default_factory=list)  # the pipeline's own scripts (bin/, python x.py, ...)
    version_tools: list[str] = field(default_factory=list)  # tool names written into versions.yml


def _one_word_values(script: str) -> dict[str, list[str]]:
    """`ANALYSE="blastp"` ... `$ANALYSE -query ...`: one-word values a command may come from."""
    words: dict[str, list[str]] = {}
    for var, value in re.findall(
        r"""^\s*(?:export\s+|local\s+)?(\w+)=["']?([A-Za-z][\w.+-]*)["']?\s*$""", script, re.M
    ):
        words.setdefault(var, []).append(value)
    return words


def _command_line(stripped: str) -> str:
    """The part of a script line in which commands are looked for."""
    # `CMD="diamond blastx ..."` followed by `eval $CMD`: the value is the command line
    m = re.match(r"""(?:export\s+|local\s+)?\w*(?:CMD|cmd|COMMAND|command)\w*=(["'])(.*?)\1?$""", stripped)
    if m:
        stripped = m.group(2)
    # `$(get_bin_dir.sh)/tool/tool.exe`: a substitution used as a path prefix is part of the path
    stripped = re.sub(r"\\?\$\([^()]*\)(?=/)", "dir", stripped)
    # `sed -e 's/a/b/g; s/c/d/g' -e "s/'/x/g"`: no commands inside quoted arguments
    return re.sub(r"""(?<=\s)('[^']*'|"[^"]*")""", "''", stripped)


def _interpreter_call(first: str, rest: list[str], found: Commands) -> None:
    """`python x.py`, `java -jar tool.jar`, `mono Tool.exe`: record the script or tool that is run."""
    if first == "java" and "-jar" in rest and rest.index("-jar") + 1 < len(rest):
        found.executables.append(PurePosixPath(rest[rest.index("-jar") + 1]).stem)
        return
    if first == "mono" and rest:  # mono ThermoRawFileParser.exe
        found.executables.append(PurePosixPath(rest[0].split("/")[-1]).stem)
        return
    target = next((t for t in rest if not t.startswith("-") and "=" not in t), "")
    if SCRIPT_FILE.search(target):
        found.scripts.append(target.split("/")[-1])


def _segment(segment: str, words: dict[str, list[str]], bin_names: set[str], found: Commands) -> None:
    """Record the command at the start of one segment of a line (between `|`, `&&`, `;`, `$(` ...)."""
    tokens = segment.split()
    while tokens and (tokens[0] in WRAPPERS or re.match(r"^\w+=", tokens[0]) or tokens[0].startswith("-")):
        tokens.pop(0)
    if not tokens:
        return
    first = tokens[0].strip("'\"")
    m = re.fullmatch(r"\$\{?(\w+)\}?", first)
    if m and m.group(1) in words:
        found.executables += [w for w in words[m.group(1)] if w not in SHELL_SKIP and w not in bin_names]
        return
    if "$" in first or "{" in first or first.endswith(":") or first.endswith((".sif", ".img")):
        return
    first = first.rstrip("/").split("/")[-1]
    if first in INTERPRETERS:
        _interpreter_call(first, [t.strip("'\"") for t in tokens[1:]], found)
        return
    if not re.match(r"^[A-Za-z][\w.+-]*$", first) or first in SHELL_SKIP:
        return
    if first in bin_names:
        found.scripts.append(first)
    else:
        found.executables.append(first)


def commands(script: str, bin_names: set[str]) -> Commands:
    """Executables, own scripts and versions.yml tools of a shell script."""
    found = Commands()
    shebang = script.lstrip().split("\n")[0]
    if shebang.startswith("#!") and not re.search(r"\b(ba|z)?sh\b", shebang):
        return found  # the whole script is Python/R/Perl, not shell commands
    script = re.sub(r"\\\\?\n", " ", script)
    words = _one_word_values(script)
    functions: set[str] = set()
    heredoc: str | None = None
    for line in script.split("\n"):
        stripped = line.strip()
        if heredoc:
            if stripped == heredoc:
                heredoc = None
            else:
                m = re.match(r"""["']?([A-Za-z][\w.+-]*)["']?\s*:\s*\\?\$\(""", stripped)
                if m:
                    found.version_tools.append(m.group(1))
            continue
        m = re.search(r"(?<!<)<<-?\s*['\"]?(\w+)['\"]?", stripped)
        if m:
            heredoc = m.group(1)
        if not stripped or stripped.startswith("#"):
            continue
        m = re.match(r"(?:function\s+)?([\w-]+)\s*\(\s*\)", stripped)
        if m:
            functions.add(m.group(1))
            continue
        for segment in re.split(r"\|\||&&|\||;|\$\(|`|\)", _command_line(stripped)):
            _segment(segment, words, bin_names, found)
    found.executables = [e for e in dict.fromkeys(found.executables) if e not in functions]
    found.scripts = list(dict.fromkeys(found.scripts))
    found.version_tools = [t for t in found.version_tools if t != "task.process"]
    return found
