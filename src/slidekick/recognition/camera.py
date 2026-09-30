# OpenCV webcam capture and frame processing
import time  # Used to determine cooldown/debounce
from collections import (
    deque,
)  # Stores recent frame history for tracking dynamic gesture displacement

import cv2  # OpenCV for webcam capture and frame processing
import mediapipe as mp  # Google's MediaPipe for gesture recognition and hand landmark detection

from .events import create_landmark_event
from .swipe_recognizer import detect_swipe

# Gesture Recognizer Task Model Path
MODEL_PATH = "models/gesture_recognizer.task"

# Intial webcam preview window dimensions
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540

# Fix to prevent gesture from canceling when skeleton flickers
HAND_LOSS_GRACE_FRAMES = 8

# Defines which hand landmarks should be connected to create the hand skeleton
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


def create_camera_window():
    window_name = "SlideKick Camera"

    # Create a normal resizable window
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    # Set Initial Window Size
    cv2.resizeWindow(window_name, WINDOW_WIDTH, WINDOW_HEIGHT)  # 960 x 540

    return window_name


def create_recognizer_options():
    # VIDEO mode allows MediaPipe to track the hand across consecutive frames
    options = mp.tasks.vision.GestureRecognizerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.40,
        min_hand_presence_confidence=0.40,
        min_tracking_confidence=0.40,
    )

    return options


def convert_frame_to_mediapipe(frame):
    # Mirror the image so the preview behaves like a normal webcam.
    frame = cv2.flip(frame, 1)

    # Converts OpenCV frames from BGR to RGB so that it can be fed to MediaPipe
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Converts the RGB frame into a MediaPipe image so that it can be processed by MediaPipe
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

    return frame, mp_image


def get_landmark_points(hand_landmarks, frame):
    # Gets the current frame dimensions so normalized coordinates can be converted into pixels
    frame_height, frame_width, _ = (
        frame.shape
    )  # floating "_" is ignoring the color channel value which we dont need

    # Stores the pixel coordinates for each detected hand landmark
    landmark_points = []

    # Draws each detected hand landmark directly onto the webcam frame
    for landmark in hand_landmarks:
        # Converts the landmark's normalized X coordinate into a pixel X coordinate
        x = int(landmark.x * frame_width)

        # Converts the landmark's normalized Y coordinate into a pixel Y coordinate
        y = int(landmark.y * frame_height)

        # Stores the landmark's pixel coordinates
        landmark_points.append((x, y))

    return landmark_points


def draw_hand_skeleton(frame, landmark_points):
    # Defines how the hand skeleton lines will be drawn
    line_color = (255, 255, 255)
    line_thickness = 2

    # Draws lines between connected hand landmarks
    for start_index, end_index in HAND_CONNECTIONS:
        start_point = landmark_points[start_index]
        end_point = landmark_points[end_index]

        cv2.line(frame, start_point, end_point, line_color, line_thickness)

    # Defines how each landmark point will be drawn
    circle_radius = 5
    circle_color = (0, 255, 0)
    circle_thickness = -1

    # Draws each landmark point over the hand skeleton
    for point in landmark_points:
        cv2.circle(frame, point, circle_radius, circle_color, circle_thickness)


def draw_recognition_diagnostic(
    frame,
    gesture_name,
    confidence,
    recognition_enabled=True,
):
    status = "ON" if recognition_enabled else "OFF"

    text_x = 20
    recognition_text_y = 30
    gesture_text_y = 60
    confidence_text_y = 90

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    text_color = (255, 255, 255)
    text_thickness = 2

    cv2.putText(
        frame,
        f"Recognition: {status}",
        (text_x, recognition_text_y),
        font,
        font_scale,
        text_color,
        text_thickness,
    )

    cv2.putText(
        frame,
        f"Gesture: {gesture_name}",
        (text_x, gesture_text_y),
        font,
        font_scale,
        text_color,
        text_thickness,
    )

    cv2.putText(
        frame,
        f"Confidence: {confidence:.2f}",
        (text_x, confidence_text_y),
        font,
        font_scale,
        text_color,
        text_thickness,
    )


def process_hand_detection(
    result, frame, position_history, last_swipe_time, missed_hand_frames
):
    # Stores standardized recognition events generated during the current frame
    gesture_event = None
    landmark_event = None

    # Checks whether MediaPipe detected hand landmarks
    if result.hand_landmarks:
        # Hand was found again, so reset the missed-frame counter
        missed_hand_frames = 0

        # Gets the 21 hand landmarks from the first detected hand
        hand_landmarks = result.hand_landmarks[0]

        # Keeps track of the current time for this frame
        current_time = time.monotonic()

        # Creates a standardized SlideKick event containing the detected hand landmarks
        landmark_event = create_landmark_event(hand_landmarks, current_time)

        # Detects a swipe and returns the standardized gesture event along with the updated last swipe time
        gesture_event, last_swipe_time = detect_swipe(
            hand_landmarks, position_history, last_swipe_time, current_time
        )

        landmark_points = get_landmark_points(hand_landmarks, frame)

        draw_hand_skeleton(frame, landmark_points)

    else:
        # If skeleton disappeared for one frame increment
        missed_hand_frames += 1

        # Clears old movement data when the hand is no longer detected for multiple consecutive frames
        if missed_hand_frames >= HAND_LOSS_GRACE_FRAMES:
            position_history.clear()

    return gesture_event, landmark_event, last_swipe_time, missed_hand_frames


def should_close_window(window_name):
    # waitKey also allows OpenCV to process window events.
    key = cv2.waitKey(1) & 0xFF

    # Press Q to close the camera.
    if key == ord("q"):
        return True

    # Detects if the user clicked the X button
    return cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1


def emit_event(event, event_handler):
    # Sends a standardized recognition event to the application if an event handler is provided
    # If event exists and event handler exists, then send event
    if event is not None and event_handler is not None:
        event_handler(event)


def print_recognition_event(event):
    # Displays only gesture events for prototype testing
    if event.get("event_type") == "gesture":
        print(event)
    # Displays onyl landmarks events for prototype testing
    # if event.get("event_type") == "landmarks":
    #   print(event)


def run_camera(event_handler=None):
    window_name = create_camera_window()

    # 0 tells OpenCV to use the computer's default webcam.
    camera = cv2.VideoCapture(0)

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    camera.set(cv2.CAP_PROP_FPS, 30)

    options = create_recognizer_options()

    # Stores the most recent positions of the tracked hand landmark (timestamp, x, y)
    position_history: deque[tuple[float, float, float]] = deque(
        maxlen=45
    )  # Keep track at most 45 frames of history

    # Stores the time when the most recent swipe was detected
    last_swipe_time = 0

    # Stores how many frames skeleton has been missing for
    missed_hand_frames = 0

    if not camera.isOpened():
        print("Error: Could not open camera.")
        return

    # Creates the MediaPipe Gesture Recognizer using the configured model and recognition settings
    with mp.tasks.vision.GestureRecognizer.create_from_options(options) as recognizer:
        last_frame_time_stamp_ms = -1
        last_gesture_name = "none"
        last_gesture_confidence = 0.0

        while True:
            success, frame = camera.read()

            if not success:
                print("Error: Could not read frame.")
                break

            frame, mp_image = convert_frame_to_mediapipe(frame)

            frame_timestamp_ms = int(time.monotonic() * 1000)

            if frame_timestamp_ms <= last_frame_time_stamp_ms:
                frame_timestamp_ms = last_frame_time_stamp_ms + 1

            last_frame_time_stamp_ms = frame_timestamp_ms

            # Processes the MediaPipe image and returns detection results
            result = recognizer.recognize_for_video(mp_image, frame_timestamp_ms)

            gesture_event, landmark_event, last_swipe_time, missed_hand_frames = (
                process_hand_detection(
                    result, frame, position_history, last_swipe_time, missed_hand_frames
                )
            )

            if gesture_event is not None:
                last_gesture_name = gesture_event["gesture"]
                last_gesture_confidence = gesture_event["confidence"]

            # Sends detected gesture and landmark events through the recognition interface
            emit_event(gesture_event, event_handler)
            emit_event(landmark_event, event_handler)

            # Prompts inside camera window recognition diagnostic
            draw_recognition_diagnostic(
                frame, last_gesture_name, last_gesture_confidence
            )

            cv2.imshow(window_name, frame)

            if should_close_window(window_name):
                break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_camera(print_recognition_event)
