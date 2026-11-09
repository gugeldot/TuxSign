#!/usr/bin/env python3
"""Comprueba el estilo de los textos del proyecto: comillas rectas, sin guiones largos y sin punto y coma en prosa.

Revisa documentación, web, textos de la interfaz, comentarios y docstrings. No toca el punto y coma que es sintaxis
(código, CSS, JavaScript, entidades HTML). Devuelve un código de salida distinto de cero si encuentra algo.
"""
from __future__ import annotations

import ast
import io
import os
import re
import sys
import tokenize

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BAD_CHARS = re.compile("[«»“”‘’—–]")
SKIP_DIRS = {".git", ".venv", ".venv-native", "build", "dist", "__pycache__", ".flatpak-builder", "assets"}
SKIP_FILES = {"LICENSE", ".gitignore", "check_text_style.py"}


def strip_md(text: str) -> str:
    text = re.sub(r"```.*?```", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", "", text)
    return re.sub(r"https?://\S+", "", text)


def strip_html(text: str) -> str:
    text = re.sub(r"<(style|script)\b.*?</\1>", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S | re.I)
    text = re.sub(r"&#?\w+;", "", text)  # entidades
    return re.sub(r"https?://\S+", "", text)


def check_lines(path: str, text: str, semicolons: bool = True) -> list[str]:
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        if BAD_CHARS.search(line):
            out.append(f"{path}:{n}: signo no permitido: {line.strip()[:90]}")
        elif semicolons and ";" in line:
            out.append(f"{path}:{n}: punto y coma en prosa: {line.strip()[:90]}")
    return out


def check_py(path: str, src: str) -> list[str]:
    out = check_lines(path, "\n".join(l for l in src.splitlines() if BAD_CHARS.search(l)), semicolons=False)
    out = [f"{path}: {o.split(': ', 1)[1]}" for o in out]
    prose_lines: set[int] = set()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(getattr(first, "value", None), ast.Constant) and isinstance(first.value.value, str):
                prose_lines.update(range(first.lineno, first.end_lineno + 1))
    if path.endswith("i18n.py"):
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and " " in node.value:
                prose_lines.update(range(node.lineno, node.end_lineno + 1))
    lines = src.splitlines()
    for n in sorted(prose_lines):
        if ";" in lines[n - 1]:
            out.append(f"{path}:{n}: punto y coma en prosa: {lines[n - 1].strip()[:90]}")
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT and ";" in tok.string:
            out.append(f"{path}:{tok.start[0]}: punto y coma en comentario: {tok.string[:90]}")
    return out


def main() -> int:
    problems: list[str] = []
    for dirpath, dirnames, files in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in files:
            if name in SKIP_FILES:
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, ROOT)
            ext = os.path.splitext(name)[1]
            try:
                text = open(full, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            if ext == ".md":
                problems += check_lines(rel, strip_md(text))
            elif ext == ".html":
                problems += check_lines(rel, strip_html(text))
            elif ext == ".js":
                strings = "\n".join(m.group(0) for m in re.finditer(r'"(?:[^"\\\n]|\\.)*"', text) if len(m.group(0)) > 25)
                problems += [f"{rel}: {p.split(': ', 1)[1]}" for p in check_lines(rel, strings)]
                problems += [f"{rel}:{n}: signo no permitido" for n, l in enumerate(text.splitlines(), 1) if BAD_CHARS.search(l)]
            elif ext == ".py" or name == "tuxsign-launcher":
                problems += check_py(rel, text)
            elif ext in (".sh", ".yml", ".yaml") or name == "build.sh":
                comments = "\n".join(l if l.lstrip().startswith("#") else "" for l in text.splitlines())
                problems += check_lines(rel, comments)
                problems += [f"{rel}:{n}: signo no permitido" for n, l in enumerate(text.splitlines(), 1) if BAD_CHARS.search(l)]
            elif ext in (".json", ".xml", ".desktop", ".css", ".txt", ".toml"):
                problems += [f"{rel}:{n}: signo no permitido" for n, l in enumerate(text.splitlines(), 1) if BAD_CHARS.search(l)]
    for p in problems:
        print(p)
    print(f"\n{len(problems)} problemas de estilo." if problems else "Estilo de textos correcto.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
