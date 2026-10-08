# S3-R03-T1 Recognition Error Analysis

## 1. Current Recognition Baseline

## Current Recognition Baseline

### Tracking
- **Tracked landmark:** MediaPipe landmark 9, near the center of the hand
- **Position history:** Up to 45 detected frames
- **Hand-loss grace:** 8 frames before movement history is cleared

### Displacement
- **Minimum horizontal displacement:** 0.10 normalized coordinates
- **Ideal displacement:** 0.20

### Direction and Axis Filtering
- **Minimum direction consistency:** 0.60
- **Minimum axis purity:** 0.45

### Gesture Duration
- **Minimum swipe duration:** 0.10 seconds
- **Ideal swipe duration:** 0.20–1.00 seconds
- **Maximum swipe duration:** 1.75 seconds

### Cooldown
- **Swipe cooldown:** 1.5 seconds

### Confidence
- **Final confidence threshold:** 0.55

### Confidence Weights
- **Displacement:** 40%
- **Direction consistency:** 35%
- **Axis purity:** 10%
- **Duration:** 15%

The current MediaPipe configuration also uses a hand detection confidence, hand presence confidence, and tracking confidence of 0.40.

The recognizer tracks the movement of landmark 9 over time and attempts to classify horizontal movement as either `swipe_right` or `swipe_left`. Candidate gestures must first pass displacement, directional consistency, axis purity, duration, and cooldown requirements before receiving a final weighted confidence score.

A gesture is emitted only when its final confidence is at or above 0.55.

---

## 2. Baseline Evaluation Scenarios

The Sprint 3 baseline evaluation used three trials for each scenario.

### Right Hand
- Right-hand swipe right
- Right-hand swipe left

### Left Hand
- Left-hand swipe right
- Left-hand swipe left

### Natural Wrist-Twist Swipes
- Natural wrist-twist swipe right
- Natural wrist-twist swipe left

These gestures allow the wrist and palm to rotate naturally during the horizontal swipe rather than keeping the hand orientation fixed.

### Fast Swipes
- Fast swipe right
- Fast swipe left

### Slow Swipes
- Slow swipe right
- Slow swipe left

### Non-Gesture Controls
- Casual hand repositioning
- Short horizontal movement
- Vertical movement

These scenarios were included to determine whether the recognizer incorrectly produces swipe events during movement that should not be interpreted as an intentional presentation gesture.

---

## 3. Observed Failure Cases

### 3.1 Standard Swipes Are Reliably Detected

Results:

- Right hand → right: 3/3 detected
- Right hand → left: 3/3 detected
- Left hand → right: 3/3 detected
- Left hand → left: 3/3 detected

This indicates that the basic left/right swipe recognizer is functional and does not strongly depend on which hand is being used.

However, some of these successful trials generated more than one gesture event:

- Right-hand right swipe: 1.67 predictions per trial
- Left-hand right swipe: 1.67 predictions per trial
- Left-hand left swipe: 1.33 predictions per trial

Therefore, successful recognition does not always mean that the gesture was segmented correctly.

---

### 3.2 Duplicate Gesture Detections Occur

Several physical swipes generated more than one recognition event.

The most significant duplicate behavior occurred during slower gestures:

- Slow swipe right: 3/3 detected
- Slow swipe left: 3/3 detected
- Slow swipe right average predictions: 2.00
- Slow swipe left average predictions: 2.00

This means that a single deliberate swipe frequently generated two identical gesture events.

For SlideKick, this is a significant problem because one physical gesture could cause two presentation commands and potentially skip a slide.

The likely behavior is:

1. The swipe first satisfies the recognition requirements.
2. A gesture event is emitted.
3. Position history is cleared.
4. The user's hand is still moving as part of the same physical gesture.
5. New movement history begins accumulating immediately.
6. The remaining movement satisfies the swipe requirements again.
7. A second gesture event is emitted.

This suggests that the recognizer currently lacks a strong gesture-completion or re-arm condition.

---

### 3.3 Natural Wrist-Twist Swipes Perform Poorly

Results:

- Natural twist right: 0/3 detected
- Natural twist left: 1/3 detected

During testing, the MediaPipe hand skeleton was visibly observed flickering or disappearing when the wrist or palm rotated significantly.

This suggests that the failure may not primarily be caused by the swipe thresholds themselves.

Instead, MediaPipe appears to temporarily lose reliable landmark tracking during rotational movement. When this occurs, the swipe recognizer receives fewer usable landmark samples and may be unable to accumulate sufficient displacement or directional history.

Because the swipe recognizer depends entirely on MediaPipe landmarks, recognition cannot succeed reliably if those landmarks disappear during the gesture.

---

### 3.4 Fast Swipes Perform Poorly

Results:

- Fast swipe right: 1/3 detected
- Fast swipe left: 0/3 detected

Similar to the wrist-twist scenarios, visible hand-skeleton instability was observed during rapid motion.

Fast hand movement appears to increase the likelihood that MediaPipe temporarily loses the hand landmarks.

This results in missing position samples during the gesture and makes it difficult for the swipe recognizer to build enough reliable movement history before the gesture ends.

Therefore, the poor fast-swipe performance may be primarily related to hand-tracking stability rather than the swipe confidence threshold itself.

---

### 3.5 Slow Swipes Are Detected but Over-Trigger

Results:

- Slow swipe right: 3/3 detected
- Slow swipe left: 3/3 detected
- Average predictions: 2.00 for both directions

Slow swipes provide MediaPipe with many stable landmark frames, so the swipe recognizer has sufficient movement information to detect the gesture.

However, because the hand remains in motion for longer, the recognizer can detect multiple valid swipe segments inside one continuous physical gesture.

This makes slow swipes highly reliable in terms of detection but unreliable in terms of producing exactly one command.

---

### 3.6 Basic Non-Gestures Are Rejected Correctly

Results:

- Casual repositioning: 0/3 false positives
- Short horizontal movement: 0/3 false positives
- Vertical movement: 0/3 false positives

Across nine non-gesture trials, no false swipe event was produced.

This indicates that the existing displacement and axis filtering already provides useful protection against simple accidental motion.

Because of this result, the geometric thresholds should not be broadly loosened without evidence that a specific threshold is responsible for a failure.

---

## 4. Likely Cause of Each Failure

### Natural Wrist-Twist Swipes

**Observed failure:** Most natural wrist-twist swipes are not detected.

**Likely cause:** MediaPipe landmark tracking becomes unstable when the palm and wrist rotate. The hand skeleton visibly flickers or disappears, preventing the recognizer from receiving continuous landmark coordinates.

**Primary area involved:** MediaPipe tracking stability.

---

### Fast Swipes

**Observed failure:** Most very fast swipes are not detected.

**Likely cause:** Rapid movement causes MediaPipe landmark tracking to temporarily fail or skip important portions of the movement.

The recognizer therefore may not receive enough continuous displacement samples before the gesture ends.

**Primary area involved:** MediaPipe tracking stability and temporal sampling.

---

### Slow Swipes

**Observed failure:** Slow swipes are recognized reliably but often generate two gesture events.

**Likely cause:** The recognizer immediately begins collecting new movement history after recognizing a gesture even though the original physical gesture is still occurring.

**Primary area involved:** Gesture segmentation and re-arming.

---

### Duplicate Normal Swipes

**Observed failure:** Some normal swipes generate more than one prediction.

**Likely cause:** Similar to slow swipes, remaining hand movement after the first recognized event can begin a second recognition sequence.

**Primary area involved:** Gesture segmentation and re-arming.

---

### Non-Gesture Controls

**Observed failure:** None observed during the current baseline.

**Likely cause:** Existing minimum displacement and axis-purity requirements are successfully preventing these movements from becoming swipe events.

**Primary area involved:** No immediate change required.

---

## 5. Severity and Frequency

### High Priority: Hand-Tracking Instability

Natural wrist-twist and fast-swipe scenarios performed poorly:

- Twist right: 0/3
- Twist left: 1/3
- Fast right: 1/3
- Fast left: 0/3

These are realistic presentation gestures and should ideally be supported.

Visible MediaPipe skeleton loss occurred during these movements, making hand-tracking stability a high-priority issue.

---

### High Priority: Duplicate Gesture Detection

Slow swipes produced an average of two predictions per physical gesture in both directions.

Duplicate recognition is particularly serious because SlideKick now routes recognized gesture events to presentation commands.

One duplicated swipe could therefore advance or reverse multiple slides.

---

### Medium Priority: Direction and Hand Differences

Standard swipes worked successfully with both hands, which indicates that handedness itself is not currently a major recognition problem.

Some right-direction gestures produced more duplicate events than left-direction gestures, but additional data would be required before concluding that there is a directional bias.

---

### Low Priority: Basic Non-Gesture False Positives

The baseline produced:

- 0/3 false positives for casual repositioning
- 0/3 false positives for short horizontal movement
- 0/3 false positives for vertical movement

The current filtering for these basic accidental motions is performing well and should be preserved.

---

## 6. Candidate Improvements

### Candidate 1: Tune MediaPipe Tracking Stability

Experiment with the MediaPipe tracking configuration before changing swipe-classification thresholds.

The current configuration uses:

- `min_hand_detection_confidence = 0.40`
- `min_hand_presence_confidence = 0.40`
- `min_tracking_confidence = 0.40`

Controlled experiments can test whether slightly different tracking-confidence values allow the hand skeleton to remain visible during fast movement and wrist rotation.

For example:

- Baseline tracking confidence: 0.40
- Experiment A: 0.35
- Experiment B: 0.30

Only one variable should be changed at a time so the effect can be measured.

---

### Candidate 2: Improve Gesture Re-Arming

After a swipe is detected, the recognizer should not immediately begin recognizing another swipe from the remaining motion of the same physical gesture.

Possible approaches include requiring one or more of the following before another gesture can begin:

- A short period of low movement
- A neutral or stable hand state
- A minimum reset displacement
- A movement-direction reset
- A dedicated recognition state such as `READY`, `GESTURE_ACTIVE`, and `WAITING_FOR_RESET`

This could prevent one continuous swipe from generating multiple presentation commands.

---

### Candidate 3: Review Position-History Behavior

Fast gestures may not provide enough reliable samples before the gesture ends.

The current 45-frame history works well for slower gestures, but the recognizer should be evaluated to determine whether fast motion requires a different temporal treatment.

Any change should preserve the existing ability to reject short accidental movements.

---

### Candidate 4: Improve Robustness to Natural Wrist Rotation

If MediaPipe tracking can be stabilized, the recognizer should be retested using natural wrist-twist gestures.

If tracking remains unreliable even after tuning, a future option would be to compare the landmark output of MediaPipe Hand Landmarker against the current Gesture Recognizer pipeline.

A model/component change should only be considered if tuning the existing pipeline does not provide sufficient stability.

---

### Candidate 5: Avoid Global Threshold Changes

The current baseline does not support simply lowering the overall confidence threshold.

Lowering thresholds could potentially recover some missed gestures, but it could also weaken the currently successful non-gesture rejection.

Similarly, raising thresholds could reduce duplicate or accidental detections while further reducing fast and natural-swipe recognition.

Threshold changes should therefore only be made when a specific measured failure justifies them.

---

## 7. Selected Highest-Value Change

The highest-value Sprint 3 tuning priority is:

**Improve MediaPipe hand-landmark tracking stability during fast motion and natural wrist rotation.**

The baseline results show that normal gestures are recognized reliably when the MediaPipe hand skeleton remains stable.

In contrast, the worst-performing gesture categories—fast swipes and natural wrist-twist swipes—were frequently associated with visible hand-skeleton flickering or disappearance.

This suggests that changing the swipe classifier alone may not solve the primary problem because the classifier cannot evaluate movement that MediaPipe fails to track.

A secondary priority is:

**Improve temporal gesture segmentation and re-arming so that one physical swipe produces exactly one gesture event.**

This is necessary to address duplicate detections observed during normal and especially slow swipes.

---

## 8. Sprint 3 Tuning Plan

### Step 1: Establish Tracking Baseline

Use the existing Sprint 3 evaluation harness to retain the current results as the before-tuning baseline.

Focus on:

- Normal swipes
- Natural wrist-twist swipes
- Fast swipes
- Slow swipes
- Non-gesture controls

---

### Step 2: Tune MediaPipe Tracking

Test small controlled changes to MediaPipe tracking confidence.

Change only one tracking parameter at a time and repeat the affected scenarios.

Primary success criteria:

- Reduced skeleton flicker during wrist rotation
- Reduced skeleton loss during fast swipes
- Improved fast-swipe detection
- Improved natural wrist-twist detection
- No increase in false positives during non-gesture controls

---

### Step 3: Add Gesture Re-Arm Logic

Introduce a clearer separation between one completed gesture and the next gesture.

The recognizer should enter a temporary post-recognition state and require evidence that the previous physical motion has ended before another swipe can be recognized.

Primary success criteria:

- Slow swipe right produces one event instead of two
- Slow swipe left produces one event instead of two
- Normal swipes consistently produce exactly one event
- Legitimate future gestures can still be recognized after the reset condition is satisfied

---

### Step 4: Re-Evaluate Confidence and Gesture Thresholds

After tracking stability and gesture segmentation are improved, re-run the same evaluation scenarios.

Only then determine whether displacement, duration, direction consistency, axis purity, or final confidence thresholds still require adjustment.

This prevents threshold tuning from compensating for problems that originate earlier in the recognition pipeline.

---

### Step 5: Preserve Non-Gesture Filtering

Any tuning changes must maintain the current successful rejection of:

- Casual hand repositioning
- Short horizontal movement
- Vertical movement

The goal is to increase valid-gesture recognition without sacrificing the current low false-positive behavior.

---

## Sprint 3 T1 Decision

The baseline evaluation indicates that SlideKick's rule-based swipe classifier is already capable of reliably recognizing standard left/right gestures and rejecting simple non-gesture motion when MediaPipe tracking remains stable.

The largest recognition failures occur during natural wrist rotation and rapid hand movement, where visible MediaPipe skeleton loss prevents the classifier from receiving reliable landmark data.

A separate temporal segmentation issue causes some normal and slow gestures to generate duplicate events.

Therefore, Sprint 3 implementation will prioritize:

1. **Improving MediaPipe landmark tracking stability during fast and rotational movement.**
2. **Improving gesture completion and re-arming so one physical swipe produces one event.**
3. **Preserving the existing successful non-gesture filtering.**
4. **Only adjusting swipe-confidence or geometric thresholds after the tracking and segmentation issues have been evaluated.**

This approach provides the highest-value improvement to prototype stability while minimizing unnecessary changes to recognition logic that is already functioning correctly under stable tracking conditions.