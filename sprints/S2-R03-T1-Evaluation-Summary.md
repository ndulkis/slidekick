# S2-R03-T1 Evaluation Summary

**Role:** R03 - Full-Stack Recognition & Data Steward  
**Sprint:** Sprint 2  
**Task:** Define baseline gestures, confidence-threshold method, calibration data, and dataset format  
**Date:** September 24, 2026

## Purpose

This document summarizes the design and evaluation work completed for S2-R03-T1. The goal of this task was to define how SlideKick should represent gestures, calculate recognition confidence, store calibration data, and structure gesture datasets before expanding the recognition prototype.

This work is design/evaluation documentation. It defines the intended recognition architecture and data contracts that later Sprint 2 implementation and testing can follow.

## 1. Recognition Architecture

SlideKick should keep gesture recognition separate from presentation commands so that gestures can later be reassigned by the user in a way similar to key bindings.

Intended flow:

```text
Camera
  ↓
Hand Tracking
  ↓
Gesture Recognition
  ↓
GestureEvent
  ↓
Gesture Binding / Mapping
  ↓
Controller Command
  ↓
PowerPoint / Keynote
```

The recognition layer should emit a generic gesture identity and recognition metadata rather than directly triggering a slide action.

A recognition result may contain attributes such as:

- `gesture_id`
- `confidence`
- `timestamp`
- `hand`
- `duration`
- `displacement`

## 2. Baseline Gesture Definitions

SlideKick will support both static and dynamic gestures.

### Static Gesture

A hand pose or configuration maintained for a short period.

Examples:

- Open Palm
- Closed Fist
- Thumbs Up

### Dynamic Gesture

A sequence of hand positions or configurations occurring over time.

Examples:

- Swipe Left
- Swipe Right
- Circle
- Push Forward
- Future custom recorded gestures

Dynamic gesture measurements may include:

- Horizontal displacement
- Vertical displacement
- Movement duration
- Direction consistency

### Gesture Definition Model

A gesture definition should remain independent from the presentation command assigned to it.

Conceptually:

```text
GestureDefinition
├── id
├── name
├── type
├── recognition_method
└── parameters
```

This allows the same recognized gesture to later be mapped to different SlideKick actions without changing the recognition layer.

## 3. Confidence-Threshold Method

Every recognizer should output a normalized confidence score between `0.0` and `1.0`.

The method used to calculate confidence may differ by gesture type.

Examples:

- Static gestures may use MediaPipe classification confidence or pose/landmark similarity.
- Dynamic gestures may use movement characteristics.
- Future custom gestures may use similarity against stored examples or templates.

SlideKick standardizes the confidence output, not the internal confidence calculation.

### Swipe Confidence Components

For swipe gestures, the initial confidence calculation will use four measurements:

| Component | Weight |
|---|---:|
| Primary-axis displacement | 0.35 |
| Directional consistency | 0.30 |
| Off-axis deviation | 0.20 |
| Movement duration | 0.15 |

Final swipe confidence:

```text
confidence =
    (0.35 × displacement_score)
  + (0.30 × direction_score)
  + (0.20 × off_axis_score)
  + (0.15 × duration_score)
```

### Candidate Validation

A movement must first satisfy the basic swipe requirements before confidence is calculated.

Initial Sprint 2 swipe candidate requirements:

- Minimum normalized primary-axis displacement: `0.20`
- Minimum directional consistency: `0.75`
- Maximum normalized off-axis deviation: `0.12`
- Allowed duration: `0.15` to `0.75` seconds
- Cooldown prevents one movement from generating repeated gesture events

After candidate validation, the gesture must meet the initial confidence threshold:

```text
confidence >= 0.75
```

Candidates below the threshold may still be useful for diagnostics and later evaluation.

Thresholds should remain configurable per gesture because different gestures may require different recognition sensitivity.

## 4. Calibration Data

Calibration should adapt SlideKick to the user and camera environment. It should not define the gesture itself.

Baseline calibration values may include:

- Preferred or detected hand
- Neutral hand position
- Horizontal movement range
- Vertical movement range
- Hand scale
- Tracking stability / landmark jitter

Example:

```json
{
  "preferred_hand": "right",
  "neutral_position": {
    "x": 0.52,
    "y": 0.48
  },
  "horizontal_range": 0.64,
  "vertical_range": 0.49,
  "hand_scale": 0.13,
  "tracking_jitter": 0.006
}
```

Calibration data should remain separate from:

- Built-in gesture definitions
- Gesture-specific thresholds
- User-recorded custom gesture examples

If calibration values are unavailable during Sprint 2, the prototype may use default recognition parameters while keeping the data structure ready for future user-specific normalization.

## 5. Dataset Format

SlideKick needs a dataset format that can represent:

- Static gestures
- Dynamic gestures
- Negative / no-gesture samples
- Future user-created gestures

JSON or JSONL will be used as the baseline storage format because nested landmark data and variable-length frame sequences are difficult to represent cleanly in flat CSV files.

### Generic Gesture Sample

Each labeled sample should include:

- Unique sample identifier
- Ground-truth gesture identity
- Gesture type
- Recording session
- Calibration reference
- Detected hand
- Start and end timestamps
- Sequence of recorded hand states

Example structure:

```json
{
  "sample_id": "sample_0001",
  "gesture_id": "swipe_right",
  "gesture_type": "dynamic",
  "session_id": "session_01",
  "calibration_id": "calibration_01",
  "hand": "right",
  "start_timestamp": 12.42,
  "end_timestamp": 12.89,
  "frames": [
    {
      "timestamp": 12.42,
      "landmarks": [
        {"id": 0, "x": 0.31, "y": 0.52, "z": -0.02}
      ]
    }
  ]
}
```

The raw timestamped MediaPipe landmark sequence should remain the primary source data.

Gesture-specific measurements may optionally be stored as derived features:

```json
{
  "features": {
    "primary_axis_displacement": 0.31,
    "direction_consistency": 0.91,
    "off_axis_deviation": 0.04,
    "duration": 0.43
  }
}
```

Derived features should not replace the original landmark sequence.

## 6. Negative Samples and Ground Truth

The dataset should include non-command movements using labels such as:

```text
no_gesture
```

Negative samples are necessary for false-positive testing and should be collected alongside intentional gestures.

Ground truth must remain separate from recognizer output.

Conceptually:

```text
Ground Truth     Prediction       Result
SWIPE_RIGHT   -> SWIPE_RIGHT   -> Correct
SWIPE_RIGHT   -> NO_GESTURE    -> False negative
NO_GESTURE    -> SWIPE_LEFT    -> False positive
SWIPE_LEFT    -> SWIPE_RIGHT   -> Misclassification
```

Keeping ground truth separate from predictions will allow Sprint 2 evaluation to calculate:

- Correct detections
- Missed detections
- False positives
- Misclassifications
- Precision and other recognition metrics

## 7. Session Metadata

Recording sessions should contain contextual metadata such as:

```json
{
  "session_id": "session_01",
  "camera_width": 1280,
  "camera_height": 720,
  "fps": 30,
  "calibration_id": "calibration_01"
}
```

Associating samples with session and calibration metadata will make later recognition experiments easier to reproduce and compare.

## 8. Custom Gesture Direction

MediaPipe Model Maker may support future user-defined static gestures, but this is not an instant runtime learning system.

A possible future workflow is:

```text
User selects "Create Gesture"
        ↓
SlideKick enters listening mode
        ↓
User holds/repeats the new pose
        ↓
SlideKick captures multiple varied examples
        ↓
Examples are labeled
        ↓
Model Maker retrains the classifier
        ↓
Updated gesture model is exported
        ↓
SlideKick loads the updated model
        ↓
New gesture becomes available for binding
```

SlideKick could hide most of this training workflow behind the application UI so the user does not need to manually train a model.

The main challenge would be collecting enough varied examples without making the experience tedious. This is currently considered a future or stretch-goal direction rather than a required Sprint 2 implementation.

## Decisions Finalized

- Gesture recognition and command binding remain separate layers.
- SlideKick supports both static and dynamic gesture concepts.
- Recognition emits gesture identities and metadata rather than presentation commands.
- Confidence is normalized to a `0.0` to `1.0` range.
- Confidence calculation is gesture-specific.
- Sprint 2 swipe confidence uses displacement, direction consistency, off-axis deviation, and duration.
- Initial swipe confidence threshold is `0.75`.
- Calibration data remains separate from gesture definitions and custom gesture training.
- JSON/JSONL is the baseline gesture dataset format.
- Raw timestamped MediaPipe landmarks remain the primary dataset source.
- Derived gesture measurements are optional diagnostic features.
- Negative `no_gesture` samples are included for false-positive evaluation.
- Ground-truth labels remain separate from recognizer predictions.
- The dataset structure remains extensible for future user-created gestures.

## Next Steps

This evaluation provides the design baseline for later Sprint 2 work, including:

- Implementing the updated swipe candidate and confidence logic
- Emitting confidence and recognition metadata through `GestureEvent`
- Adding the diagnostic UI
- Collecting labeled positive and negative gesture samples
- Evaluating precision, false positives, missed detections, and latency
- Tuning provisional thresholds using collected test data
