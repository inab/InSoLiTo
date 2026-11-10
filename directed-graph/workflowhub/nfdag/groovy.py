"""Reading Groovy (Nextflow) source without evaluating it: masking, brackets, sections and statements."""

import re
from collections.abc import Iterator
from typing import Final

Span = tuple[int, int]

# Groovy keywords and Nextflow globals: never a channel or a process
_KEYWORD_WORDS: Final = """
    if else for while def return true false null new in it params Channel channel workflow file files log task
    this println exit switch case try catch finally throw as instanceof
"""
KEYWORDS: Final = frozenset(_KEYWORD_WORDS.split())
CONTROL: Final = re.compile(r"^\s*(if|else|for|while|try|catch|finally|switch)\b")
IDENT: Final = re.compile(r"(?<![\w.$@])([A-Za-z_]\w*)")

OPENING: Final = "([{"
CLOSING: Final = ")]}"
SLASHY_AFTER: Final = "(,=~!&|:?[{;"  # a `/` after one of these starts a slashy string, not a division


def _string_end(text: str, i: int) -> int:
    """text[i] starts a string literal; return the index just past its end."""
    n = len(text)
    if text.startswith("$/", i):
        j = text.find("/$", i + 2)
        return n if j < 0 else j + 2
    for quote in ('"""', "'''"):
        if text.startswith(quote, i):
            j = i + 3
            while j < n:
                if text[j] == "\\":
                    j += 2
                elif quote == '"""' and text.startswith("${", j):
                    j = _code_end(text, j + 2)
                elif text.startswith(quote, j):
                    return j + 3
                else:
                    j += 1
            return n
    quote = text[i]
    j = i + 1
    while j < n:
        c = text[j]
        if c == "\\":
            j += 2
        elif quote == '"' and text.startswith("${", j):
            j = _code_end(text, j + 2)
        elif c == quote:
            return j + 1
        elif c == "\n":  # unterminated one-line string (or a division misread as slashy string)
            return j
        else:
            j += 1
    return n


def _code_end(text: str, j: int) -> int:
    """Return the index just past the '}' that closes a ${...} interpolation starting at j."""
    depth = 0
    while j < len(text):
        c = text[j]
        if c in "\"'":
            j = _string_end(text, j)
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            if depth == 0:
                return j + 1
            depth -= 1
        j += 1
    return len(text)


def _blank(chars: list[str], start: int, end: int) -> None:
    """Replace chars[start:end] by spaces, keeping newlines (so positions and line numbers stay)."""
    for k in range(start, end):
        if chars[k] != "\n":
            chars[k] = " "


def _comment_end(text: str, i: int) -> int:
    """text[i] starts a `//` or `/* */` comment; return the index just past it."""
    if text.startswith("//", i):
        j = text.find("\n", i)
        return len(text) if j < 0 else j
    j = text.find("*/", i + 2)
    return len(text) if j < 0 else j + 2


def scan(text: str) -> tuple[str, str]:
    """Return (clean, code), both as long as text: comments blanked in both, string contents also in code."""
    clean, code = list(text), list(text)
    i, prev = 0, ""
    if text.startswith("#!"):
        i = text.find("\n") if "\n" in text else len(text)
        _blank(clean, 0, i)
        _blank(code, 0, i)
    while i < len(text):
        c = text[i]
        if text.startswith(("//", "/*"), i):
            j = _comment_end(text, i)
            _blank(clean, i, j)
            _blank(code, i, j)
            i = j
            continue
        if c in "\"'" or text.startswith("$/", i) or (c == "/" and prev in SLASHY_AFTER):
            j = _string_end(text, i)
            _blank(code, i + 1, j - 1)
            i, prev = j, '"'
            continue
        if not c.isspace():
            prev = c
        i += 1
    return "".join(clean), "".join(code)


def close_of(code: str, i: int) -> int:
    """code[i] is an opening bracket; return the index of its matching closing bracket."""
    depth = 0
    for j in range(i, len(code)):
        if code[j] in OPENING:
            depth += 1
        elif code[j] in CLOSING:
            depth -= 1
            if depth == 0:
                return j
    return len(code) - 1


def depths(code: str) -> list[int]:
    """Bracket depth before each character."""
    out, depth = [], 0
    for c in code:
        out.append(depth)
        if c in OPENING:
            depth += 1
        elif c in CLOSING:
            depth = max(depth - 1, 0)
    return out


def labels_at_top(code: str, names: list[str]) -> list[tuple[str, int, int]]:
    """[(label, start of label, end of label)] for `name:` labels at bracket depth 0 of code."""
    d = depths(code)
    pattern = re.compile(r"^[ \t]*(" + "|".join(names) + r")[ \t]*:(?!:)", re.M)
    return [(m.group(1), m.start(1), m.end()) for m in pattern.finditer(code) if d[m.start(1)] == 0]


def sections(code: str, names: list[str], default: str) -> dict[str, Span]:
    """Split code by labels; text before the first label goes to `default`. Returns {label: (start, end)}."""
    found = labels_at_top(code, names)
    out: dict[str, Span] = {}
    for k, (name, _, end) in enumerate(found):
        out.setdefault(name, (end, found[k + 1][1] if k + 1 < len(found) else len(code)))
    out.setdefault(default, (0, found[0][1] if found else len(code)))
    return out


def section_text(code: str, parts: dict[str, Span], label: str) -> str:
    """The text of one section, or '' if the label is not there."""
    if label not in parts:
        return ""
    start, end = parts[label]
    return code[start:end]


def _continues(stripped: str, following: str, depth: int) -> bool:
    """Whether a statement goes on after this line."""
    return (
        depth > 0
        or stripped.endswith(("(", ",", "=", "|", "?", ":", "+", "&&", "||", "->", "."))
        or (following.startswith((".", "|", "?", ":")) and not following.startswith("||"))
        or re.match(r"(else|catch|finally)\b", following) is not None
    )


def _split_semicolons(code: str, start: int, end: int) -> list[Span]:
    """`a; b` on one line: split code[start:end] at ';' outside brackets."""
    spans, seg, depth = [], start, 0
    for p in range(start, end):
        if code[p] in OPENING:
            depth += 1
        elif code[p] in CLOSING:
            depth = max(depth - 1, 0)
        elif code[p] == ";" and depth == 0:
            spans.append((seg, p))
            seg = p + 1
    spans.append((seg, end))
    return spans


def statement_spans(code: str) -> list[Span]:
    """(start, end) of each statement: newlines at bracket depth 0 end one, unless the line continues."""
    lines = code.split("\n")
    line_starts, pos = [], 0
    for line in lines:
        line_starts.append(pos)
        pos += len(line) + 1
    following, nxt = [""] * len(lines), ""
    for k in range(len(lines) - 1, -1, -1):
        following[k] = nxt
        nxt = lines[k].strip() or nxt
    spans: list[Span] = []
    start: int | None = None
    depth = 0
    for k, line in enumerate(lines):
        if start is None:
            start = line_starts[k]
        for c in line:
            if c in OPENING:
                depth += 1
            elif c in CLOSING:
                depth = max(depth - 1, 0)
        if _continues(line.strip(), following[k], depth) and k < len(lines) - 1:
            continue
        spans += _split_semicolons(code, start, line_starts[k] + len(line))
        start = None
    return [(a, b) for a, b in spans if code[a:b].strip()]


def statements(code: str) -> list[str]:
    """The statements of code, stripped."""
    return [code[a:b].strip() for a, b in statement_spans(code)]


def brace_blocks(text: str) -> Iterator[tuple[int, int]]:
    """(start, end) of the inner text of each top-level `{...}` block in text, left to right."""
    pos = 0
    while True:
        brace = text.find("{", pos)
        if brace < 0:
            return
        end = close_of(text, brace)
        yield brace + 1, end
        pos = end + 1


def flat_statement_spans(code: str, offset: int = 0) -> Iterator[Span]:
    """Statement spans, with the bodies of if/else/for/... blocks replaced by their own statements."""
    for a, b in statement_spans(code):
        text = code[a:b]
        if not CONTROL.match(text):
            yield offset + a, offset + b
            continue
        found = False
        for start, end in brace_blocks(text):
            yield from flat_statement_spans(text[start:end], offset + a + start)
            found = True
        if not found:
            yield offset + a, offset + b


def split_top(code: str, sep: str) -> list[str]:
    """Split code at `sep` characters at bracket depth 0 (`|` ignores `||`)."""
    parts, depth, start, i = [], 0, 0, 0
    while i < len(code):
        c = code[i]
        if c in OPENING:
            depth += 1
        elif c in CLOSING:
            depth = max(depth - 1, 0)
        elif c == sep and depth == 0:
            if sep == "|" and (code[i + 1 : i + 2] == "|" or code[i - 1 : i] == "|"):
                i += 1
                continue
            parts.append(code[start:i])
            start = i + 1
        i += 1
    parts.append(code[start:])
    return parts


def string_literals(clean: str) -> list[str]:
    """All quoted literals in a piece of clean (comment-free) code, including those inside ${...}."""
    return [single or double for single, double in re.findall(r"'([^'\n]*)'|\"([^\"\n]*)\"", clean)]
