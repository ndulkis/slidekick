# S4-R03-T3: Static Gesture Recognition Evaluation

**Project:** SlideKick  
**Sprint:** 4  
**Task:** S4-R03-T3 — Evaluate Static Gesture Recognition and Document Results  
**Evaluation Type:** Preliminary manual testing

## 1. Overview

This document summarizes preliminary evaluation findings for SlideKick's custom static gesture recognition system.

The objective was to assess whether static gesture recognition could operate alongside the existing dynamic swipe recognizer without introducing unintended presentation commands.

Testing focused on intended gestures, non-gestures, gesture re-arming, and potential conflicts between static and dynamic recognition.

## 2. Model Configuration

The prototype uses a custom MediaPipe Gesture Recognizer model trained using MediaPipe Model Maker.

| Configuration | Value |
|---|---|
| Model format | MediaPipe `.task` |
| Custom gesture | `pinch` (thumb-to-index finger) |
| Negative class | `none` |
| Dataset | 120 labeled images |
| Class distribution | 60 `pinch`, 60 `none` |
| Training epochs | 10 |
| Batch size | 2 |
| Learning rate | 0.001 |
| Static activation hold | 400 ms |
| Gesture release period | 250 ms |
| Post-swipe suppression | 600 ms |

The prototype achieved 100% accuracy on a small 12-image test split during initial training experiments. Due to the limited dataset and evaluation conditions, this result should not be interpreted as production-level accuracy.

## 3. Manual Evaluation Findings

### 3.1 Intended Static Gesture Recognition

The custom thumb-to-index-finger pinch was successfully recognized during live webcam testing.

Accepted pinch events were converted into standardized recognition events and passed through SlideKick's existing command controller.

The `pinch` gesture was successfully mapped to the End Presentation command, confirming end-to-end integration.

### 3.2 Dynamic Swipe Compatibility

Existing swipe-left and swipe-right recognition remained operational after integrating static gesture recognition.

Manual testing did not reveal conflicts between intended swipe gestures and static gesture activation.

The arbitration mechanism was observed suppressing static gesture activation during significant hand movement and immediately after accepted swipes.

### 3.3 Static Gesture Lifecycle

Hold detection and gesture re-arming were manually tested.

The system was observed to require a sustained static gesture before activation and to prevent continuous repeated commands while the same gesture remained held.

### 3.4 Non-Gesture Classification

During non-gesture testing, occasional false-positive classifications were observed.

Specifically, touching the thumb to the middle finger or ring finger sometimes produced a `pinch` classification, despite the intended gesture being thumb-to-index-finger contact.

This indicates that the prototype may not reliably distinguish the target pinch from certain visually similar finger configurations.

The observed behavior is consistent with possible gaps in the negative training examples, although further testing is required to determine the exact cause.

## 4. Reliability Assessment

| Evaluation area | Preliminary finding |
|---|---|
| Intended pinch recognition | Functioning in manual testing |
| Swipe-left recognition | Functioning |
| Swipe-right recognition | Functioning |
| Swipe/static conflicts | No conflicts observed during manual testing |
| Duplicate command suppression | Functioning in observed hold and release tests |
| Similar-gesture false positives | Occasional misclassification observed |
| Classification confidence | Available in recognition events; statistical analysis pending |
| Quantitative accuracy | Not yet established through controlled repeatable trials |

These findings are qualitative observations. Formal detection rates, false-positive rates, and confidence distributions have not yet been measured.

## 5. Known Limitations

- The prototype training dataset is small and has limited variation.
- Recognition has not been systematically evaluated across multiple users, lighting conditions, backgrounds, and camera positions.
- Similar finger configurations can occasionally be misclassified as the target gesture.
- Manual testing is insufficient to establish statistically reliable accuracy or false-positive rates.
- Model Maker dependency compatibility and long-term maintenance require consideration.
- Built-in static gesture command integration remains future work.

## 6. Recommended Improvements

1. Expand the negative training dataset with thumb-to-middle, thumb-to-ring, and thumb-to-pinky finger configurations.
2. Collect training and evaluation samples across multiple users and environmental conditions.
3. Introduce repeatable automated recognition evaluation using separately labeled test samples.
4. Measure classification accuracy, false positives, duplicate activations, and confidence distributions.
5. Evaluate confusion between visually similar gestures using a confusion matrix.
6. Reassess classification thresholds and gesture-specific validation after collecting additional evaluation data.

## 7. Conclusion

Preliminary testing demonstrates that custom static gesture recognition can be integrated into SlideKick while preserving dynamic swipe functionality.

The custom pinch gesture successfully executes presentation commands, and the existing arbitration and gesture lifecycle mechanisms functioned as intended during manual testing.

However, occasional false-positive recognition of similar finger configurations highlights the need for improved training data and more rigorous evaluation.

The prototype is suitable for continued development and controlled demonstrations, but further validation is required before making production-level reliability claims.