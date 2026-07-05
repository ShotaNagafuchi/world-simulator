#!/usr/bin/env python3
"""イノベーション機会の評価プロトコル。

全法則・全制約を順に適用し、どこで弾かれるかを表示する。
スコアカードの罠（高スコア→個別法則スキップ）を防ぐため、
全チェックを強制する。
"""

FILTERS = [
    {
        "id": "F1-必須行動",
        "question": "全員が頻繁にやる行動か？（週1回以上）",
        "kill": "特殊な人だけ or 年数回以下 → 市場が小さい",
        "law": "基本条件",
    },
    {
        "id": "F2-因果即時",
        "question": "結果が秒-分で分かるか？（成功/失敗が即座に判定可能）",
        "kill": "結果が週-年で判明 → CON-004でデータの堀が形成されない、CON-013で支払い意思なし",
        "law": "CON-004, CON-013",
    },
    {
        "id": "F3-痛み急性",
        "question": "「今すぐ解決しないと困る」痛みか？（慢性ではなく急性）",
        "kill": "あると便利だがなくても死なない → LAW-012でユーザーが払わない",
        "law": "LAW-012, CON-010, CON-013",
    },
    {
        "id": "F4-馬鹿描写",
        "question": "現在の動作を文字通り描写すると馬鹿げているか？",
        "kill": "描写しても合理的に見える → 摩擦が小さい、10倍改善の余地がない",
        "law": "CON-006（10倍必要）",
    },
    {
        "id": "F5-能力拡張",
        "question": "判断を代替するのではなく、新しい能力を与えるか？",
        "kill": "AIが代わりに判断する形 → CON-008で人間が拒絶する",
        "law": "CON-008",
    },
    {
        "id": "F6-サプライ得",
        "question": "サプライ側（相手方）は協力するインセンティブがあるか？",
        "kill": "サプライ側が損する（ロックイン弱化、価格競争激化）→ LAW-012で協力しない",
        "law": "LAW-012, CON-009",
    },
    {
        "id": "F7-ルーティング",
        "question": "A×Bの両面構造があるか？（両側がルーターを経由する必要がある）",
        "kill": "片面だけ → LAW-009でロックインが形成されない → ツール止まり",
        "law": "LAW-009",
    },
    {
        "id": "F8-低信頼開始",
        "question": "小さな賭けから始められるか？（最初の1回が低リスク）",
        "kill": "初回から高額/高リスク → CON-002とCON-010で採用されない",
        "law": "CON-002, CON-004, CON-010",
    },
    {
        "id": "F9-窓開き",
        "question": "この領域の決定的プレイヤーはまだいないか？",
        "kill": "既に独占者がいる → LAW-009で窓が閉じている",
        "law": "LAW-009",
    },
    {
        "id": "F10-別方法",
        "question": "既存の方法とは全く別のアプローチか？（改善ではなく構造変更）",
        "kill": "既存プロセスの高速化 → CON-008（自動化≠イノベーション）",
        "law": "CON-008",
    },
    {
        "id": "F11-ボトルネック",
        "question": "解消する摩擦はその行動の本当のボトルネックか？",
        "kill": "ボトルネックでない摩擦を解消 → LAW-007で産業は変わらない",
        "law": "LAW-007",
    },
]


def evaluate(name: str, description: str, answers: dict[str, bool | str]) -> None:
    """機会を全フィルターで評価し、結果を表示する。"""
    print(f"\n{'=' * 60}")
    print(f"  評価: {name}")
    print(f"  {description}")
    print(f"{'=' * 60}")

    passed = 0
    failed = 0
    for f in FILTERS:
        fid = f["id"]
        ans = answers.get(fid)
        if ans is True:
            print(f"  ✓ {fid}: {f['question']}")
            passed += 1
        elif ans is False:
            print(f"  ✕ {fid}: {f['question']}")
            print(f"    → KILL: {f['kill']}")
            print(f"    → 根拠: {f['law']}")
            failed += 1
        else:
            print(f"  ? {fid}: {f['question']}")
            print(f"    → 回答: {ans}")

    print(f"\n  結果: {passed} 通過 / {failed} 不通過 / {len(FILTERS) - passed - failed} 未判定")
    if failed == 0:
        print(f"  → ★★★ 全フィルター通過")
    elif failed <= 2:
        print(f"  → ★★ 条件付きで有望（不通過フィルターの克服方法を検討）")
    else:
        print(f"  → ✕ 構造的に困難")


def main():
    print("イノベーション機会の評価プロトコル")
    print(f"フィルター数: {len(FILTERS)}")
    print()
    for i, f in enumerate(FILTERS, 1):
        print(f"  {f['id']}: {f['question']}")
        print(f"    KILL条件: {f['kill']}")
        print(f"    根拠法則: {f['law']}")
        print()


if __name__ == "__main__":
    main()


