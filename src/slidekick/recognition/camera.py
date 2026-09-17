# OpenCV webcam capture and frame processing
import time  # Used to determine cooldown/debounce
from collections import (
    deque,
)  # Stores recent frame history for tracking dynamic gesture displacement

import cv2  # OpenCV for webcam capture and frame processing
import mediapipe as mp  # Google's MediaPipe for gesture recognition and hand landmark detection
from events import (
    create_gesture_event,
    create_landmark_event,
)  # Creates standardized SlideKick gesture and landmark event payloads

# Gesture Recognizer Task Model Path
MODEL_PATH = "models/gesture_recognizer.task"

# Intial webcam preview window dimensions
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540

# Minimum horizontal movement required to count as a potential swipe
SWIPE_THRESHOLD = 0.20  # 0.20 x 640 = 128 pixels (We keep value as normalize coordinate distance to be compatible to different resolutions)

# Defines how long the system must wait before another swipe can be detected
SWIPE_COOLDOWN = 0.75

# Maximum amount of time allowed for a hand movement to count as a swipe
MAX_SWIPE_DURATION = (
    0.50  # Helps differentiate between intentional swipes and repositioning
)

# Minimum percentage of frame movements that must travel in the same direction
MIN_DIRECTION_CONSISTENCY = 0.75


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
    # Configures MediaPipe to use the Gesture Recognizer model in image-processing mode
    options = mp.tasks.vision.GestureRecognizerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=mp.tasks.vision.RunningMode.IMAGE,
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


def detect_swipe(hand_landmarks, position_history, last_swipe_time, current_time):
    # Stores a gesture event if a valid swipe is detected
    gesture_event = None

    # Uses landmark 9 (base of middle finger) near the center of the hand to track hand movement
    tracked_landmark = hand_landmarks[9]

    # Stores the time and horizontal position of the tracked Landmark
    position_history.append((current_time, tracked_landmark.x))

    if len(position_history) > 1:
        # Get the oldest and newest recorded time and horizontal positions
        starting_time, starting_x = position_history[0]
        ending_time, ending_x = position_history[-1]

        # Calculates how far the hand moved horizontally
        x_displacement = ending_x - starting_x

        # Calculates how long the hand movement took
        movement_duration = ending_time - starting_time

        # Stores the horizontal movement between each recorded frame
        frame_movements = []  # A swipe should look like "0.30 -> 0.35 -> 0.41 -> 0.48 -> 0.56 -> 0.64"
        # A non swipe would look like "+0.05 -> -0.03 -> +0.07 -> -0.04 -> +0.06"

        for index in range(1, len(position_history)):
            previous_x = position_history[index - 1][1]
            current_x = position_history[index][1]

            frame_movements.append(current_x - previous_x)

        # Counts how many recorded movements traveled right or left
        right_movements = sum(movement > 0 for movement in frame_movements)

        left_movements = sum(movement < 0 for movement in frame_movements)

        # Calculate the percentage of movements traveling in each direction
        right_consistency = right_movements / len(frame_movements)
        left_consistency = left_movements / len(frame_movements)

        # Checks whether the movement happened quickly enough to be considered a swipe
        valid_duration = movement_duration <= MAX_SWIPE_DURATION

        # Checks whether enough time has passed since the previous detected swipe
        cooldown_complete = ending_time - last_swipe_time >= SWIPE_COOLDOWN

        # Checks if the hand moved far enough horizontally to count as a potential swipe
        if (
            x_displacement >= SWIPE_THRESHOLD
            and right_consistency >= MIN_DIRECTION_CONSISTENCY
            and valid_duration
            and cooldown_complete
        ):
            # Creates a standardized SlideKick event for the detected right Swipe
            gesture_event = create_gesture_event("swipe_right", ending_time)

            last_swipe_time = ending_time

            # Once swipe is accepted, clear and start measuring new motion
            position_history.clear()

        elif (
            x_displacement <= -SWIPE_THRESHOLD
            and left_consistency >= MIN_DIRECTION_CONSISTENCY
            and valid_duration
            and cooldown_complete
        ):
            # Creates a standardize SlideKick event for the detected left swipe
            gesture_event = create_gesture_event("swipe_left", ending_time)

            last_swipe_time = ending_time

            # Once swipe is accepted, clear and start measuring new motion
            position_history.clear()

    # Return should look like
    #     No swipe:
    #     (None, 0)
    # or
    #     Right swipe:
    #     ({"event_type": "gesture", ...}, 12345.6)
    return gesture_event, last_swipe_time


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


def process_hand_detection(result, frame, position_history, last_swipe_time):
    # Stores standardized recognition events generated during the current frame
    gesture_event = None
    landmark_event = None

    # Checks whether MediaPipe detected hand landmarks
    if result.hand_landmarks:
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

        # #Temporary for Testing
        # #Displays the standardized gesture event for prototype verification
        # if gesture_event is not None:
        #     print(gesture_event)

        landmark_points = get_landmark_points(hand_landmarks, frame)

        draw_hand_skeleton(frame, landmark_points)

    else:
        # Clears old movement data when the hand is no longer detected
        position_history.clear()

    return gesture_event, landmark_event, last_swipe_time


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
    # Displays recognition events for prototype testing
    print(event)


def run_camera(event_handler=None):
    window_name = create_camera_window()

    # 0 tells OpenCV to use the computer's default webcam.
    camera = cv2.VideoCapture(0)

    options = create_recognizer_options()

    # Stores the most recent positions of the tracked hand landmark
    position_history = deque(maxlen=10)  # Keep track at most 10 frames of history

    # Stores the time when the most recent swipe was detected
    last_swipe_time = 0

    if not camera.isOpened():
        print("Error: Could not open camera.")
        return

    # Creates the MediaPipe Gesture Recognizer using the configured model and recognition settings
    with mp.tasks.vision.GestureRecognizer.create_from_options(options) as recognizer:
        while True:
            success, frame = camera.read()

            if not success:
                print("Error: Could not read frame.")
                break

            frame, mp_image = convert_frame_to_mediapipe(frame)

            # Processes the MediaPipe image and returns detection results
            result = recognizer.recognize(mp_image)

            gesture_event, landmark_event, last_swipe_time = process_hand_detection(
                result, frame, position_history, last_swipe_time
            )

            # Sends detected gesture and landmark events through the recognition interface
            emit_event(gesture_event, event_handler)
            emit_event(landmark_event, event_handler)

            cv2.imshow(window_name, frame)

            if should_close_window(window_name):
                break

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_camera(print_recognition_event)
