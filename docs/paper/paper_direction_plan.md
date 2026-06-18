# Paper Direction Plan

**Project**: Microseismic Precursor Identification and Rockburst Hazard Warning at the Hongyang Coal Mine
**Status**: Direction-fixing phase (no experimental results yet)
**Date**: 2026-05-26

---

## 1. Recommended Paper Direction

A **physics-informed machine-learning (PIML) framework** that combines the existing W/y empirical rockburst criterion with a data-driven classifier to identify microseismic precursors of high-energy / hazardous events at the Hongyang coal mine.

The paper deliberately positions itself as a **dataset + method** contribution, not a pure-ML paper. The W/y criterion is treated as prior physical knowledge that is injected into the ML pipeline as engineered features and as an interpretable baseline, rather than being replaced.

## 2. Target Venue Type

- **Primary target**: SCI / EI journal in mining engineering, rock mechanics, or geo-hazard early warning.
  - Candidate venue families (for orientation only — confirm specific journal later):
    *International Journal of Rock Mechanics and Mining Sciences*; *Engineering Geology*; *Tunnelling and Underground Space Technology*; *Rock Mechanics and Rock Engineering*; *Process Safety and Environmental Protection*; *Safety Science*.
- **Secondary target**: a Chinese EI / 中文核心 venue covering engineering integration (e.g., *岩石力学与工程学报*, *煤炭学报*, *中国矿业大学学报*).
- **Tertiary fallback**: a Data Descriptor style submission for HMRP-2026 alone, if the method side is not yet mature.

## 3. Core Research Question

> Can the identification of microseismic precursors of high-energy / rockburst events at the Hongyang coal mine be improved by combining the empirical W/y physical criterion with data-driven machine learning, while remaining interpretable enough for on-site engineering use?

## 4. Main Claim

A **physics-informed ML classifier**, trained on a curated single-mine microseismic dataset (HMRP-2026) with W/y-derived features, can produce hazard probability estimates that are (i) better aligned with observed precursor patterns than the W threshold alone, and (ii) interpretable through SHAP analysis, *subject to validation on a single mine and to the label-definition assumptions stated in the paper*.

Scope of the claim is intentionally narrow: single mine, candidate framework, conditional on external validation.

## 5. Contributions

1. **HMRP-2026 dataset construction**: an analytical microseismic precursor dataset compiled from Hongyang monitoring records, including event-level descriptors, time-window aggregates, spatial context, and W/y physical-criterion features.
2. **Physics-informed hybrid framework**: a unified pipeline that uses W/y values and their underlying physical parameters as features and as a transparent baseline, alongside a gradient-boosting classifier.
3. **Interpretability and engineering-decision view**: SHAP-based attribution plus a planned 2-D decision chart that maps W-axis × ML-probability-axis to discrete hazard tiers, intended to plug into the existing Hongyang warning platform.

## 6. Dataset Definition (HMRP-2026)

- **Source records**: `资料/数据源/1208微震事件（清洗后）.xlsx`, `资料/数据源/红阳矿区微震预警判据.xls`, mine geometry from `红阳三矿集成工程图10.28.dxf`.
- **Per-event fields**: timestamp; source coordinates (X, Y, Z); energy E; magnitude M; location precision; nearest-fault distance; distance to active face; seam membership.
- **Temporal-window features** (rolling windows of 6 / 12 / 24 / 72 h prior to each event):
  event count, cumulative energy, b-value, energy index EI, apparent stress σ_app, migration velocity.
- **Spatial context**: clustering density (e.g., ST-DBSCAN), local seismicity rate.
- **Physical-criterion features**: W value from `compute_wi/main.cpp`; y value from `资料/y值计算.py`; the input physical parameters (ρ, E, λ, ξ, etc.) as raw channels.
- **Engineering parameters**: daily face advance, mining depth, mining stage.
- **Labels**: see § 7.

## 7. Label Definition Options

| ID | Definition | Pros | Cons |
|----|-----------|------|------|
| L1 | Binary energy threshold on the event itself (E ≥ E*) | Objective, easy to reproduce | "High energy" ≠ "hazardous"; provides no early-warning value |
| L2 | Triggered by current W/y threshold being exceeded | Directly comparable to baseline | Tautological if the model also sees W as input |
| L3 | Precursor label: event e is labelled 1 if a high-energy event occurs in (e.t, e.t + T] | Carries genuine engineering value; matches "early warning" framing | Sensitive to T; class imbalance |
| L4 | On-site expert annotation of warning / response | Highest quality | Likely sparse and inconsistent in the available records |

## 8. Recommended Final Label Strategy

- **Primary label**: **L3** with T ∈ {6, 12, 24, 72} h reported as a sensitivity study; the headline configuration is the T value that maximises positive-class support while remaining engineering-meaningful (to be selected after EDA, [TODO: choose final T after dataset audit]).
- **Auxiliary labels**: L1 (energy threshold) and L2 (W exceedance) used only for cross-checking and as comparison baselines, never as the headline target.
- **L4** treated as an external validation source if any expert-annotated records can be recovered from the existing warning logs; otherwise excluded.

## 9. Methodological Pipeline

```
Raw microseismic records
        │
        ▼
Cleaning, deduplication, coordinate alignment
        │
        ▼
Per-event feature extraction  ─── W/y physical criterion computation
        │                                  │
        ▼                                  ▼
Temporal-window aggregation         Physical parameter channels
        │
        ▼
Spatial-context features (faults, face, clusters)
        │
        ▼
Label assignment (L3 with multiple T)
        │
        ▼
Train / validation / test split (chronological)
        │
        ├──► Baseline A: W / y threshold rule
        ├──► Baseline B: ML-only (XGBoost / LightGBM)
        └──► Proposed:   Physics-Informed Hybrid (ML + W/y features + physical-parameter channels)
                │
                ▼
        SHAP attribution + decision chart (W-axis × ML-prob)
```

## 10. Baselines

- **B1 — Pure W threshold**: existing implementation in `compute_wi/main.cpp`, reproduced on HMRP-2026.
- **B2 — Pure y threshold**: from `资料/y值计算.py`.
- **B3 — ML without physics features**: gradient-boosting on event + window + spatial features, with W/y excluded.
- **B4 — Logistic regression / shallow MLP**: simple ML reference.
- **Proposed — Physics-informed hybrid**: gradient-boosting on the full feature stack including W, y, and their physical input parameters; optional W-as-prior soft constraint via monotonic constraints on the W feature.

## 11. Evaluation Metrics

- **Classification**: Precision, Recall, F1, ROC-AUC, PR-AUC.
- **Engineering metrics**: False Alarm Rate (FAR), Missed Alarm Rate (MAR), lead-time distribution for true positives.
- **Calibration**: reliability diagram, Brier score.
- **Uncertainty**: optional Conformal Prediction set sizes (planned, not required for the first submission).
- **Imbalance-aware**: macro-F1 and PR-AUC are the headline numbers; raw accuracy is reported only for transparency.

## 12. Planned Figures

See [figure_table_plan.md](figure_table_plan.md) for full captions. Headline figures:

1. Overall framework diagram.
2. Dataset construction pipeline.
3. Feature groups + W/y integration schematic.
4. Model comparison (placeholder, populated after experiments).
5. SHAP interpretation (placeholder).
6. Engineering decision chart (placeholder).

## 13. Planned Tables

1. Dataset statistics.
2. Feature list with categorisation (event / temporal / spatial / physical).
3. Baseline vs. proposed performance.
4. Ablation study.

## 14. Risks and Limitations

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| Positive-class count too small under L3 | High | Run dataset audit before fixing T; report per-T sensitivity; consider semi-supervised augmentation |
| Single-mine generalisation is weak | Certain | Frame the paper as a case study; explicitly disclaim cross-mine generalisation |
| W formula parameters (ρ, E, λ, ξ) are heuristic | Medium | Document the provenance of each constant; mark as a known limitation; investigate Idea D (data-driven re-calibration) in a follow-up paper |
| Label leakage between window features and L3 label | High if careless | Strict chronological split; window features must use only data strictly prior to e.t |
| SHAP misread as causal | Medium | State explicitly that SHAP shows attribution, not causation |
| Engineering integration claim is overreach | Medium | Show a *prototype* integration, not a deployed system |

## 15. What Must Be Verified Before Submission

- [ ] Number of positive samples under each T setting is reported and non-trivial.
- [ ] W formula parameter values are traceable to source documents or marked as adopted from prior work.
- [ ] Train / test split is strictly chronological with no peeking.
- [ ] All numerical claims in Results have corresponding code and run logs.
- [ ] References list contains only verified, real publications — no model-fabricated citations.
- [ ] Limitations section honestly states single-mine scope.
- [ ] Any statement using the words "real-time", "always", "guarantee" is removed.
- [ ] Data-sharing statement is consistent with what mine management approves.
- [ ] Ethics / safety statement: the model is decision-support, not a replacement for site experts.

---

*This plan is the contract for the rest of the paper. Every experimental claim in `paper_draft_with_placeholders.md` must trace back to a row in `experiment_todo_list.md`.*
