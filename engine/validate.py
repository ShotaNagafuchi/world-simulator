#!/usr/bin/env python3
"""スキーマ・参照整合性・期限の検証。

強制する掟（CLAUDE.md / LAW-000 に対応）:
- 法則: kill_conditions 必須（殺せない法則は法則ではない）
- 予測: 法則の引用必須（勘は予測ではない）、確率は (0,1)、期限・解決基準必須
- シグナル: 出典・信用クラス・期限必須。予測に未接続なら警告
- 世界線: 反世界（anti-thesis）分岐と決定的観測セクション必須
- 現在地 (state/): 更新周期必須。as_of + refresh_every_days を過ぎたら STALE 警告
- 歴史 (history/): 出典必須。腐らないので期限チェックはない
- 参照整合性: 存在しない LAW / SIG / PRED / WORLD への参照はエラー
- 期限: 期限切れの open 予測（OVERDUE）と腐敗したシグナルを警告

エラーがあれば exit 1。警告のみなら exit 0。
"""

import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from frontmatter import collect

ROOT = Path(__file__).parent.parent

LAW_STATUSES = {"active", "weakened", "falsified", "deprecated"}
SOURCE_CLASSES = {"S0", "S1", "S2", "S3"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

REQUIRED = {
    "law": {"id", "name", "title", "status", "confidence", "domains", "kill_conditions"},
    "case": {"id", "title", "period", "domains", "laws"},
    "signal": {"id", "title", "observed", "source_class", "trust", "source",
               "domains", "expires", "linked_laws", "linked_predictions"},
    "prediction": {"id", "title", "statement", "probability", "laws", "horizon",
                   "resolution_criteria", "status"},
    "simulation": {"id", "title", "domain", "horizon", "laws", "branches"},
    "state": {"id", "title", "domain", "as_of", "refresh_every_days",
              "linked_simulations"},
    "history": {"id", "title", "domains", "type", "sources"},
}


def is_date(v) -> bool:
    return isinstance(v, str) and bool(DATE_RE.match(v))


def main() -> int:
    errors, warnings = [], []

    def err(path, msg):
        errors.append(f"  ERROR {path.relative_to(ROOT)}: {msg}")

    def warn(path, msg):
        warnings.append(f"  WARN  {path.relative_to(ROOT)}: {msg}")

    docs = {}  # kind -> list[(path, fm)]
    for kind, subdir in [("law", "laws"), ("case", "cases"), ("signal", "signals"),
                         ("prediction", "predictions"), ("simulation", "simulations"),
                         ("state", "state"), ("history", "history")]:
        docs[kind] = []
        for path, fm, e in collect(ROOT / subdir):
            if e:
                err(path, e)
                continue
            missing = REQUIRED[kind] - fm.keys()
            if missing:
                err(path, f"必須フィールド欠落: {sorted(missing)}")
            docs[kind].append((path, fm))

    law_ids = {fm.get("id") for _, fm in docs["law"]}
    sig_ids = {fm.get("id") for _, fm in docs["signal"]}
    pred_ids = {fm.get("id") for _, fm in docs["prediction"]}
    case_ids = {fm.get("id") for _, fm in docs["case"]}
    sim_ids = {fm.get("id") for _, fm in docs["simulation"]}
    today = date.today().isoformat()

    # --- 法則 ---
    for path, fm in docs["law"]:
        if fm.get("status") not in LAW_STATUSES:
            err(path, f"status が不正: {fm.get('status')} (許可: {sorted(LAW_STATUSES)})")
        kc = fm.get("kill_conditions")
        if not kc:
            err(path, "kill_conditions が空。殺せない法則は法則ではない (LAW-000)")
        c = fm.get("confidence")
        if not isinstance(c, (int, float)) or not (0 <= c <= 1):
            err(path, f"confidence は 0-1 の数値: {c}")
        ec = fm.get("evidence_cases", [])
        for cid in ec or []:
            if cid not in case_ids:
                err(path, f"存在しない事例への参照: {cid}")
        if fm.get("id") != "LAW-000" and not ec:
            warn(path, "証拠事例 (evidence_cases) がない。証拠のない法則は弱い")

    # --- 事例 ---
    for path, fm in docs["case"]:
        for lid in fm.get("laws", []) or []:
            if lid not in law_ids:
                err(path, f"存在しない法則への参照: {lid}")

    # --- シグナル ---
    for path, fm in docs["signal"]:
        if fm.get("source_class") not in SOURCE_CLASSES:
            err(path, f"source_class が不正: {fm.get('source_class')}")
        if fm.get("source_class") == "S3":
            warn(path, "S3 (AI生成/伝聞) シグナル。原則禁止 — 本文に理由があるか確認せよ")
        if not is_date(fm.get("expires", "")):
            err(path, "expires が YYYY-MM-DD でない")
        elif fm["expires"] < today:
            warn(path, f"シグナル腐敗 (expires={fm['expires']})。予測未接続なら削除せよ")
        for lid in fm.get("linked_laws", []) or []:
            if lid not in law_ids:
                err(path, f"存在しない法則への参照: {lid}")
        for pid in fm.get("linked_predictions", []) or []:
            if pid not in pred_ids:
                err(path, f"存在しない予測への参照: {pid}")
        if not (fm.get("linked_predictions") or fm.get("linked_laws")):
            warn(path, "予測にも法則にも未接続。接続できないシグナルは追加しない掟")

    # --- 予測 ---
    for path, fm in docs["prediction"]:
        p = fm.get("probability")
        if not isinstance(p, (int, float)) or not (0 < p < 1):
            err(path, f"probability は 0 と 1 の間（両端を含まない）: {p}")
        if not fm.get("laws"):
            err(path, "法則を引用しない予測は登録できない（勘は予測ではない）")
        for lid in fm.get("laws", []) or []:
            if lid not in law_ids:
                err(path, f"存在しない法則への参照: {lid}")
        for sid in fm.get("signals", []) or []:
            if sid not in sig_ids:
                err(path, f"存在しないシグナルへの参照: {sid}")
        if not is_date(fm.get("horizon", "")):
            err(path, "horizon が YYYY-MM-DD でない")
        status = fm.get("status")
        in_resolved_dir = "resolved" in path.parts
        if status == "open":
            if in_resolved_dir:
                err(path, "status: open だが resolved/ にある")
            if is_date(fm.get("horizon", "")) and fm["horizon"] < today:
                warn(path, f"OVERDUE: 期限 {fm['horizon']} を過ぎている。解決せよ")
        elif status == "resolved":
            if not in_resolved_dir:
                err(path, "status: resolved だが open/ にある。resolved/ へ移動せよ")
            if fm.get("outcome") not in (True, False, "void"):
                err(path, f"resolved なのに outcome が不正: {fm.get('outcome')}")
            if not is_date(str(fm.get("resolved_on", ""))):
                err(path, "resolved なのに resolved_on がない")
            if not fm.get("resolution_note"):
                err(path, "resolved なのに resolution_note がない。学習なき解決は禁止")
        else:
            err(path, f"status が不正: {status} (open | resolved)")

    # --- シミュレーション ---
    for path, fm in docs["simulation"]:
        for lid in fm.get("laws", []) or []:
            if lid not in law_ids:
                err(path, f"存在しない法則への参照: {lid}")
        branches = fm.get("branches", []) or []
        if len(branches) < 2:
            err(path, "分岐が2未満。反世界 (anti-thesis) の分岐は必須")
        joined = " ".join(str(b) for b in branches)
        if "反世界" not in joined and "anti" not in joined.lower():
            err(path, "反世界 (anti-thesis) 分岐が見つからない。自己確証バイアスを構造で殺す掟")
        body = path.read_text(encoding="utf-8")
        if "決定的観測" not in body:
            err(path, "「決定的観測」セクションがない。何を観測すべきかを持たない世界線は更新できない")

    # --- 現在地 (state) ---
    for path, fm in docs["state"]:
        if not is_date(str(fm.get("as_of", ""))):
            err(path, "as_of が YYYY-MM-DD でない")
        days = fm.get("refresh_every_days")
        if not isinstance(days, int) or days <= 0:
            err(path, f"refresh_every_days は正の整数: {days}")
        elif is_date(str(fm.get("as_of", ""))):
            due = date.fromisoformat(fm["as_of"]) + timedelta(days=days)
            if due.isoformat() < today:
                warn(path, f"STALE: 最終更新 {fm['as_of']}、更新期限 {due.isoformat()} 超過。"
                           "決定的観測リストを巡回して更新せよ")
        for wid in fm.get("linked_simulations", []) or []:
            if wid not in sim_ids:
                err(path, f"存在しない世界線への参照: {wid}")

    # --- 歴史 (history) ---
    for path, fm in docs["history"]:
        if fm.get("type") not in ("timeline", "data-series", "record"):
            err(path, f"type が不正: {fm.get('type')} (timeline | data-series | record)")
        if not fm.get("sources"):
            err(path, "sources が空。出典のない歴史は伝聞である")

    print(f"検証対象: 法則 {len(docs['law'])} / 事例 {len(docs['case'])} / "
          f"歴史 {len(docs['history'])} / 現在地 {len(docs['state'])} / "
          f"シグナル {len(docs['signal'])} / 予測 {len(docs['prediction'])} / "
          f"世界線 {len(docs['simulation'])}")
    for w in warnings:
        print(w)
    for e in errors:
        print(e)
    if errors:
        print(f"\nNG: エラー {len(errors)} 件 / 警告 {len(warnings)} 件")
        return 1
    print(f"\nOK: エラー 0 件 / 警告 {len(warnings)} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
