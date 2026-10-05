# S1-R03-T3 Recognition Experiment Log

## Purpose

This experiment establishes an initial baseline for the SlideKick gesture-recognition prototype created during Sprint 1.

The goal is to observe the current prototype's gesture detection accuracy and processing latency before additional recognition tuning is performed in later sprints.

## Test Environment

- Operating System: Windows
- Development Environment: Docker / Lando
- Python Version: 3.11
- Recognition Library: MediaPipe Gesture Recognizer
- Computer Vision Library: OpenCV
- Camera:
- Lighting Conditions:
- Approximate Distance From Camera:

## Recognition Configuration

- Swipe Tracking Landmark: Landmark 9
- Swipe Threshold: 0.20 normalized horizontal displacement
- Swipe Cooldown: 0.75 seconds
- Maximum Swipe Duration: 0.50 seconds
- Minimum Direction Consistency: 0.75
- Position History: 10 frames

## Baseline Accuracy Test

### Test Procedure

The recognition prototype was tested under normal indoor lighting with the user's hand clearly visible to the webcam.

Three test groups were performed:

1. 10 intentional right-swipe gestures
2. 10 intentional left-swipe gestures
3. 10 non-swipe hand movements

For each intentional swipe, the result was recorded as:

- Correct Detection: The expected swipe event was emitted.
- Missed Detection: No swipe event was emitted.
- Incorrect Detection: The opposite swipe direction was emitted.

For each non-swipe movement:

- Correct Rejection: No swipe event was emitted.
- False Positive: A swipe event was emitted even though no intentional swipe occurred.

At least one second was allowed between intentional swipe attempts to avoid interference from the prototype's swipe cooldown.

### Results

Swipe Right (10 Attempts):
Correct - 8
Missed - 2
Incorrect - 0
Accuracy - 80%

Swipe Left (10 Attempts):
Correct - 7
Missed - 3
Incorrect - 0
Accuracy - 70%

Non-Swipe (10 Attempts):
Correct - 9
Incorrect - 1
Correction Rejection Rate - 90%
False Positive Rate - 10%

Total (30 Attempts):
Overall trial Accuracy - 80%

## Observations

- Right swipes were detected more reliably than left swipes during the baseline test.
- The prototype correctly detected 15 of 20 intentional swipe gestures, resulting in a combined swipe detection accuracy of 75%.
- No intentional swipe was detected as the opposite direction; all failed swipe attempts were missed detections.
- The prototype correctly ignored 9 of 10 non-swipe movements.
- One non-swipe movement produced an unintended swipe event, resulting in a 10% false positive rate.
- Hand landmark tracking became less stable under poor lighting. When the landmark skeleton temporarily disappeared, swipe tracking could be interrupted because the current movement history was reset.
- Testing was therefore performed under normal indoor lighting with the hand clearly visible to the webcam.
- Swiping was detected more efficiently when hand faced forward, when any twist motion occurred, at times it failed to properly identify a swipe

## Baseline Latency Test

### Test Procedure

The recognition prototype was run three times under normal indoor lighting. During each run, a hand remained visible to the webcam while normal hand movements and swipe gestures were performed.

Processing latency was measured from the start of MediaPipe frame processing until SlideKick completed processing the recognition result for that frame.

Latency was measured using Python's `time.perf_counter()` and converted to milliseconds.

#### Results

Run 1:
- Samples:
- Average:
- Minimum:
- Maximum:

Run 2:
- Samples:
- Average:
- Minimum:
- Maximum:

Run 3:
- Samples:
- Average:
- Minimum:
- Maximum:

### Results

Run 1:
Samples: 414
Average: 16.48 ms
Minimum: 14.29 ms
Maximum: 27.28 ms

Run 2:
Samples: 517
Average: 16.19 ms
Minimum: 13.98 ms
Maximum: 22.59 ms

Run 3:
Samples: 534
Average: 16.23 ms
Minimum: 14.08 ms
Maximum: 23.16 ms

Summary:
Total Samples: 1,465
Weighted Average Processsing Latency: approximately 16.29ms
Lowest Observed Latency: 13.90 ms
Highest Obeserved Latency: 27.28 ms
Average latency remaine consisteen accross all three runs, ranging from 16.19 ms to 16.48 ms.

## Observations

- Recognition processing latency remained stable across all three test runs.
- The average processing latency was approximately 16.29 ms across 1,465 recorded frames.
- Each individual run produced an average latency close to 16 ms, indicating consistent recognition processing performance during the baseline test.
- The highest individual latency observed was 27.28 ms, while the lowest was 13.98 ms.
- These measurements represent recognition processing latency only and do not represent total end-to-end latency between a user's physical gesture and a presentation command.

## Limitations

- The prototype's swipe detection depends on continuous hand landmark tracking. If MediaPipe temporarily loses the hand, the current position history is cleared and the swipe must begin again.

- Poor lighting reduces landmark tracking stability. During testing, the hand skeleton occasionally flickered or disappeared, which could interrupt otherwise valid swipe gestures.

- Swipe detection currently relies on fixed thresholds for horizontal displacement, movement duration, direction consistency, and cooldown. These values have not yet been tuned across multiple users or environments.

- The baseline accuracy test was performed by a single user with a limited number of trials, so the results should only be treated as an initial prototype baseline.

- Only left and right swipe behavior was evaluated during this Sprint 1 baseline. Other SlideKick gesture commands were not included.

- The latency measurements represent recognition processing time for individual frames. They do not measure full end-to-end latency from the start of a physical gesture to the execution of a presentation command.

- Camera quality, user distance, hand position, background conditions, and lighting may affect recognition performance. These factors were not systematically varied during the baseline test.

- The current prototype does not include a recovery/grace period for briefly lost hand landmarks, advanced filtering, calibration, or user-specific threshold adjustment.