"""Markdown ファイルの YAML 風フロントマターを読む最小パーサ。

このリポジトリのスキーマ（スカラー・インラインリスト・ダッシュリスト）だけを
サポートする。外部依存ゼロを維持するため、汎用 YAML パーサは使わない。
"""

import re
from pathlib import Path

_FM_RE = re.compile(r"^---\n(.*?)\n---\n?", re.S)
_KV_RE = re.compile(r"^([A-Za-z_][\w-]*):\s*(.*)$")
_DASH_RE = re.compile(r"^\s+-\s+(.*)$")


def coerce(raw: str):
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [coerce(x) for x in inner.split(",")]
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ("'", '"'):
        return raw[1:-1]
    if raw in ("null", "~", "None"):
        return None
    if raw == "true":
        return True
    if raw == "false":
        return False
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


def parse_frontmatter(text: str):
    """フロントマターを dict で返す。無ければ None。"""
    m = _FM_RE.match(text)
    if not m:
        return None
    data = {}
    current_list_key = None
    for line in m.group(1).split("\n"):
        if not line.strip() or line.strip().startswith("#"):
            continue
        dash = _DASH_RE.match(line)
        if dash and current_list_key is not None:
            data[current_list_key].append(coerce(dash.group(1)))
            continue
        kv = _KV_RE.match(line)
        if kv:
            key, raw = kv.group(1), kv.group(2).strip()
            if raw == "":
                data[key] = []
                current_list_key = key
            else:
                data[key] = coerce(raw)
                current_list_key = None
    return data


def load(path: Path):
    """ファイルからフロントマターを読む。(dict|None, error|None) を返す。"""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        return None, f"読み込み失敗: {e}"
    fm = parse_frontmatter(text)
    if fm is None:
        return None, "フロントマターがない"
    return fm, None


def collect(directory: Path, recursive: bool = True):
    """ディレクトリ配下の .md（テンプレート除く）を (path, fm, error) で列挙する。"""
    if not directory.is_dir():
        return
    pattern = "**/*.md" if recursive else "*.md"
    for path in sorted(directory.glob(pattern)):
        if path.name.startswith("_"):
            continue
        fm, err = load(path)
        yield path, fm, err
