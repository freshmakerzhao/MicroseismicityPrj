# Handoff for the Next AI Assistant

> Read this file first. It is the entry point for any subsequent AI session — Claude Code, Gemini, ChatGPT, or another — picking up the paper work after the direction-fixing session of 2026-05-26.

---

## 1. Project background

This repository hosts a Vue + ECharts visualisation platform for the Hongyang coal mine's intelligent perception and warning system. Alongside the platform, the user is preparing an academic paper that will use the same microseismic data and the same W/y physical-judgement criterion the platform already implements.

Key project assets relevant to the paper:

- `docs/微震危险性判别_研究规划.md` — the original Chinese research plan (the user's primary spec).
- `资料/数据源/1208微震事件（清洗后）.xlsx` — the cleaned microseismic event catalogue.
- `资料/数据源/红阳矿区微震预警判据.xls` — the W/y criterion specification used at the mine.
- `compute_wi/main.cpp` — the existing C++ implementation of the W computation.
- `资料/y值计算.py` — the existing Python implementation of the y computation.
- `红阳三矿集成工程图10.28.dxf` — mine geometry, parsed by `database/inspect_dxf.py`.
- Visualisation pages: `src/views/page5.vue`, `page6.vue`, `page8.vue`, and possibly a new `page9.vue` for the paper's engineering-integration prototype.

## 2. Current paper direction

A **physics-informed machine-learning framework** for microseismic precursor identification and rockburst hazard warning at the Hongyang coal mine. The W/y empirical criterion is treated as a prior to be embedded as feature channels in a gradient-boosting classifier, **not** as a baseline to be displaced.

Recommended title (chosen during this session):
**A Physics-Informed Machine-Learning Framework for Microseismic Precursor Identification and Rockburst Hazard Warning in the Hongyang Coal Mine.**

Target venue type: SCI / EI journal in mining engineering, rock mechanics, or geo-hazard early warning. See `paper_direction_plan.md` § 2 for candidate venue families.

## 3. Core thesis

Combining the W/y empirical criterion with a data-driven classifier — through feature-level injection, monotonic constraints, SHAP attribution, and a 2-D decision chart — produces a hazard identifier that is **simultaneously more flexible than the W threshold rule and more interpretable than a black-box ML classifier**, *subject to single-mine scope and to the precursor-label assumption*.

## 4. Dataset plan — HMRP-2026

Per-event rows with four feature groups: event-level (timestamp, location, energy, magnitude), temporal-window aggregates over τ ∈ {6, 12, 24, 72} h, spatial-context (fault distance, face distance, cluster density), and W/y-derived (W value, y value, plus the physical parameters that feed them).

Headline label: **L3 precursor label** — event e is labelled positive iff a high-energy event occurs in (e.t, e.t + T] for the chosen T.

Splits are **strictly chronological**. Any temporal leakage between window features and labels invalidates every downstream number.

Full schema, label options, and split design are in `paper_direction_plan.md`.

## 5. Method plan

Three model families share one evaluation protocol:
- **B1 / B2** — W threshold and y threshold (reproduced as-is, no fitting).
- **B3** — gradient-boosting (XGBoost / LightGBM) on event + window + spatial features only.
- **Proposed** — same model class on the full feature stack including W, y, and the physical-parameter channels; optionally with a monotonic constraint on W.

Imbalance handling compared across class-weighted loss, focal loss, SMOTE. SHAP attribution on the proposed model. A 2-D decision chart on the W-axis × ML-probability plane is the engineering artefact.

## 6. Current missing experiments

Nothing has been run yet. The complete to-do list is in `experiment_todo_list.md`. The blocking items (priority H) before any honest result can be reported are:

1. **T1** — Build HMRP-2026 v0.1.
2. **T2** — Generate L1/L2/L3 labels for all candidate T values and audit positive counts.
3. **T3** — Define and verify the chronological train / val / test split (with a leakage check).
4. **T4, T5, T6** — W/y threshold baseline, ML-only baseline, physics-informed hybrid.
5. **T10** — SHAP analysis.
6. **T11** — Engineering decision chart.
7. **T16** — Data-sharing statement, aligned with what site management approves.

## 7. Do-not-invent rules

These rules apply to every future AI session working on this paper. They are non-negotiable.

- **No fabricated numbers.** No precision, recall, F1, AUC, FAR, MAR, or any other metric may be written into the draft except after running the corresponding experiment. Until then, use `[TODO: ...]`.
- **No fabricated citations.** Never invent author names, DOIs, journal names, years, or page ranges. Use `[TODO: Add references on ...]` and let the human verify against real sources.
- **No fabricated dataset statistics.** Event counts, positive-class proportions, time spans must come from running T1 + T2.
- **No fabricated formulas.** Re-derive W, y, b-value, EI, and σ_app from the source code (`compute_wi/main.cpp`, `资料/y值计算.py`) or from the original papers before writing them down. Do not transcribe from memory.
- **No quiet replacement of placeholders.** If you fill a placeholder, leave a comment trail (a commit message, a session log entry) noting which experiment produced the number.
- **No overreach on generalisation.** The framework is a single-mine case study. Any claim broader than that must be explicitly hedged and tied to a follow-up validation experiment.
- **No closed-loop autonomy claims.** The framework is decision support; it does not replace site experts. Do not write text that implies otherwise.

## 8. Key terminology

| Term | Definition in this project |
|------|---------------------------|
| Microseismic event | A discrete stress-release event recorded by the mine's seismic array. |
| Rockburst | A violent failure of rock mass, often associated with deep mining; the hazard the paper is ultimately about. |
| Precursor | An earlier microseismic event that statistically precedes a high-energy / hazardous event within a chosen time window. |
| W (criterion) | The site's existing empirical scalar combining stress, stiffness, and dissipation, used as a threshold rule. |
| y (criterion) | A companion empirical scalar; same role as W in the existing platform. |
| HMRP-2026 | The dataset compiled in this paper — Hongyang Microseismic Rockburst Precursor dataset, 2026 edition. |
| L1 / L2 / L3 / L4 | Four candidate label definitions; L3 (precursor label) is the headline choice. |
| Physics-informed ML | An ML model that takes physically-derived quantities as features and may impose physical constraints (e.g., monotonicity) on its predictions. |
| SHAP | Shapley-additive feature attribution; used here as a post-hoc interpretability layer, not as a causal certification. |
| Decision chart | The 2-D engineering visualisation on the W-axis × predicted-probability plane, partitioned into hazard tiers. |
| Lead time | For a true-positive prediction, the elapsed time between the predicted event and the eventual high-energy event. |

## 9. Recommended next prompts

When the next AI session starts, the user can use one of these directly. Each prompt is self-contained.

**Prompt A — execute T1 (dataset build).**
> Read `docs/paper/paper_direction_plan.md` § 6 and `docs/paper/experiment_todo_list.md` T1. Then build HMRP-2026 v0.1 from `资料/数据源/1208微震事件（清洗后）.xlsx`, the W/y source files, and the parsed mine geometry. Produce a versioned dataset file, a data dictionary, and a one-page audit report with per-stage retained-event counts. Do not invent numbers; report exactly what the data yields. Then update Table 1 and Figure 2 in `docs/paper/paper_draft_with_placeholders.md`.

**Prompt B — execute T2 (label generation and audit).**
> Read `docs/paper/experiment_todo_list.md` T2. Generate L1, L2, and L3 labels for T ∈ {6, 12, 24, 72} h on HMRP-2026 v0.1. Report per-T positive counts, temporal distribution of positives, and a recommendation for the headline T value. Output a label-audit notebook and update the dataset section of the draft with the real counts.

**Prompt C — execute T4 + T5 + T6 (baselines and main model).**
> Read `docs/paper/experiment_todo_list.md` T4, T5, T6 and `paper_direction_plan.md` § 10. Train the W/y threshold baseline, the ML-only baseline (gradient boosting, no physics features), and the physics-informed hybrid model. Evaluate all three on the chronological test split fixed in T3. Report Precision, Recall, F1, ROC-AUC, PR-AUC, FAR, MAR, and lead-time distribution. Then fill the corresponding `[TODO: ...]` placeholders in `paper_draft_with_placeholders.md` § 6 with the actual numbers; leave a commit message recording which experiment produced which value.

**Prompt D — execute T10 (SHAP analysis).**
> Read `docs/paper/experiment_todo_list.md` T10. On the trained physics-informed hybrid model from T6, compute SHAP values on the test split. Produce the summary plot, the W-dependence plot, and three representative force plots. Add the figures to the paper, write the SHAP subsection in § 6.7, and explicitly state that SHAP shows attribution, not causation.

**Prompt E — build the engineering decision chart (T11) and integration prototype (T15).**
> Read `docs/paper/experiment_todo_list.md` T11 and T15. Build the 2-D decision chart on the W-axis × predicted-probability plane using validation-split predictions; calibrate tier boundaries and overlay test-set events. Then add a probability-overlay layer to one of `src/views/page5.vue` / `page6.vue` / `page8.vue`, or a new `page9.vue`, that visualises the hybrid model's hazard probability on the mine geometry. Capture screenshots and add them to § 7 of the draft.

**Prompt F — citation pass.**
> Walk through `docs/paper/paper_draft_with_placeholders.md` and replace every `[TODO: Add references on ...]` placeholder with real, verified citations. For each citation, record the DOI, the venue, and the year. Do not invent any reference; if you cannot find a suitable real source, leave the placeholder in place and report it.

## 10. Files generated in this session (2026-05-26)

All under `docs/paper/`:

- `paper_direction_plan.md` — the contract: direction, dataset, labels, methods, risks, pre-submission checklist.
- `paper_draft_with_placeholders.md` — the English working draft, with every unfinished item marked `[TODO: ...]`.
- `experiment_todo_list.md` — sixteen experiments, each with purpose, inputs, outputs, the figure / table it produces, and a priority tag.
- `figure_table_plan.md` — six figures and four tables, with placeholder captions and required-data notes.
- `handoff_for_next_ai.md` — this file.

The user explicitly did *not* invoke the full ARS automated pipeline in this session. Future sessions should respect the same boundary: produce structure and placeholders, never fabricated results.
