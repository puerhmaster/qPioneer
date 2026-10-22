"""Синтетический пример для кнопки «Загрузить пример» (96 лунок). Данные выдуманы, это не результаты эксперимента.

Раскладка: ACTB (референсный ген) — ряды A–B, SOX2 — C–D, PAX6 — E–F.
Верхний ряд пары — Control, нижний — Treated; колонки 1–3, 4–6, 7–9 — биологические повторы 1–3
(по 3 технических повтора), 10–12 в ряду Control — отрицательный контроль (вода, без Cp).
SOX2 в Treated выше примерно в 3 раза, PAX6 не меняется.

Запуск: python examples/make_demo.py  → examples/demo_96well.txt и examples/demo_96well_annotation.json
"""
import json
import random
from pathlib import Path

OUT = Path(__file__).parent
RUN = "Run1"
GENES = [  # ген, роль, ряды (Control, Treated), средний Cp (Control, Treated)
    ("ACTB", "reference gene", ("A", "B"), (18.0, 18.0)),
    ("SOX2", "target gene", ("C", "D"), (26.0, 24.4)),
    ("PAX6", "target gene", ("E", "F"), (28.0, 28.0)),
]
CONDITIONS = ("Control", "Treated")

rnd = random.Random(42)
lines = ["Experiment: qPioneer demo (synthetic data)", "Pos\tName\tCp"]
annotation = {}
for gene, role, rows, means in GENES:
    for cond, row, mean in zip(CONDITIONS, rows, means):
        for rep in range(3):
            bio = mean + rnd.gauss(0, 0.25)
            for k in range(3):
                well = f"{row}{rep * 3 + k + 1}"
                lines.append(f"{well}\t{gene} {cond} {rep + 1}\t{bio + rnd.gauss(0, 0.08):.2f}")
                annotation[well] = {"gene": gene, "role": role, "template": cond, "replicate": str(rep + 1), "run": RUN}
        if cond == "Control":
            for col in (10, 11, 12):
                well = f"{row}{col}"
                lines.append(f"{well}\t{gene} NTC\t")
                annotation[well] = {"gene": gene, "role": "negative control"}

(OUT / "demo_96well.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
(OUT / "demo_96well_annotation.json").write_text(json.dumps(annotation, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"{len(lines) - 2} лунок")
