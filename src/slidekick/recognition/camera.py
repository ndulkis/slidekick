"""SlideKick webcam capture, hand tracking, and recognition event processing.

Responsibilities:
- Initialize the webcam and MediaPipe Gesture Recognizer.
- Convert camera frames into the format expected by MediaPipe.
- Draw detected hand landmarks and recognition diagnostics.
- Forward detected hands to the swipe recognition subsystem.
- Emit standardized recognition events to the application.
- Support manual recognition sample recording for evaluation.
"""

# ============================================================
# 1. IMPORTS
# ============================================================

import time
from collections import deque

import cv2  # OpenCV for webcam capture and frame processing
import mediapipe as mp  # MediaPipe for hand detection and tracking

from .events import create_landmark_event
from .sample_recorder import SampleRecorder
from .swipe_recognizer import (
    GestureCalibration,
    GestureRecognitionState,
    detect_swipe,
)

# ============================================================
# 2. CAMERA AND RECOGNITION CONFIGURATION
# ============================================================

# Path to the MediaPipe Gesture Recognizer task model.
MODEL_PATH = "models/gesture_recognizer.task"

# Initial dimensions of the SlideKick camera preview window.
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540

# Requested webcam capture resolution and frame rate.
CAMERA_CAPTURE_WIDTH = 1280
CAMERA_CAPTURE_HEIGHT = 720
CAMERA_CAPTURE_FPS = 30

# Maximum number of consecutive failed frame reads before exiting.
MAX_FAILED_READS = 30

# Number of missed hand-detection frames tolerated before
# clearing old movement history to avoid stale swipe data.
HAND_LOSS_GRACE_FRAMES = 8

# Maximum number of hand positions stored for swipe recognition.
POSITION_HISTORY_SIZE = 45

# MediaPipe's hand detection and tracking confidence thresholds.
HAND_DETECTION_CONFIDENCE = 0.40
HAND_PRESENCE_CONFIDENCE = 0.40
HAND_TRACKING_CONFIDENCE = 0.40


# ============================================================
# 3. HAND SKELETON CONFIGURATION
# ============================================================

# Landmark pairs that form the hand skeleton.
# Each number corresponds to a MediaPipe hand landmark index.
HAND_CONNECTIONS = [
    # Thumb
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    # Index finger
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),
    # Middle finger
    (5, 9),
    (9, 10),
    (10, 11),
    (11, 12),
    # Ring finger
    (9, 13),
    (13, 14),
    (14, 15),
    (15, 16),
    # Pinky
    (13, 17),
    (17, 18),
    (18, 19),
    (19, 20),
    # Bottom of palm
    (0, 17),
]


# ============================================================
# 4. CAMERA AND MEDIAPIPE INITIALIZATION
# ============================================================


def create_camera_window():
    """Create the resizable SlideKick camera preview window."""

    window_name = "SlideKick Camera"

    # Create a normal resizable window.
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    # Set the initial window size.
    cv2.resizeWindow(window_name, WINDOW_WIDTH, WINDOW_HEIGHT)

    return window_name


def create_recognizer_options():
    """Configure the MediaPipe Gesture Recognizer."""

    # VIDEO mode allows MediaPipe to track hands across
    # consecutive frames rather than processing isolated images.
    options = mp.tasks.vision.GestureRecognizerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=HAND_DETECTION_CONFIDENCE,
        min_hand_presence_confidence=HAND_PRESENCE_CONFIDENCE,
        min_tracking_confidence=HAND_TRACKING_CONFIDENCE,
    )

    return options


def convert_frame_to_mediapipe(frame):
    """Mirror and convert an OpenCV frame into a MediaPipe image."""

    # Mirror the image so the preview behaves like a normal webcam.
    frame = cv2.flip(frame, 1)

    # Convert OpenCV frames from BGR to RGB for MediaPipe.
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Wrap the RGB frame in MediaPipe's image representation.
    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame,
    )

    return frame, mp_image


# ============================================================
# 5. HAND LANDMARK EXTRACTION AND DRAWING
# ============================================================


def get_landmark_points(hand_landmarks, frame):
    """Convert normalized hand landmarks into pixel coordinates."""

    # Get frame dimensions for normalized-to-pixel conversion.
    frame_height, frame_width, _ = frame.shape

    # Stores the pixel coordinates for each detected hand landmark.
    landmark_points = []

    for landmark in hand_landmarks:
        # Convert normalized X and Y coordinates into pixels.
        x = int(landmark.x * frame_width)
        y = int(landmark.y * frame_height)

        # Store each landmark's pixel coordinates.
        landmark_points.append((x, y))

    return landmark_points


def draw_hand_skeleton(frame, landmark_points):
    """Draw landmark connections and points onto a camera frame."""

    # Defines how the hand skeleton lines will be drawn.
    line_color = (255, 255, 255)
    line_thickness = 2

    # Draw lines between connected hand landmarks.
    for start_index, end_index in HAND_CONNECTIONS:
        start_point = landmark_points[start_index]
        end_point = landmark_points[end_index]

        cv2.line(
            frame,
            start_point,
            end_point,
            line_color,
            line_thickness,
        )

    # Defines how each landmark point will be drawn.
    circle_radius = 5
    circle_color = (0, 255, 0)
    circle_thickness = -1

    # Draw each landmark point over the hand skeleton.
    for point in landmark_points:
        cv2.circle(
            frame,
            point,
            circle_radius,
            circle_color,
            circle_thickness,
        )


# ============================================================
# 6. RECOGNITION DIAGNOSTIC DISPLAY
# ============================================================


def draw_recognition_diagnostic(
    frame,
    gesture_name,
    confidence,
    recognition_enabled=True,
):
    """Display recognition status and the latest swipe prediction."""

    # Determine whether recognition is currently enabled.
    status = "ON" if recognition_enabled else "OFF"

    # Text placement inside the camera preview.
    text_x = 20
    recognition_text_y = 30
    gesture_text_y = 60
    confidence_text_y = 90

    # Shared formatting for all diagnostic labels.
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    text_color = (255, 255, 255)
    text_thickness = 2

    # Display recognition status.
    cv2.putText(
        frame,
        f"Recognition: {status}",
        (text_x, recognition_text_y),
        font,
        font_scale,
        text_color,
        text_thickness,
    )

    # Display the most recently recognized gesture.
    cv2.putText(
        frame,
        f"Gesture: {gesture_name}",
        (text_x, gesture_text_y),
        font,
        font_scale,
        text_color,
        text_thickness,
    )

    # Display the confidence of the most recent gesture.
    cv2.putText(
        frame,
        f"Confidence: {confidence:.2f}",
        (text_x, confidence_text_y),
        font,
        font_scale,
        text_color,
        text_thickness,
    )


# ============================================================
# 7. HAND DETECTION AND GESTURE PROCESSING
# ============================================================


def process_hand_detection(
    result,
    frame,
    position_history,
    gesture_state: GestureRecognitionState,
    missed_hand_frames,
    calibration: GestureCalibration | None = None,
):
    """Process tracked hands and return standardized recognition events.

    Calibration is optional. When omitted, detect_swipe uses the
    tested default GestureCalibration settings.

    Gesture lifecycle state is preserved across missed frames so
    temporary tracking loss cannot automatically re-arm a gesture.
    """

    # Stores standardized recognition events generated during the current frame.
    gesture_event = None
    landmark_event = None

    # Check whether MediaPipe detected any hand landmarks.
    if result.hand_landmarks:
        # A hand was found, so reset the missed-frame counter.
        missed_hand_frames = 0

        # Get the 21 landmarks from the first detected hand.
        hand_landmarks = result.hand_landmarks[0]

        # Record the current monotonic time for recognition.
        current_time = time.monotonic()

        # Create a standardized SlideKick hand landmark event.
        landmark_event = create_landmark_event(
            hand_landmarks,
            current_time,
        )

        # Detect a swipe using the current gesture lifecycle state.
        # The optional calibration controls recognition thresholds.
        gesture_event = detect_swipe(
            hand_landmarks,
            position_history,
            gesture_state,
            current_time,
            calibration=calibration,
        )

        # Convert the detected landmarks into pixel coordinates.
        landmark_points = get_landmark_points(
            hand_landmarks,
            frame,
        )

        # Draw the hand skeleton onto the camera frame.
        draw_hand_skeleton(frame, landmark_points)

    else:
        # Increment the number of consecutive frames without a hand.
        missed_hand_frames += 1

        # Clear stale position history after prolonged tracking loss.
        if missed_hand_frames >= HAND_LOSS_GRACE_FRAMES:
            position_history.clear()

            # Do not reset gesture_state here.
            # Recognition must still satisfy its re-arming conditions.

    return gesture_event, landmark_event, missed_hand_frames


# ============================================================
# 8. WINDOW AND EVENT UTILITIES
# ============================================================


def should_close_window(window_name, key):
    """Check whether the user requested to close the camera."""

    # Press Q to close the camera.
    if key == ord("q"):
        return True

    # Also close if the user clicked the window's X button.
    return (
        cv2.getWindowProperty(
            window_name,
            cv2.WND_PROP_VISIBLE,
        )
        < 1
    )


def emit_event(event, event_handler):
    """Send a recognition event to an optional application handler."""

    # Only send events when both the event and handler exist.
    if event is not None and event_handler is not None:
        event_handler(event)


def print_recognition_event(event):
    """Print gesture events during standalone prototype testing."""

    # Display only gesture events for prototype testing.
    if event.get("event_type") == "gesture":
        print(event)

    # Landmark events can be printed when additional
    # recognition diagnostics are needed.
    # if event.get("event_type") == "landmarks":
    #     print(event)


# ============================================================
# 9. MAIN CAMERA APPLICATION
# ============================================================


def run_camera(
    event_handler=None,
    calibration: GestureCalibration | None = None,
    key_handler=None,
):
    """Run the SlideKick camera and gesture recognition loop.

    Args:
        event_handler:
            Optional callback receiving standardized gesture and
            landmark events.

        calibration:
            Optional custom recognition settings. If omitted,
            SlideKick uses its tested default thresholds.
    """

    # --------------------------------------------------------
    # A. Initialize camera window and capture device
    # --------------------------------------------------------
    window_name = create_camera_window()

    # Camera index 0 selects the computer's default webcam.
    camera = cv2.VideoCapture(0)

    # Request the capture resolution and frame rate.
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_CAPTURE_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_CAPTURE_HEIGHT)
    camera.set(cv2.CAP_PROP_FPS, CAMERA_CAPTURE_FPS)

    # Configure the MediaPipe Gesture Recognizer.
    options = create_recognizer_options()

    # Resolve the recognition calibration once per camera session.
    # The UI or session manager may supply a custom configuration.
    if calibration is None:
        calibration = GestureCalibration()

    # --------------------------------------------------------
    # B. Initialize recognition and tracking state
    # --------------------------------------------------------

    # Store recent tracked hand positions as (timestamp, x, y).
    position_history: deque[tuple[float, float, float]] = deque(
        maxlen=POSITION_HISTORY_SIZE
    )

    # Store gesture lifecycle information across camera frames.
    gesture_state = GestureRecognitionState()

    # Track consecutive frames where no hand was detected.
    missed_hand_frames = 0

    # Track consecutive unsuccessful camera frame reads.
    failed_reads = 0

    # --------------------------------------------------------
    # C. Initialize Sprint 2 manual sample recording
    # --------------------------------------------------------

    # TOP(TEST) Used for S2 testing sample recorder.
    # This workflow remains available for manual evaluation.
    sample_recorder = SampleRecorder("data/evaluation/s2_recognition_samples.jsonl")

    # Labels assigned to consecutive evaluation samples.
    evaluation_labels = [
        "swipe_right",
        "swipe_left",
        "no_gesture",
    ]

    # Continue recording from the next expected sample label.
    evaluation_index = sample_recorder.next_label_index

    # The next sample waits until a hand is detected.
    pending_expected_gesture = None

    # BOTTOM(TEST)

    # --------------------------------------------------------
    # D. Verify the camera is available
    # --------------------------------------------------------

    if not camera.isOpened():
        print("Error: Could not open camera.")
        camera.release()
        cv2.destroyAllWindows()
        return

    # --------------------------------------------------------
    # E. Start the MediaPipe recognition session
    # --------------------------------------------------------

    # Create the recognizer with the configured task model.
    with mp.tasks.vision.GestureRecognizer.create_from_options(options) as recognizer:
        # MediaPipe VIDEO mode requires increasing timestamps.
        last_frame_time_stamp_ms = -1

        # Values displayed by the diagnostic overlay.
        last_gesture_name = "none"
        last_gesture_confidence = 0.0

        # ----------------------------------------------------
        # F. Main frame-processing loop
        # ----------------------------------------------------

        while True:
            # Read the next camera frame.
            success, frame = camera.read()

            if not success:
                failed_reads += 1

                # Give up after too many failed reads in a row.
                if failed_reads >= MAX_FAILED_READS:
                    print("Error: Could not read frame.")
                    break

                # Wait briefly before retrying so the camera
                # has time to warm up.
                time.sleep(0.03)
                continue

            # Reset failures after successfully reading a frame.
            failed_reads = 0

            # Mirror and convert the frame for MediaPipe.
            frame, mp_image = convert_frame_to_mediapipe(frame)

            # Create a timestamp in milliseconds.
            frame_timestamp_ms = int(time.monotonic() * 1000)

            # Ensure timestamps are strictly increasing.
            if frame_timestamp_ms <= last_frame_time_stamp_ms:
                frame_timestamp_ms = last_frame_time_stamp_ms + 1

            last_frame_time_stamp_ms = frame_timestamp_ms

            # Process the image using MediaPipe hand tracking.
            result = recognizer.recognize_for_video(
                mp_image,
                frame_timestamp_ms,
            )

            # Convert MediaPipe results into standardized
            # landmark and gesture events.
            gesture_event, landmark_event, missed_hand_frames = process_hand_detection(
                result,
                frame,
                position_history,
                gesture_state,
                missed_hand_frames,
                calibration=calibration,
            )

            # ------------------------------------------------
            # G. Sprint 2 evaluation sample recording
            # ------------------------------------------------

            # TOP TEST

            # Start recording when a sample is armed and
            # a hand has become visible.
            if (
                pending_expected_gesture is not None
                and sample_recorder.active_sample is None
                and landmark_event is not None
            ):
                sample_recorder.start_sample(
                    pending_expected_gesture,
                    landmark_event["timestamp"],
                )

                print(f"Hand detected. Recording: {pending_expected_gesture}")

                pending_expected_gesture = None

            # Record landmark observations and predictions
            # while an evaluation sample is active.
            if sample_recorder.active_sample is not None:
                if landmark_event is not None:
                    sample_recorder.record_landmarks(landmark_event)

                if gesture_event is not None:
                    sample_recorder.record_prediction(gesture_event)

                current_time = time.monotonic()

                # Finish the sample once its recording
                # duration has elapsed.
                if sample_recorder.should_finish_sample(current_time):
                    sample_recorder.finish_sample(current_time)
                    evaluation_index = sample_recorder.next_label_index

            # BOTTOM TEST

            # ------------------------------------------------
            # H. Process and emit recognition events
            # ------------------------------------------------

            # Store the latest gesture details for the overlay.
            if gesture_event is not None:
                last_gesture_name = gesture_event["gesture"]
                last_gesture_confidence = gesture_event["confidence"]

            # Send gesture and landmark events to the application.
            emit_event(gesture_event, event_handler)
            emit_event(landmark_event, event_handler)

            # ------------------------------------------------
            # I. Draw diagnostics and display camera preview
            # ------------------------------------------------

            # Overlay the recognition status and latest gesture.
            draw_recognition_diagnostic(
                frame,
                last_gesture_name,
                last_gesture_confidence,
            )

            # Display the processed frame in the camera window.
            cv2.imshow(window_name, frame)

            # Process keyboard input and window events.
            key = cv2.waitKey(1) & 0xFF

            # ------------------------------------------------
            # J. Sprint 2 manual evaluation controls
            # ------------------------------------------------

            # TOP TEST

            # Press Space to arm the next labeled sample.
            # Recording begins when the hand is detected.
            if (
                key == ord(" ")
                and sample_recorder.active_sample is None
                and pending_expected_gesture is None
            ):
                pending_expected_gesture = evaluation_labels[evaluation_index]

                # Start each evaluation sample with fresh
                # recognition history and lifecycle state.
                position_history.clear()
                gesture_state = GestureRecognitionState()
                missed_hand_frames = 0

                print(
                    f"Sample {evaluation_index + 1}/"
                    f"{len(evaluation_labels)} armed: "
                    f"{pending_expected_gesture}. "
                    f"Waiting for hand..."
                )

            # BOTTOM TEST

            # ------------------------------------------------
            # K. Check whether the camera should close
            # ------------------------------------------------

            # Close when Q is pressed or the window is dismissed.
            if should_close_window(window_name, key):
                break

            if key_handler is not None:
                key_handler(key)

    # --------------------------------------------------------
    # L. Release camera resources
    # --------------------------------------------------------

    # Release the webcam after the recognition loop exits.
    camera.release()

    # Close all OpenCV windows created by the application.
    cv2.destroyAllWindows()


# ============================================================
# 10. STANDALONE ENTRY POINT
# ============================================================

if __name__ == "__main__":
    # Run the camera with default calibration and print
    # recognized gesture events for development diagnostics.
    run_camera(print_recognition_event)
