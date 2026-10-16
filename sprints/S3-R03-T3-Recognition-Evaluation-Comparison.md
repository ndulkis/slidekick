# SlideKick — Sprint 3 Recognition Evaluation Comparison

**Owner:** R03 — Full-Stack Recognition & Data Steward

**Work item:** S3-R03-T3 · Midterm recognition metrics, confusion matrix, latency snapshot, and limitations

**Protocol recorded in both datasets:** `s3-r03-t2-lifecycle-030-v1`

**Status:** Analysis ready for team review · Controller/UI pull-request review not evidenced by these datasets

## 1. Executive summary

Two complete **39-trial** manual camera evaluations were compared: an **earlier session with stronger natural light** (as reported by the tester) and a **later session with less favorable lighting**. Both contain 13 motion scenarios tested three times. Neither dataset shows duplicate gesture events or wrong-direction swipe classifications; the meaningful failure mode is a missed gesture (`no_gesture`).

**Critical comparability warning:** The six slow-swipe trials have **different ground-truth labels** across the files. In the earlier, brighter-light file, they are labeled `swipe_left`/`swipe_right` (an expected detection). In the later file, they are labeled `no_gesture` (an expected rejection). The recognizer rejects slow swipes in **both** runs. As a result, direct comparison of the recorded `correct` fields is misleading; this report presents both the *as-recorded* and *consistently relabeled* results.

| Measure | Earlier, brighter light | Later, less favorable light |
|---|---:|---:|
| Trials | 39 | 39 |
| **As-recorded trial accuracy** | **33/39 (84.6%)** | **32/39 (82.1%)** |
| **Normalized trial accuracy** | **39/39 (100.0%)** | **32/39 (82.1%)** |
| Correct detected swipes (of 24 intended regular/fast/twist swipe trials) | 24/24 | 17/24 |
| All intended negatives, normalized (15) | 15/15 | 15/15 |
| Natural wrist-twist swipes detected | **6/6** | **0/6** |
| Wrong-direction classifications | 0 | 0 |
| Duplicate event predictions | 0 | 0 |
| Hand-landmark detection across processed frames | 4541/4726 (96.1%) | 4624/4739 (97.6%) |
| Natural wrist-twist hand-landmark detection | 725/726 (99.9%) | 655/730 (89.7%) |

For the **normalized accuracy**, slow swipes are expected to be rejected. Under this interpretation, the earlier run outperforms the later run by **17.9 percentage points**. This is an *observational association* with different lighting, not proof of lighting causality: operator movement, pose, camera exposure, background, distance, and trial order were not independently controlled.

## 2. Evaluation method and scoring rules

- **Data:** Two supplied newline-delimited JSON (`.jsonl`) session exports with complete `t1-001` through `t13-003` sample IDs, 39 unique trials each, and matching protocol identifiers.
- **Classes:** `swipe_left`, `swipe_right`, `no_gesture`. For classification, a null/missing `predicted_gesture` is counted as `no_gesture`.
- **Trial accuracy:** Number of trials whose predicted class equals the expected class, divided by 39. Counts come from saved predictions and labels rather than from inferred hand motion.
- **Duplicate event count:** `sum(max(prediction_count - 1, 0))` per run; every trial emitted either zero or one event.
- **Normalization:** The six `slow_swipe_left` and `slow_swipe_right` trials are treated as **intended negative controls** (`no_gesture`) in **both*** datasets, consistent with the later dataset and the stability-filtering intent. The raw JSONL files are not modified. If project requirements instead state slow swipes should be accepted, use the as-recorded label convention for that specific scenario and explicitly revise acceptance criteria.
- **Tracking detection rate:** Sum of `tracking_metrics.hand_detected_frames` divided by sum of `tracking_metrics.total_processed_frames`; this is a **frame-weighted tracking statistic**, not gesture-recognition accuracy.
- **Timing:** For trials with a gesture event, `prediction_time - sample_start_time`. These time stamps measure **time from recording start to an event**, including any wait before movement. They are **not** measured algorithm inference time, physical gesture-onset latency, slide transition latency, or guaranteed responsiveness.

## 3. Confusion matrices — recorded ground truth

### Run A — Earlier, brighter natural lighting (as recorded)

| Actual / Predicted | Swipe left | Swipe right | No gesture |
|---|---:|---:|---:|
| Swipe Left | 12 | 0 | 3 |
| Swipe Right | 0 | 12 | 3 |
| No Gesture | 0 | 0 | 9 |

Original labels produce 33/39 accuracy. The six undetected slow-swipe cases contribute all six errors; no natural-twist gestures are missed.

### Run B — Later, less favorable lighting (as recorded)

| Actual / Predicted | Swipe left | Swipe right | No gesture |
|---|---:|---:|---:|
| Swipe Left | 9 | 0 | 3 |
| Swipe Right | 0 | 8 | 4 |
| No Gesture | 0 | 0 | 15 |

Original labels produce 32/39 accuracy. Seven positive swipe trials are missed, including six natural-twist trials and one left-hand rightward swipe.

## 4. Confusion matrices — harmonized acceptance criterion

In these matrices, **slow swipes are negative controls in both runs**; no recorded prediction is changed.

### Run A — Brighter lighting, normalized

| Actual / Predicted | Swipe left | Swipe right | No gesture |
|---|---:|---:|---:|
| Swipe Left | 12 | 0 | 0 |
| Swipe Right | 0 | 12 | 0 |
| No Gesture | 0 | 0 | 15 |

### Run B — Later lighting, normalized

| Actual / Predicted | Swipe left | Swipe right | No gesture |
|---|---:|---:|---:|
| Swipe Left | 9 | 0 | 3 |
| Swipe Right | 0 | 8 | 4 |
| No Gesture | 0 | 0 | 15 |

**Interpretation:** In the brighter-light run, all 24 intended normal/fast/twist swipes are recognized and all 15 intended negatives rejected. In the later run, the system still rejects all 15 negatives, but misses seven of 24 intended swipes. The evidence suggests a tracking/recognition robustness issue under the later conditions, concentrated in wrist rotation.

## 5. Scenario-by-scenario results

Each scenario was tested three times per session. Counts indicate emitted gesture events, regardless of whether detection was expected. Slow swipes and other negative controls should have **0/3** detections.

| Scenario | Earlier detections | Later detections |
|---|---:|---:|
| `right_hand_swipe_right` | 3/3 | 3/3 |
| `left_hand_swipe_left` | 3/3 | 3/3 |
| `fast_swipe_right` | 3/3 | 3/3 |
| `slow_swipe_left` | 0/3 | 0/3 |
| `vertical_movement` | 0/3 | 0/3 |
| `left_hand_swipe_right` | 3/3 | 2/3 |
| `natural_twist_swipe_left` | 3/3 | 0/3 |
| `slow_swipe_right` | 0/3 | 0/3 |
| `short_horizontal_movement` | 0/3 | 0/3 |
| `right_hand_swipe_left` | 3/3 | 3/3 |
| `natural_twist_swipe_right` | 3/3 | 0/3 |
| `fast_swipe_left` | 3/3 | 3/3 |
| `casual_reposition` | 0/3 | 0/3 |

**Wrist-twist-specific tracking:** In brighter conditions, landmark detection was 99.9% across recorded wrist-twist frames; in the later run it was 89.7%. The later natural-twist trials also show longer contiguous tracking interruptions. This provides a plausible link between wrist rotation, temporary tracking loss, and missed recognition; more controlled tests are needed to distinguish tracking failures from the recognizer's movement thresholds.

## 6. Timing and system stability

| Measurement | Earlier, brighter | Later |
|---|---:|---:|
| Predicted events | 24 | 17 |
| Mean trial-start-to-event time | 794 ms | 861 ms |
| Median trial-start-to-event time | 735 ms | 875 ms |
| Observed range | 546–1562 ms | 656–1016 ms |
| Duplicate predictions | 0 | 0 |
| Wrong-direction predictions | 0 | 0 |
| Frame-weighted hand detection | 96.1% | 97.6% |

**Do not interpret the later run's longer mean as evidence of slower processing.** Only successful detections have event timestamps, samples begin before the actual gesture may start, and the two sets of successful scenarios differ. A valid end-to-end latency benchmark requires a reliable physical gesture-onset timestamp and the slide-controller command/transition timestamp.

The later run has a *slightly higher overall frame tracking rate* even though wrist-twist tracking and recognition are worse. Overall tracking averages can conceal motion-specific failures; per-scenario tracking matters more here.

## 7. Limitations and threats to validity

1. **Limited sample and operator diversity:** Only 39 controlled trials per session, three repetitions per scenario. Findings do not establish general-user accuracy or statistical significance.

2. **Different labeling of slow swipes:** Six trials have conflicting acceptance criteria, corrected analytically but still requiring one documented team decision for future datasets.

3. **Lighting is self-reported, not calibrated:** No measured lux/exposure values, fixed camera settings, or paired randomized design. No causal conclusion about lighting can be made.

4. **Hand visibility vs. usable landmark trajectory:** Overall hand detection is not sufficient to ensure reliable recognition through wrist twists or temporary occlusion.

5. **Non-gesture event latency:** Recording-start timestamps cannot identify actual gesture onset or measure end-to-end PowerPoint/Keynote action timing.

6. **Manual scripted movement:** Accuracy may differ with real presenters' motion variability, hand sizes, clothing, background, camera models, and Mac/Windows behavior.

7. **No downstream integration measurement:** These JSONL files do not test command mapping, UI feedback, presentation compatibility, or background resource use.

## 8. Recommended follow-up and midterm acceptance checks

- **Agree on slow-swipe semantics.** Treat them as explicit negative controls if the design intentionally rejects motions longer than the maximum swipe duration; encode expected labels consistently in the evaluation script and protocol documentation.
- **Investigate natural wrist twists.** Capture debug overlays with hand tracking continuity, landmark 9 horizontal displacement, direction consistency, axis purity, gesture state, and rejection reason; compare under repeatable lighting and fixed camera placement.
- **Add controlled lighting tests.** Repeat the same randomized scenario sequence in measured lighting conditions while fixing camera exposure, distance, and background; avoid attributing differences to lighting until confounders are reduced.
- **Protect stability improvements.** Add deterministic recorded/synthetic-frame regression tests for single emission, cooldown/rearm, and rejection of slow/off-axis motion in pytest/CI.
- **Measure true latency separately.** Instrument recognizer event time, controller command dispatch, and observed slide response, and define a reproducible gesture-onset criterion.
- **Review teammate changes.** Examine available controller/command-mapping and UI PRs for canonical gesture-event compatibility, background behavior, calibration handoff, and diagnostic feedback. **PR review is not demonstrated by these uploaded datasets and remains an open T3 deliverable.**

## 9. T3 evidence and remaining status

| Deliverable | Evidence/status |
|---|---|
| Labeled evaluation samples | **Available:** two complete 39-trial datasets; 78 observations total |
| Accuracy and confusion snapshot | **Completed:** raw and normalized matrices above |
| Tracking stability snapshot | **Completed:** weighted frame detection and wrist-twist breakdown |
| Timing snapshot | **Completed with qualification:** recording-start-to-event, not end-to-end latency |
| Explicit limitations and recommended next steps | **Completed** |
| Command/controller pull request review | **Pending confirmation/review** |
| UI pull request review | **Pending confirmation/review** |

