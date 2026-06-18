# Paper Draft (with Placeholders)

> **Status**: Working draft, direction-fixing phase. All experimental results, statistics, figures, tables, and citations are placeholders. **Do not treat any number, AUC, F1, or finding in this document as real.** Anything that must be produced before submission is marked `[TODO: ...]`.

---

## Title — Three Candidates

1. **A Physics-Informed Machine-Learning Framework for Microseismic Precursor Identification and Rockburst Hazard Warning in the Hongyang Coal Mine** ← **recommended**
2. Hybrid W-Criterion and Machine-Learning Identification of Microseismic Rockburst Precursors: A Case Study of the Hongyang Coal Mine
3. HMRP-2026: An Analytical Microseismic Dataset and Physics-Informed Hazard Identification Framework for Deep Coal Mines

The recommended title is preferred because it (i) signals the physics-informed positioning up front, (ii) names the application (rockburst warning) rather than a generic ML task, and (iii) constrains scope to a single mine, which is honest about the dataset.

---

## Abstract

Microseismic monitoring is the dominant in-situ technique for anticipating rockburst hazards in deep coal mines, yet the operational decision rules in use today rely heavily on hand-tuned energy thresholds and empirical physical criteria such as the W and y indices. These criteria are interpretable but rigid: their parameters are calibrated from a small number of historical cases, and they cannot exploit the rich temporal and spatial structure recorded by modern microseismic arrays. Purely data-driven machine-learning approaches address the second limitation but introduce their own problems — opaque decision boundaries, fragility under class imbalance, and weak alignment with the physical reasoning that on-site engineers trust. This paper proposes a physics-informed machine-learning framework that treats the W/y criterion not as a competitor to be beaten but as a prior to be embedded. We compile the Hongyang Microseismic Rockburst Precursor dataset (HMRP-2026) from monitoring records of the Hongyang coal mine, derive event-level, time-window, and spatial-context features, and inject the W and y values and their underlying physical parameters as additional feature channels into a gradient-boosting classifier. The framework is evaluated against (i) the existing W and y threshold rules and (ii) a data-driven baseline without physics features. SHAP attribution is used to expose which physical and statistical features drive each prediction, and a two-dimensional decision chart on the W-probability plane is proposed for engineering deployment. [TODO: Insert headline quantitative findings — precision, recall, F1, PR-AUC for each model and the relative improvement of the hybrid model.] [TODO: Insert lead-time statistics for true-positive predictions.] The framework is intended as decision support layered on top of, not as a replacement for, the existing Hongyang warning platform, and its claims are explicitly conditional on validation at other mines.

---

## Keywords

Microseismic monitoring; rockburst warning; physics-informed machine learning; coal mine safety; hazard identification; SHAP; W/y criterion.

---

## 1. Introduction

Rockburst events in deep coal mines remain among the most consequential and least-controlled hazards in underground mining. Microseismic monitoring, deployed widely since the 1990s, provides a continuous record of stress-release events that precede, accompany, and follow such hazards, and has become a primary input to mine-scale early warning systems. [TODO: Add references on microseismic rockburst monitoring history and Chinese coal mine practice.]

The decision rules in current operational use generally fall into two families. The first family applies energy or magnitude thresholds directly to microseismic events: any event whose released energy exceeds a calibrated level is flagged as potentially hazardous. The second family applies empirical physical criteria, of which the W and y indices used at the Hongyang coal mine are representative. Such criteria integrate stress, stiffness, depth, and energy-release parameters into a single scalar, compared against a fixed threshold. Both families are valued by site engineers for their transparency: a triggered alarm is a triggered threshold, and the reasoning can be reconstructed from a small set of numbers. They are also limited in three concrete ways. First, the thresholds are calibrated from a small set of historical cases and rarely re-tuned as the mining face advances. Second, the criteria collapse rich temporal and spatial information — the b-value evolution, energy-rate trends, spatial clustering near active faults — into a point statistic, discarding precursor patterns that span hours to days. Third, the underlying physical parameters (rock density, Young's modulus, lateral stress coefficient, dissipation coefficient, etc.) are treated as fixed constants even where the geological setting varies significantly along the working face.

Machine-learning approaches, especially gradient-boosted decision trees and neural sequence models, can in principle absorb this richer signal. A growing literature applies such methods to microseismic precursor identification, rockburst prediction, and related geo-hazard forecasting tasks. [TODO: Add representative references on machine learning for microseismic rockburst prediction.] These approaches typically improve raw classification scores on the datasets they are evaluated on, but they introduce risks of their own: predictions become opaque to the engineers who must act on them; class imbalance — hazardous events are rare by definition — biases models towards trivial majority predictions; and the disregard for established physical criteria makes the result difficult to defend in a safety-critical setting.

This paper takes the position that the W/y physical criterion is best treated not as a baseline to be displaced but as a prior to be embedded. We construct a single-mine analytical dataset, HMRP-2026, from microseismic records of the Hongyang coal mine, and we use the W and y values, together with their underlying physical parameters, as feature channels in a gradient-boosting classifier. The model is evaluated against the W-threshold and y-threshold rules currently used at the mine, and against a data-driven model that has no access to the physical features. We use SHAP attribution to expose which features — physical or statistical — drive each prediction, and we propose a two-dimensional decision chart on the W-axis × predicted-probability plane that can be integrated into the existing mine warning platform.

We make three contributions:

1. **HMRP-2026**, an analytical microseismic precursor dataset compiled from Hongyang monitoring records, with event-level, time-window, spatial-context, and W/y-derived features, and with precursor labels defined over multiple time horizons.
2. **A physics-informed hybrid identification framework** that combines the W/y empirical criterion with a gradient-boosting classifier, evaluated against pure-threshold and pure-ML baselines on HMRP-2026.
3. **An interpretability and engineering-integration layer**, comprising SHAP-based feature attribution and a 2-D decision chart designed to be deployed alongside the existing Hongyang warning platform.

The scope of the contribution is bounded. The dataset comes from a single mine, the labels rest on the precursor-window assumption discussed in § 3, and the framework is positioned as decision support rather than a closed-loop controller. Cross-mine generalisation is left to follow-up work.

---

## 2. Related Work

### 2.1 Microseismic monitoring and rockburst warning

[TODO: Add representative references on microseismic monitoring systems, network design, and operational rockburst warning practice in Chinese coal mines.] Prior work has established standard event-level descriptors (location, magnitude, energy, apparent stress) and aggregate indicators (event rate, cumulative energy, b-value, energy index) as the typical inputs to warning systems. The remaining open questions concern how these indicators should be combined and how the combination should be calibrated against site-specific data.

### 2.2 Empirical and physics-based hazard criteria

The W index and related stiffness-based criteria are widely used in Chinese mining practice to encode the local energy-release potential. [TODO: Add references on the W criterion derivation, on the y index, and on related empirical indicators such as the Russenes index, the elastic strain energy index Wet, and the burst-proneness classification used in Chinese standards.] These criteria are interpretable but inflexible; their parameters are typically calibrated from a limited number of laboratory and case-history measurements and are not adjusted as conditions evolve.

### 2.3 Machine learning for mine hazard prediction

[TODO: Add references on supervised classification, sequence modelling, and clustering applied to microseismic data; on gradient-boosting and tree-ensemble methods in geo-hazard contexts; and on imbalanced learning techniques relevant to rare-event prediction.] Reported performance varies widely and is difficult to compare across studies because of inconsistent label definitions, inconsistent splits, and limited reporting of false-alarm and missed-alarm rates.

### 2.4 Interpretable and physics-informed learning

[TODO: Add references on physics-informed neural networks, on physics-guided feature engineering, on SHAP and other attribution methods, and on the application of interpretable ML in safety-critical engineering settings.] Most existing work in mining hazard prediction is either purely empirical or purely data-driven; the physics-informed middle ground is comparatively underexplored. This paper contributes to that middle ground for the specific case of rockburst precursor identification.

---

## 3. Dataset Construction — HMRP-2026

### 3.1 Concept

HMRP-2026 is an analytical, event-keyed dataset compiled from the operational microseismic records of the Hongyang coal mine. Each row corresponds to a single microseismic event and carries (i) the event's own attributes, (ii) aggregate descriptors of the seismic environment in the preceding time window, (iii) the spatial context of the event with respect to the active mining face and known geological structures, and (iv) the W and y physical-criterion values, together with their underlying physical parameters.

### 3.2 Source records

The primary source is `资料/数据源/1208微震事件（清洗后）.xlsx`, containing the cleaned event catalogue. Physical criteria are computed from `资料/数据源/红阳矿区微震预警判据.xls` and the W-computation code in `compute_wi/main.cpp` and `资料/y值计算.py`. Mine geometry, used for spatial-context features, is parsed from `红阳三矿集成工程图10.28.dxf` via `database/inspect_dxf.py`.

### 3.3 Event-level features

For each event we record timestamp, source coordinates (X, Y, Z), released energy E, magnitude M, location precision, and seam membership.

### 3.4 Temporal-window features

For each candidate window length τ ∈ {6, 12, 24, 72} h ending at the event's timestamp, we compute event count, cumulative released energy, b-value, energy index EI, apparent stress σ_app, and source-migration velocity. Window features use only events strictly prior to the labelled event; no future information is allowed to leak into the feature vector.

### 3.5 Spatial-context features

Distance to the nearest mapped fault, distance to the active working face, and local seismicity density derived from a spatio-temporal clustering procedure (candidate: ST-DBSCAN, [TODO: confirm clustering choice]).

### 3.6 W/y physical-criterion features

The W value and the y value as computed by the existing site code are recorded for every event. Their underlying physical parameters — rock density ρ, Young's modulus E_rock, lateral stress coefficient λ, dissipation coefficient ξ, and depth — are stored as separate channels so that the ML model can re-weight them rather than relying only on the scalar W. [TODO: Cross-check the parameter conventions used in `compute_wi/main.cpp` against the W formula reported in the original derivation and document any deviations.]

### 3.7 Label definition

The headline label is the **precursor label L3**: an event e is labelled positive if and only if at least one high-energy event with E ≥ E* occurs in the time interval (e.t, e.t + T]. The threshold E* and the precursor window T are reported as design parameters; the sensitivity of results to T ∈ {6, 12, 24, 72} h is reported as a dedicated experiment (§ 5). For comparison and as auxiliary information, the energy-threshold label L1 and the W-exceedance label L2 are also recorded.

### 3.8 Data cleaning

Duplicate events, events with location precision below the array's nominal resolution, and events outside the mine footprint are removed. Time stamps are normalised to a single timezone. [TODO: Insert the exact cleaning rules and the number of events retained at each stage.]

### 3.9 Data split

Splits are **strictly chronological**: the earliest portion is used for training, the middle portion for validation and hyperparameter selection, and the most recent portion as a held-out test set. No event in the test set may have a window feature that overlaps in time with any event in the training set. [TODO: Insert exact split ratios and the date boundaries.]

### 3.10 Class imbalance

Under any meaningful L3 setting the positive class is expected to be small relative to the negative class. We report the per-window positive count explicitly and treat imbalance handling as a methodological component rather than as a hidden preprocessing step (§ 4.5).

### 3.11 Dataset statistics

[TODO: Insert dataset statistics — total events, retained events after cleaning, positive count per T setting, energy distribution, spatial coverage, time span.]

---

## 4. Method

### 4.1 Overall framework

The proposed framework is a three-stage pipeline: (1) per-event feature construction as in § 3; (2) classification by one of three model families — the W/y threshold rule, the data-only ML model, or the physics-informed hybrid; (3) post-hoc interpretation through SHAP attribution and a 2-D decision chart. The three model families share the same evaluation protocol and the same chronological data split. **Figure 1** illustrates the framework; see [figure_table_plan.md](figure_table_plan.md).

### 4.2 W/y physical-criterion baseline

The W threshold rule labels an event as hazardous if W ≥ W*. The y threshold rule is analogous on the y index. Threshold values are taken from the existing site convention and reported alongside the results. [TODO: Document W* and y* values used; confirm with mine engineers.] No fitting is performed for this baseline — it is reproduced as the rule currently in operational use.

### 4.3 Data-driven ML model

A gradient-boosted decision-tree classifier is trained on the event-level, temporal-window, and spatial-context features, without access to W, y, or their underlying physical parameters. Candidate libraries: XGBoost or LightGBM. Hyperparameters are tuned on the validation split by random search. [TODO: Insert search range and selected hyperparameters.]

### 4.4 Physics-informed hybrid model

The hybrid model uses the full feature stack, including W, y, and the physical-parameter channels. Optionally, a monotonic constraint is imposed on the W feature so that, all else being equal, a larger W cannot decrease the predicted hazard probability — this preserves the qualitative physical relationship while still allowing the model to learn data-driven corrections. [TODO: Confirm whether the monotonic-constraint variant is reported as the main configuration or as an ablation.]

The hybrid model is the principal contribution of the paper.

### 4.5 Imbalanced-class handling

Three strategies are compared: (i) class-weighted loss, (ii) focal loss, (iii) synthetic minority oversampling (SMOTE) on the training split only. All three are evaluated under the same chronological protocol; no resampling is performed on the validation or test split.

### 4.6 SHAP interpretability

After training, SHAP values are computed on the test split. We report (i) a global summary plot showing the marginal contribution of each feature group, (ii) a dependence plot for the W feature to confirm that its contribution direction is consistent with the physical expectation, and (iii) per-event force plots for selected high-probability and false-alarm cases.

### 4.7 Engineering decision chart

For deployment, we propose a 2-D decision chart on the W-axis × ML-probability-axis. The plane is partitioned into discrete hazard tiers, and the partition lines are calibrated on the validation split so that each tier corresponds to a target false-alarm / missed-alarm trade-off. The chart is the artefact intended to be embedded in the existing Hongyang warning platform.

### 4.8 Formal notation

[TODO: When the formulas for W, y, b-value, EI, and σ_app are written out, cross-check the symbols and unit conventions against `compute_wi/main.cpp`, `资料/y值计算.py`, and the original derivations. Do not transcribe formulas from memory.]

---

## 5. Experiments

### 5.1 Experimental setup

All models are trained on the chronological split defined in § 3.9. Random seeds are fixed and reported. Computational environment, library versions, and runtime are recorded for reproducibility. [TODO: Insert environment specification.]

### 5.2 Baselines

B1: W threshold; B2: y threshold; B3: ML without W/y features; B4: logistic regression on the full feature stack as a linear reference. Proposed: physics-informed hybrid.

### 5.3 Metrics

Precision, Recall, F1, ROC-AUC, PR-AUC, FAR, MAR, lead-time distribution for true positives, Brier score for calibration.

### 5.4 Evaluation protocol

Each model is fit on the training split, model selection is performed on the validation split using PR-AUC, and the held-out test split is touched exactly once per model configuration. The chronological order is preserved end-to-end.

### 5.5 Ablation study

Ablations remove, in turn: (a) the W feature; (b) all physics-derived features (W, y, and the physical-parameter channels); (c) the spatial-context features; (d) the temporal-window features. Each ablation isolates the contribution of one feature group to the hybrid model.

### 5.6 Sensitivity analysis for the precursor window T

The same hybrid configuration is re-trained for T ∈ {6, 12, 24, 72} h. We report per-T metrics and per-T positive-class counts so that readers can assess how much the headline numbers depend on the choice of T.

### 5.7 Imbalanced classification handling

The three imbalance strategies (class weight, focal loss, SMOTE) are compared on the hybrid model under the headline T value.

### 5.8 Interpretability analysis

The SHAP summary, the SHAP dependence on W, and selected force plots are presented in § 6 (Results). The aim is to confirm that the model's reliance on W is qualitatively consistent with the physical expectation, and to surface which non-physical features the model has discovered.

---

## 6. Results and Discussion

> The results subsections below are scaffolds. They will be populated after the experiments defined in § 5 and in [experiment_todo_list.md](experiment_todo_list.md) are executed. **No numerical claims appear here.**

### 6.1 Baseline performance

[TODO: Report W criterion baseline performance — precision, recall, F1, FAR, MAR — on the test split.]
[TODO: Report y criterion baseline performance.]
[TODO: Comment on the operating point of each threshold rule relative to the ROC and PR curves.]

### 6.2 Data-driven ML performance

[TODO: Report ML-only model performance.]
[TODO: Compare against the threshold baselines and discuss whether the improvement, if any, is concentrated in precision or in recall.]

### 6.3 Physics-informed hybrid performance

[TODO: Report physics-informed hybrid performance.]
[TODO: Quantify the absolute and relative improvement over the ML-only model and over the W threshold rule.]
[TODO: Insert ROC-AUC and PR-AUC comparison figure.]
[TODO: Insert confusion matrix.]

### 6.4 Ablation results

[TODO: Insert ablation table; comment on which feature group contributes most.]

### 6.5 Sensitivity to precursor window T

[TODO: Insert per-T metrics table; comment on monotonicity of performance with respect to T and on the engineering implications for warning lead time.]

### 6.6 Imbalance-handling comparison

[TODO: Report the three imbalance strategies side-by-side; identify the configuration adopted as the headline.]

### 6.7 SHAP interpretation

[TODO: Insert SHAP summary plot.]
[TODO: Insert SHAP dependence plot for the W feature; comment on direction-consistency with the physical expectation.]
[TODO: Insert representative force plots for one true positive, one false positive, and one false negative case.]
[TODO: State explicitly that SHAP shows attribution, not causation.]

### 6.8 Engineering decision chart

[TODO: Insert the calibrated 2-D decision chart on the W-axis × ML-probability plane, with tier boundaries.]
[TODO: Report the FAR and MAR associated with each tier on the held-out test split.]

### 6.9 Discussion

After the experiments are completed, this section will discuss (i) whether the hybrid model's gains over the ML-only baseline are concentrated in the feature regimes where the W criterion already performs well or in the regimes where it does not, (ii) what the SHAP analysis suggests about which information channels the W formula currently fails to capture, and (iii) what the sensitivity-to-T analysis implies for the operational warning lead time. [TODO: Fill in once results exist; do not pre-write conclusions.]

---

## 7. Engineering Implications

The framework is designed to be layered onto the existing Hongyang intelligent perception and warning platform, not to replace it. Three integration points are anticipated.

**Dual-criterion warning.** The platform's existing W-based warning continues to operate unchanged. The ML-derived hazard probability is added as a second channel. An event raises an alert when either channel exceeds its operational threshold; the 2-D decision chart formalises the combination rule. This preserves the engineering interpretability of W while letting the ML channel pick up patterns the W formula misses.

**Hazard-probability layer in the visualisation.** Existing platform pages (`page5`, `page6`, `page8` or equivalents) currently display the W contour and the 3-D mine geometry. A planned new view — `page9` — overlays the ML hazard probability on top of these maps and animates the time evolution of hazardous zones. [TODO: Confirm with the frontend team which existing page is the appropriate host; add a screenshot once the prototype is implemented.]

**False-alarm / missed-alarm trade-off control.** Because the decision chart's tier boundaries are calibrated on validation data, the on-site engineer can choose an operating point that emphasises sensitivity (lower MAR, higher FAR) or specificity (lower FAR, higher MAR), depending on the production phase. The trade-off is explicit and reportable, not buried inside a single threshold.

These implications are positioned as engineering value, not as research claims. The framework provides a probability layer and a decision-chart artefact; whether and how it is deployed remains a site management decision.

---

## 8. Limitations

- **Single-mine scope.** HMRP-2026 is built from one mine. The framework's quantitative behaviour at other mines is unknown and cannot be inferred from the results reported here. External validation on at least one additional mine is required before any cross-site generalisation is claimed.
- **Label-definition uncertainty.** The L3 precursor label depends on the precursor window T and on the energy threshold E*. We report sensitivity to T, but the choice of E* itself is a design decision with no canonical answer. Results should be read with this assumption visible.
- **Class imbalance.** Hazardous events are rare. Even after imbalance handling, the absolute number of positive samples in the test split is small, and confidence intervals on the headline metrics will be correspondingly wide. [TODO: Report bootstrap or DeLong confidence intervals.]
- **Engineering-parameter coverage.** Mining-stage and face-advance information is not uniformly recorded across the catalogue. Where it is missing, the model is exposed to silent confounders.
- **Reproducibility under restricted data sharing.** If site management does not approve full release of HMRP-2026, the paper can publish only the schema and the code, which limits independent reproduction. The data-sharing statement will be aligned with what site management authorises. [TODO: Confirm data-sharing scope before submission.]
- **Decision support, not autonomous control.** The framework is intended to support — never to replace — site-expert judgement. It must not be deployed in a closed-loop configuration that issues automated production stops without human review.
- **SHAP is attribution, not causation.** SHAP exposes which features the model relies on; it does not certify that those features cause hazardous events. Causal claims require dedicated experimental designs that are out of scope for this paper.

---

## 9. Conclusion

This paper has set out a physics-informed machine-learning framework for microseismic precursor identification and rockburst hazard warning at the Hongyang coal mine. The contributions are an analytical single-mine dataset (HMRP-2026), a hybrid identification framework that treats the W/y empirical criterion as a feature-level prior rather than as a competitor, and an interpretability-plus-decision-chart layer aimed at engineering integration. The framework is positioned as decision support for the existing Hongyang warning platform, and its scope is intentionally limited to a single mine pending external validation. [TODO: After the experiments are completed, summarise the headline finding in one sentence — relative improvement of the hybrid model over the W threshold baseline and the ML-only baseline — and state the immediate next step (external validation on a second mine).]

---

## References

[TODO: Add references on microseismic rockburst monitoring history and Chinese coal mine practice.]
[TODO: Add references on the W criterion derivation, the y index, the Russenes index, Wet, and burst-proneness classification.]
[TODO: Add references on supervised classification, gradient boosting, and imbalanced learning in geo-hazard contexts.]
[TODO: Add references on physics-informed learning and on SHAP attribution.]
[TODO: Add references on engineering deployment of microseismic warning systems in Chinese coal mines.]

> All references must be verified against original sources before submission. Do not accept any auto-generated citation without checking the DOI, the venue, and the year.
