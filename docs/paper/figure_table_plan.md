# Figure and Table Plan

> All captions below are placeholders for the manuscript. The numeric content must come from `experiment_todo_list.md`; never fill these figures from imagined results.

---

## Figures

### Figure 1 — Overall framework

- **Purpose**: One-glance view of the physics-informed hybrid pipeline; anchors the Methods section.
- **Required data**: None (schematic).
- **What it should show**: Three parallel branches — W/y threshold baseline, ML-only baseline, physics-informed hybrid — sharing the same feature-extraction front end and the same evaluation back end. Highlight the W/y feature injection arrow into the hybrid branch and the SHAP / decision-chart post-processing block.
- **Placeholder caption**:
  > **Fig. 1.** Overall framework of the proposed physics-informed identification pipeline for microseismic precursors. Per-event features, temporal-window aggregates, and spatial-context descriptors are extracted once and shared across three model branches: the W/y threshold baseline, the data-driven ML baseline, and the physics-informed hybrid model. Post-hoc SHAP attribution and the 2-D decision chart are applied to the hybrid branch.

### Figure 2 — Dataset construction pipeline

- **Purpose**: Show how raw monitoring records become HMRP-2026.
- **Required data**: Schematic; per-stage retained-event counts to be added once T1 runs.
- **What it should show**: Raw catalogue → cleaning → feature extraction (event / temporal / spatial / physical) → label assignment (L1, L2, L3 for multiple T) → chronological split. Funnel-style with per-stage counts.
- **Placeholder caption**:
  > **Fig. 2.** Construction of the HMRP-2026 dataset from operational microseismic records of the Hongyang coal mine. Per-stage event counts are reported above each block. [TODO: Insert per-stage counts after dataset cleaning.]

### Figure 3 — Feature groups and W/y physical-criterion integration

- **Purpose**: Make the physics-informed positioning visually concrete.
- **Required data**: Schematic; feature-group names from § 3 of the draft.
- **What it should show**: Four feature buckets — event-level, temporal-window, spatial-context, physical-criterion — feeding a single feature vector; the physical-criterion bucket is highlighted and annotated to emphasise its prior role.
- **Placeholder caption**:
  > **Fig. 3.** Feature groups used by the proposed framework. Event-level, temporal-window, and spatial-context features are derived from the microseismic catalogue and mine geometry; the W/y physical-criterion features and their underlying physical parameters are injected as an explicit prior into the hybrid model.

### Figure 4 — Model comparison results (placeholder)

- **Purpose**: Headline performance comparison across baselines and the proposed model.
- **Required data**: Test-split predictions from T4, T5, T6.
- **What it should show**: A pair of panels — left, ROC curves; right, precision–recall curves — for the W threshold, y threshold, ML-only model, and physics-informed hybrid. Each curve labelled with its AUC. Optionally, an inset confusion matrix for the hybrid model at its chosen operating point.
- **Placeholder caption**:
  > **Fig. 4.** Comparison of identification performance on the held-out test split. (a) ROC curves; (b) precision–recall curves for the W threshold, the y threshold, the ML-only baseline, and the physics-informed hybrid model. [TODO: Insert ROC-AUC and PR-AUC values once experiments T4–T6 are complete.]

### Figure 5 — SHAP interpretation (placeholder)

- **Purpose**: Demonstrate model interpretability and consistency of the W feature with physical expectation.
- **Required data**: SHAP values computed in T10.
- **What it should show**: (a) Global SHAP summary (beeswarm) of the top-N features; (b) SHAP dependence plot for the W feature; (c) three force plots — one true positive, one false positive, one false negative — chosen to illustrate the model's reasoning.
- **Placeholder caption**:
  > **Fig. 5.** SHAP-based interpretation of the physics-informed hybrid model. (a) Global summary of feature attribution; (b) dependence plot for the W feature, confirming direction-consistency with the physical expectation; (c) representative force plots for one true positive, one false positive, and one false negative case. [TODO: Insert SHAP plots once experiment T10 is complete.]

### Figure 6 — Engineering decision chart (placeholder)

- **Purpose**: Deliver the deployable artefact described in § 7.
- **Required data**: Validation-split predictions and W values from T6 + T11.
- **What it should show**: A 2-D plane with the W value on the x-axis and the model's predicted hazard probability on the y-axis; tier boundaries drawn as polylines; test-set events overlaid as coloured points (true positives, false positives, true negatives, false negatives); per-tier FAR/MAR annotated.
- **Placeholder caption**:
  > **Fig. 6.** Proposed engineering decision chart on the W-axis × predicted-probability plane. Tier boundaries are calibrated on the validation split and held fixed on the test split. Per-tier false-alarm and missed-alarm rates are annotated. [TODO: Insert calibrated chart and per-tier rates once experiment T11 is complete.]

---

## Tables

### Table 1 — Dataset statistics (placeholder)

- **Purpose**: Anchor the dataset section with concrete numbers.
- **Required data**: T1 + T2.
- **What it should show**: Total raw events; events retained after cleaning; positive count under L1 (energy threshold) and L3 with T ∈ {6, 12, 24, 72} h; time span; depth range; spatial extent.
- **Placeholder caption**:
  > **Table 1.** Summary statistics of the HMRP-2026 dataset. [TODO: Insert event counts, label distribution per T setting, time span, spatial extent.]

### Table 2 — Feature list

- **Purpose**: Make every feature visible and reviewable.
- **Required data**: Feature inventory from § 3 of the draft.
- **What it should show**: Feature name; category (event / temporal / spatial / physical); brief definition; unit; data source (catalogue field, derived formula, or external file).
- **Placeholder caption**:
  > **Table 2.** Feature inventory used in HMRP-2026. Categories indicate whether a feature is event-level, temporal-window-aggregated, spatial-context, or derived from the W/y physical criterion.

### Table 3 — Baseline comparison (placeholder)

- **Purpose**: Headline numerical comparison.
- **Required data**: T4, T5, T6, plus T7 and T12 once available.
- **What it should show**: Rows for W threshold, y threshold, logistic regression, ML-only, physics-informed hybrid (and optionally the monotonic-W hybrid). Columns for Precision, Recall, F1, ROC-AUC, PR-AUC, FAR, MAR, mean lead time. Bootstrap CIs in a secondary row block.
- **Placeholder caption**:
  > **Table 3.** Identification performance on the held-out test split. Confidence intervals are bootstrap-estimated. [TODO: Insert per-row metrics once experiments T4–T6, T12 are complete.]

### Table 4 — Ablation study (placeholder)

- **Purpose**: Attribute the hybrid model's gains to feature groups.
- **Required data**: T9.
- **What it should show**: Rows for the full hybrid model; minus W; minus all physics features; minus spatial-context; minus temporal-window. Same metric columns as Table 3 but trimmed to the headline metrics (F1, PR-AUC, FAR, MAR).
- **Placeholder caption**:
  > **Table 4.** Ablation of feature groups in the physics-informed hybrid model. Each row removes one feature group while leaving the rest unchanged. [TODO: Insert ablation metrics once experiment T9 is complete.]

---

## Notes on figure rendering

- All figures must use vector formats (PDF / SVG / EPS) for final submission; PNG only for placeholders during drafting.
- Colour choices must remain readable in greyscale; encode model identity by line style, not by colour alone.
- Every placeholder figure currently used in the draft should be replaced by a real artefact only after its corresponding experiment in `experiment_todo_list.md` has been executed and reviewed.
