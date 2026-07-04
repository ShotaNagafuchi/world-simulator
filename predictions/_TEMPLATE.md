---
id: PRED-YYYY-NNN
title: 予測の一行タイトル
statement: "第三者が真偽判定できる一文。曖昧語禁止"
probability: 0.5
laws: [LAW-XXX]
signals: []
horizon: 2028-12-31
resolution_criteria: "何をどう観測したら true / false と判定するか"
status: open
outcome: null
resolved_on: null
resolution_note: null
---

# 賭けの内容

statement の背景。どの法則のどの適用からこの確率が出たか。

# この予測が外れるとしたら

最も可能性の高い外れ方を事前に書く（外れたときの学習を最大化するため）。

# 掟

- 法則を引用しない予測は登録できない（勘は予測ではない）
- 解決したら predictions/resolved/ へ移動し、status / outcome / resolved_on / resolution_note を埋めて `make score`
