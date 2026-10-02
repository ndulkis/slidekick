# SlideKick S2 Recognition Sample Analysis

## Dataset Overview

This report analyzes the supplied JSONL dataset containing **36 samples** collected across **12 rounds** (`t1` through `t12`). Each round contains one `swipe_right`, one `swipe_left`, and one `no_gesture` trial, giving **12 samples per condition**.

The recorded trial duration averaged **4.013 seconds**, which is consistent with the configured 4-second sample window.

## Overall Results

| Metric | Result |
|---|---:|
| Total trials | 36 |
| Correct trials | 32 |
| Overall accuracy | 88.9% |
| Intended swipe trials | 24 |
| Correct intended swipes | 22 |
| Swipe-trial recall | 91.7% |
| `no_gesture` trials | 12 |
| Correct rejections | 10 |
| False-positive trials | 2 |
| False-positive rate on `no_gesture` | 16.7% |
| Total gesture prediction events | 24 |
| Correct gesture events | 22 |
| Overall gesture-event precision | 91.7% |

The recognizer produced **32 correct outcomes out of 36 trials**, for an overall accuracy of **88.9%**.

## Confusion Matrix

| Expected \ Predicted | `swipe_right` | `swipe_left` | No prediction |
|---|---:|---:|---:|
| `swipe_right` | 12 | 0 | 0 |
| `swipe_left` | 0 | 10 | 2 |
| `no_gesture` | 2 | 0 | 10 |

There were **no wrong-direction classifications during intended swipe trials**. The two `swipe_left` failures were misses rather than being classified as `swipe_right`. Both false positives during `no_gesture` trials were classified as `swipe_right`.

## Per-Gesture Performance

| Gesture | Correct / Expected | Recall | Precision | F1 |
|---|---:|---:|---:|---:|
| `swipe_right` | 12 / 12 | 100.0% | 85.7% | 92.3% |
| `swipe_left` | 10 / 12 | 83.3% | 100.0% | 90.9% |

`swipe_right` was detected in all 12 intended right-swipe trials. Its precision is lower than its recall because two `no_gesture` trials also produced `swipe_right`.

`swipe_left` was correctly detected in 10 of 12 intended trials. No false `swipe_left` predictions occurred elsewhere in the dataset.

## Incorrect Trials

| Sample | Expected | Predicted | Confidence | Frames | Outcome |
|---|---|---|---:|---:|---|
| `t3-002` | `swipe_left` | `none` | — | 88 | Missed gesture |
| `t4-002` | `swipe_left` | `none` | — | 84 | Missed gesture |
| `t4-003` | `no_gesture` | `swipe_right` | 0.597 | 41 | False positive |
| `t7-003` | `no_gesture` | `swipe_right` | 0.621 | 113 | False positive |

The missed left swipes occurred in `t3-002` and `t4-002`. The false-positive negative trials were `t4-003` and `t7-003`, and both generated `swipe_right`.

## Confidence Analysis

For the **22 correct swipe detections**, confidence values were:

| Statistic | Value |
|---|---:|
| Mean | 0.696 |
| Median | 0.676 |
| Minimum | 0.557 |
| Maximum | 0.850 |

Average confidence by correctly detected gesture:

| Gesture | Mean confidence |
|---|---:|
| `swipe_right` | 0.708 |
| `swipe_left` | 0.682 |

The two false positives had confidences of **0.597** and **0.621**, averaging **0.609**.

This is important for tuning: the false positives were relatively low-confidence, but several legitimate swipe detections were also in the same general confidence range. Raising the confidence threshold alone could reduce false positives while also creating additional missed gestures, so threshold tuning should be evaluated with a new before/after dataset rather than changed from these results alone.

## Detection Delay and Latency

For correctly detected swipes, the raw **sample-to-prediction delay** was:

| Metric | All swipes | Right | Left |
|---|---:|---:|---:|
| Mean | 773 ms | 778 ms | 767 ms |
| Median | 781 ms | 781 ms | 774 ms |

This value is **not pure recognition latency** because sample recording begins before the tester necessarily begins moving.

As an exploratory offline estimate, movement onset was approximated from landmark 9. The estimate searched for the first three-frame window before prediction that accumulated at least **0.02 normalized x displacement** in the intended swipe direction. Using that heuristic:

| Estimated motion-to-detection latency | Result |
|---|---:|
| Mean | 253 ms |
| Median | 219 ms |
| Minimum | 156 ms |
| Maximum | 500 ms |
| Right mean | 251 ms |
| Left mean | 255 ms |

This latency estimate is useful as a baseline indicator, but it should be labeled **heuristic/post-hoc latency**, not an instrumented runtime measurement. A future test should explicitly timestamp movement onset inside the recognizer or use a defined motion-start detector.

## Landmark / Tracking Coverage

Across all 36 samples:

| Statistic | Landmark frames |
|---|---:|
| Mean | 105.2 |
| Median | 120.5 |
| Minimum | 41 |
| Maximum | 122 |
| Mean for correct samples | 108.1 |
| Mean for incorrect samples | 81.5 |

Incorrect samples averaged fewer tracked frames than correct samples (**81.5 vs. 108.1**). This suggests tracking continuity may contribute to some failures, but the dataset is too small to treat that relationship as causal.

Round 4 was especially notable because it contained two of the four total errors and had reduced landmark coverage in multiple samples. This makes camera/hand tracking continuity a useful item to inspect when reviewing failures.

## Behavior Across the Collection

The first six rounds produced **15/18 correct trials (83.3%)**. The final six rounds produced **17/18 correct trials (94.4%)**.

The recognizer itself was not learning during these trials, so this should not be interpreted as model improvement. Possible explanations include more consistent gesture execution, better hand positioning, or more stable tracking later in the session.

## Main Findings

1. The baseline recognizer achieved **88.9% overall accuracy** on this 36-trial dataset.
2. Right-swipe recall was **100.0%**, while left-swipe recall was **83.3%**.
3. There were no left/right direction confusions during intended swipe trials; the two gesture errors were missed left swipes.
4. The `no_gesture` false-positive rate was **16.7%**, with both false positives classified as `swipe_right`.
5. Correct gesture predictions averaged **0.696 confidence**.
6. The exploratory landmark-based motion-to-detection estimate had a median of approximately **219 ms**.
7. Lower landmark coverage appears in several failure cases, so tracking reliability should remain part of future tuning and evaluation.

## Recommended Follow-Up

Keep this dataset unchanged as the Sprint 2 baseline. For the next tuning pass, investigate `t3-002` and `t4-002` for the missed left swipes and `t4-003` and `t7-003` for the right-swipe false positives. After changing thresholds or recognition logic, repeat the same test protocol in a new JSONL file and compare the new metrics against this baseline.

For future datasets, consider recording additional metadata such as hand used, negative-motion scenario, lighting/session identifier, and an explicit movement-onset timestamp. Those fields would make error analysis and latency measurement more reliable.
