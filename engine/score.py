#!/usr/bin/env python3
"""予測の採点と、法則への成績伝播 (blame propagation)。

- 解決済み予測ごとに Brier スコアを計算する: (probability - outcome)^2
  （0 が完璧、0.25 がコイン投げ、1 が最悪の自信過剰）
- 各予測のスコアを、その予測が引用した全法則に伝播させる
- 法則ごとの平均 Brier とオープンポジション（未解決の賭け）を
  scoreboard/SCOREBOARD.md に書き出す

法則の評価はここでは機械的な集計に留める。confidence の更新と
falsified 判定は人間（またはAIセッション）が scoreboard を見て行う。
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from frontmatter import collect

ROOT = Path(__file__).parent.parent
SCOREBOARD = ROOT / "scoreboard" / "SCOREBOARD.md"


def brier(probability: float, outcome: bool) -> float:
    return (probability - (1.0 if outcome else 0.0)) ** 2


def grade(mean_brier: float) -> str:
    if mean_brier <= 0.10:
        return "strong"
    if mean_brier <= 0.25:
        return "ok"
    return "falsification-pressure"


def load_docs():
    laws, predictions = [], []
    for _, fm, e in collect(ROOT / "laws"):
        if not e and fm.get("id"):
            laws.append(fm)
    for path, fm, e in collect(ROOT / "predictions"):
        if not e and fm.get("id"):
            fm["_path"] = path
            predictions.append(fm)
    return laws, predictions


def score(laws, predictions):
    resolved = [p for p in predictions
                if p.get("status") == "resolved" and p.get("outcome") in (True, False)]
    open_preds = [p for p in predictions if p.get("status") == "open"]

    rows = []
    for law in sorted(laws, key=lambda l: l.get("id", "")):
        lid = law["id"]
        cited_resolved = [p for p in resolved if lid in (p.get("laws") or [])]
        cited_open = [p for p in open_preds if lid in (p.get("laws") or [])]
        scores = [brier(p["probability"], p["outcome"]) for p in cited_resolved]
        mean = sum(scores) / len(scores) if scores else None
        rows.append({
            "id": lid,
            "title": law.get("title", ""),
            "status": law.get("status", ""),
            "confidence": law.get("confidence", ""),
            "n_resolved": len(cited_resolved),
            "n_open": len(cited_open),
            "mean_brier": mean,
            "grade": grade(mean) if mean is not None else "no-data",
        })
    return rows, resolved, open_preds


def render(rows, resolved, open_preds) -> str:
    lines = [
        "# SCOREBOARD",
        "",
        f"自動生成: `make score` / 生成日: {date.today().isoformat()}",
        "",
        "Brier = (確率 − 結果)²。0 が完璧、0.25 がコイン投げ。",
        "`falsification-pressure` の法則は confidence を下げ、kill condition を再確認せよ。",
        "",
        "## 法則の成績",
        "",
        "| 法則 | status | confidence | 解決済み | オープン | 平均Brier | 判定 |",
        "|------|--------|-----------|---------|---------|-----------|------|",
    ]
    for r in rows:
        mb = f"{r['mean_brier']:.3f}" if r["mean_brier"] is not None else "—"
        lines.append(
            f"| {r['id']} {r['title']} | {r['status']} | {r['confidence']} "
            f"| {r['n_resolved']} | {r['n_open']} | {mb} | {r['grade']} |")

    lines += ["", "## 解決済みの賭け", ""]
    if resolved:
        lines += ["| 予測 | 確率 | 結果 | Brier | 引用法則 |",
                  "|------|------|------|-------|----------|"]
        for p in sorted(resolved, key=lambda x: x["id"]):
            b = brier(p["probability"], p["outcome"])
            o = "true" if p["outcome"] else "false"
            lines.append(f"| {p['id']} {p.get('title','')} | {p['probability']} "
                         f"| {o} | {b:.3f} | {', '.join(p.get('laws') or [])} |")
    else:
        lines.append("（まだない）")

    lines += ["", "## オープンポジション（未解決の賭け）", ""]
    if open_preds:
        lines += ["| 予測 | 確率 | 期限 | 引用法則 |",
                  "|------|------|------|----------|"]
        today = date.today().isoformat()
        for p in sorted(open_preds, key=lambda x: str(x.get("horizon", ""))):
            overdue = " **OVERDUE**" if str(p.get("horizon", "")) < today else ""
            lines.append(f"| {p['id']} {p.get('title','')} | {p['probability']} "
                         f"| {p.get('horizon','')}{overdue} | {', '.join(p.get('laws') or [])} |")
    else:
        lines.append("（まだない — 予測のない法則体系は死んでいる。予測を作れ）")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    laws, predictions = load_docs()
    rows, resolved, open_preds = score(laws, predictions)
    SCOREBOARD.parent.mkdir(exist_ok=True)
    SCOREBOARD.write_text(render(rows, resolved, open_preds), encoding="utf-8")
    print(f"採点完了: 解決済み {len(resolved)} 件 / オープン {len(open_preds)} 件")
    print(f"→ {SCOREBOARD.relative_to(ROOT)}")
    for r in rows:
        if r["grade"] == "falsification-pressure":
            print(f"  ⚠ {r['id']} に反証圧力 (平均Brier {r['mean_brier']:.3f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
