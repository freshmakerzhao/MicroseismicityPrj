# Experiment To-Do List

> Priority encoding: **H** = blocking for submission; **M** = required for a competitive submission; **L** = nice-to-have / follow-up work.

---

## T1 — Dataset construction (HMRP-2026 v0.1)

- **Task**: Compile the analytical dataset from raw monitoring records.
- **Purpose**: Provide the substrate for every downstream experiment.
- **Required input**: `资料/数据源/1208微震事件（清洗后）.xlsx`; mine geometry from `红阳三矿集成工程图10.28.dxf`; W parameters from `compute_wi/main.cpp`; y parameters from `资料/y值计算.py`.
- **Expected output**: A versioned `hmrp_2026_v0.1.parquet` (or `.csv`) with the schema defined in `paper_direction_plan.md` § 6, plus a one-page data dictionary.
- **Figure / table produced**: Table 1 (dataset statistics); Figure 2 (dataset construction pipeline schematic).
- **Priority**: **H**.

## T2 — Label definition and audit

- **Task**: Generate L1, L2, and L3 labels for T ∈ {6, 12, 24, 72} h; report per-T positive counts; choose the headline T.
- **Purpose**: Confirm that labels are non-trivial before any model is trained; fix the headline configuration.
- **Required input**: HMRP-2026 v0.1 from T1.
- **Expected output**: A label-audit notebook reporting positive/negative counts, temporal distribution of positives, and the chosen headline T with justification.
- **Figure / table produced**: A label-audit table (not necessarily in the paper) and a per-T positive-count line plot (likely in supplementary).
- **Priority**: **H**. Without this, every later number is meaningless.

## T3 — Train / validation / test split

- **Task**: Build the chronological split and verify there is no temporal leakage between window features and labels.
- **Purpose**: Fix the evaluation protocol once and for all.
- **Required input**: HMRP-2026 v0.1 with labels (T1 + T2).
- **Expected output**: Saved split indices; an automated leakage check that fails if any test-event window touches training data.
- **Figure / table produced**: A small table reporting split sizes and date boundaries.
- **Priority**: **H**.

## T4 — W/y threshold baseline

- **Task**: Reproduce the existing W and y threshold rules on HMRP-2026 and evaluate them on the chronological test split.
- **Purpose**: Establish the operational baseline the paper claims to improve over.
- **Required input**: T1, T2, T3; the existing W/y thresholds used at the mine.
- **Expected output**: Precision, recall, F1, FAR, MAR, ROC curve, PR curve for each threshold rule.
- **Figure / table produced**: Table 3 (baseline comparison) — W and y rows; ROC/PR overlays in Figure 4.
- **Priority**: **H**.

## T5 — ML-only baseline (no physics features)

- **Task**: Train a gradient-boosting classifier (XGBoost or LightGBM) on event + window + spatial features only.
- **Purpose**: Isolate the contribution of the physics features in the hybrid model.
- **Required input**: T1, T2, T3.
- **Expected output**: A trained model artefact, the test-set metric report, and the validation-set hyperparameter log.
- **Figure / table produced**: Table 3 (ML-only row); Figure 4 (ML-only ROC and PR curves).
- **Priority**: **H**.

## T6 — Physics-informed hybrid model

- **Task**: Train the gradient-boosting classifier on the full feature stack, including W, y, and the physical-parameter channels. Optionally include the monotonic-W variant.
- **Purpose**: The principal model of the paper.
- **Required input**: T1, T2, T3.
- **Expected output**: Trained model artefact; test-set metrics; calibration diagram; lead-time distribution for true positives.
- **Figure / table produced**: Table 3 (hybrid row); Figure 4 (hybrid ROC and PR curves); calibration plot.
- **Priority**: **H**.

## T7 — Imbalanced-class handling comparison

- **Task**: Compare class-weighted loss, focal loss, and SMOTE on the hybrid model under the headline T.
- **Purpose**: Justify the choice of imbalance strategy used in the headline configuration.
- **Required input**: T6 setup.
- **Expected output**: A small table of metrics for the three strategies; identification of the headline strategy.
- **Figure / table produced**: A row block in Table 3 or a separate supplementary table.
- **Priority**: **M**.

## T8 — Sensitivity analysis for the precursor window T

- **Task**: Re-train the hybrid model for T ∈ {6, 12, 24, 72} h; report metrics and lead-time statistics for each.
- **Purpose**: Show that headline numbers do not silently depend on a single arbitrary choice of T.
- **Required input**: T1, T2, T3, T6.
- **Expected output**: A per-T metric table and an accompanying figure.
- **Figure / table produced**: A figure in the body or in supplementary; values feed Table 3 footnotes.
- **Priority**: **M**.

## T9 — Ablation study

- **Task**: Remove, one at a time, (a) W feature, (b) all physics-derived features, (c) spatial-context features, (d) temporal-window features; report metrics for each ablation.
- **Purpose**: Identify which feature group drives the hybrid model's behaviour.
- **Required input**: T6.
- **Expected output**: An ablation table.
- **Figure / table produced**: Table 4 (ablation study).
- **Priority**: **M**.

## T10 — SHAP interpretability analysis

- **Task**: Compute SHAP values on the test split for the hybrid model; produce the summary plot, the W-dependence plot, and three representative force plots (true positive, false positive, false negative).
- **Purpose**: Provide the interpretability layer that supports the "physics-informed" positioning.
- **Required input**: T6.
- **Expected output**: Three figures plus a short commentary on whether the W-dependence direction matches the physical expectation.
- **Figure / table produced**: Figure 5 (SHAP interpretation).
- **Priority**: **H**.

## T11 — Engineering decision chart

- **Task**: Calibrate tier boundaries on the W-axis × ML-probability plane using the validation split; visualise the chart and overlay test-set events.
- **Purpose**: Deliver the engineering artefact that the paper's title and § 7 promise.
- **Required input**: T6, optionally T8.
- **Expected output**: A 2-D decision chart with explicit tier boundaries and per-tier FAR/MAR.
- **Figure / table produced**: Figure 6 (engineering decision chart).
- **Priority**: **H**.

## T12 — Confidence-interval estimation

- **Task**: Bootstrap (or DeLong, for ROC-AUC) confidence intervals on every headline metric.
- **Purpose**: Honest uncertainty reporting under small positive-class counts.
- **Required input**: T4, T5, T6.
- **Expected output**: Confidence intervals added to Table 3.
- **Figure / table produced**: Updated Table 3 with CI columns.
- **Priority**: **M**.

## T13 — Robustness check

- **Task**: Re-train the hybrid model with at least three random seeds and three alternative hyperparameter settings; report variance across seeds.
- **Purpose**: Verify that the headline gain is not a single-run artefact.
- **Required input**: T6.
- **Expected output**: A small variance summary added to Table 3 or a supplementary table.
- **Figure / table produced**: Supplementary table.
- **Priority**: **M**.

## T14 — Cross-mine external validation (follow-up)

- **Task**: If any additional mine catalogue becomes available, evaluate the trained hybrid model on it without re-training.
- **Purpose**: Probe generalisation beyond Hongyang.
- **Required input**: A second-mine catalogue with compatible fields.
- **Expected output**: A short transfer-evaluation table.
- **Figure / table produced**: Optional supplementary or follow-up paper.
- **Priority**: **L**. Out of scope for the first submission; named here so the discussion section can promise it.

## T15 — Engineering integration prototype

- **Task**: Integrate the hybrid model's hazard-probability output as an overlay layer in the existing visualisation platform (`page5`, `page6`, `page8`, or a new `page9`).
- **Purpose**: Substantiate the engineering-implications section with a concrete prototype.
- **Required input**: T6 model artefact and a stable inference endpoint.
- **Expected output**: A screenshot or screen capture of the integrated view; a description of the data path from raw event to displayed probability.
- **Figure / table produced**: A figure for § 7 (engineering implications).
- **Priority**: **M**.

## T16 — Data-sharing and ethics statements

- **Task**: Confirm with site management what portion of HMRP-2026 can be released; draft the data-sharing statement and the ethics statement accordingly.
- **Purpose**: Compliance and reproducibility framing.
- **Required input**: Communication with mine management.
- **Expected output**: A short paragraph for the manuscript and a corresponding repository README section.
- **Figure / table produced**: None.
- **Priority**: **H** before submission.

---

## Recommended execution order

1. T1 → T2 → T3 (dataset foundation, must precede everything else).
2. T4 → T5 → T6 (baselines and main model).
3. T10, T11 in parallel with T7, T8, T9 (interpretability, decision chart, ablations).
4. T12, T13 (uncertainty and robustness).
5. T15, T16 (engineering and compliance).
6. T14 left as an honest follow-up.
