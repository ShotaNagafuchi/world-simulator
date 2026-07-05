#!/usr/bin/env python3
"""観測すべき現象の導出と、シグナル-法則の命中判定。

法則の kill_conditions / 制約の unfreeze_conditions から
「何を観測すれば法則が更新されるか」のウォッチリストを導出し、
既存シグナルとの接続状況を分析する。

出力:
1. WATCHLIST: 各法則・制約ごとに「観測すべき現象」と接続シグナルの有無
2. BLIND SPOTS: kill_condition に対応するシグナルがゼロの法則（観測の死角）
3. COVERAGE: 法則ごとのシグナル接続数（観測カバレッジ）
4. ANOMALIES: 複数の法則に同時に接続するシグナル（法則間の相互作用の兆候）
5. UPDATE CANDIDATES: confidence が証拠と乖離している可能性のある法則
"""

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from frontmatter import collect

ROOT = Path(__file__).parent.parent


def main() -> int:
    laws: list[tuple[Path, dict]] = []
    constraints: list[tuple[Path, dict]] = []
    signals: list[tuple[Path, dict]] = []
    cases: list[tuple[Path, dict]] = []

    for path, fm, e in collect(ROOT / "laws"):
        if not e and fm:
            laws.append((path, fm))
    for path, fm, e in collect(ROOT / "constraints"):
        if not e and fm:
            constraints.append((path, fm))
    for path, fm, e in collect(ROOT / "signals"):
        if not e and fm:
            signals.append((path, fm))
    for path, fm, e in collect(ROOT / "cases"):
        if not e and fm:
            cases.append((path, fm))

    # --- シグナル→法則の接続マップ ---
    law_signals: dict[str, list[dict]] = defaultdict(list)
    for _, sfm in signals:
        for lid in sfm.get("linked_laws", []) or []:
            law_signals[lid].append(sfm)

    # --- 事例→法則の接続マップ ---
    law_cases: dict[str, list[dict]] = defaultdict(list)
    for _, cfm in cases:
        for lid in cfm.get("laws", []) or []:
            law_cases[lid].append(cfm)

    blind_spots: list[str] = []
    update_candidates: list[str] = []

    # ===== WATCHLIST: 法則 =====
    print("=" * 70)
    print("WATCHLIST: 法則の kill_conditions と観測状況")
    print("=" * 70)

    for path, fm in laws:
        law_id = fm.get("id", "?")
        if law_id == "LAW-000":
            continue
        title = fm.get("title", "")
        confidence = fm.get("confidence", "?")
        kill_conditions = fm.get("kill_conditions", []) or []
        evidence_cases = fm.get("evidence_cases", []) or []
        sigs = law_signals.get(law_id, [])

        print(f"\n{'─' * 60}")
        print(f"  {law_id}: {title}")
        print(f"  confidence: {confidence} | シグナル接続: {len(sigs)} | 証拠事例: {len(evidence_cases)}")

        if kill_conditions:
            print(f"  kill_conditions:")
            for i, kc in enumerate(kill_conditions, 1):
                print(f"    [{i}] {kc}")
        else:
            print(f"  ⚠ kill_conditions なし")

        if sigs:
            print(f"  接続シグナル:")
            for s in sigs:
                print(f"    - {s.get('id', '?')}: {s.get('title', '?')} "
                      f"(class={s.get('source_class', '?')}, trust={s.get('trust', '?')})")
        else:
            blind_spots.append(f"{law_id}: {title}")
            print(f"  ⚠ 接続シグナルなし（死角）")

        # --- confidence 妥当性チェック ---
        evidence_count = len(evidence_cases) + len(sigs)
        if isinstance(confidence, (int, float)):
            if confidence >= 0.8 and evidence_count <= 1:
                update_candidates.append(
                    f"{law_id}: confidence={confidence} だが証拠({evidence_count}件)が少ない → 過信？")
            elif confidence <= 0.5 and evidence_count >= 4:
                update_candidates.append(
                    f"{law_id}: confidence={confidence} だが証拠({evidence_count}件)が多い → 過小評価？")

    # ===== WATCHLIST: 制約 =====
    print(f"\n\n{'=' * 70}")
    print("WATCHLIST: 制約の unfreeze_conditions と観測状況")
    print("=" * 70)

    for path, fm in constraints:
        con_id = fm.get("id", "?")
        title = fm.get("title", "")
        layer = fm.get("layer", "?")
        status = fm.get("status", "?")
        unfreeze = fm.get("unfreeze_conditions", []) or []

        print(f"\n{'─' * 60}")
        print(f"  {con_id}: {title}")
        print(f"  layer: {layer} | status: {status}")

        if unfreeze:
            print(f"  unfreeze_conditions:")
            for i, uc in enumerate(unfreeze, 1):
                print(f"    [{i}] {uc}")

    # ===== BLIND SPOTS =====
    print(f"\n\n{'=' * 70}")
    print("BLIND SPOTS: シグナルが接続されていない法則（観測の死角）")
    print("=" * 70)

    if blind_spots:
        for bs in blind_spots:
            print(f"  ⚠ {bs}")
        print(f"\n  → これらの法則は現実からのフィードバックを受けていない。")
        print(f"    kill_conditions を観測できるシグナルを追加するか、")
        print(f"    観測不能なら法則の有用性を再検討する。")
    else:
        print(f"  ✓ 全法則にシグナルが接続されている")

    # ===== ANOMALIES: 法則間の交差 =====
    print(f"\n\n{'=' * 70}")
    print("ANOMALIES: 複数法則に同時接続するシグナル（相互作用の兆候）")
    print("=" * 70)

    for _, sfm in signals:
        linked = sfm.get("linked_laws", []) or []
        if len(linked) >= 2:
            print(f"  {sfm.get('id', '?')}: {sfm.get('title', '?')}")
            print(f"    → 接続法則: {', '.join(str(l) for l in linked)}")
            print(f"    → 法則間の関係を検証する機会")

    # ===== UPDATE CANDIDATES =====
    print(f"\n\n{'=' * 70}")
    print("UPDATE CANDIDATES: confidence と証拠の乖離")
    print("=" * 70)

    if update_candidates:
        for uc in update_candidates:
            print(f"  ? {uc}")
    else:
        print(f"  ✓ 明らかな乖離なし")

    # ===== SUMMARY =====
    print(f"\n\n{'=' * 70}")
    print("SUMMARY")
    print("=" * 70)
    total_laws = len([l for l in laws if l[1].get("id") != "LAW-000"])
    covered = total_laws - len(blind_spots)
    print(f"  法則: {total_laws} | シグナル接続あり: {covered} | 死角: {len(blind_spots)}")
    print(f"  制約: {len(constraints)} | シグナル: {len(signals)} | 事例: {len(cases)}")
    print(f"  confidence更新候補: {len(update_candidates)}")

    if blind_spots:
        print(f"\n  最優先アクション: 死角の法則にシグナルを接続する")

    return 0


if __name__ == "__main__":
    sys.exit(main())
