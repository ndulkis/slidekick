# S1-R03-T2 Recognition Event Payloads

SlideKick's recognition prototype converts MediaPipe recognition results into
standardized event payloads. These events allow other application components
to consume recognition data without depending directly on MediaPipe objects.

## Gesture Event

Gesture events are generated when the recognition pipeline detects a valid
dynamic gesture.

### Example

{'event_type': 'gesture', 'gesture': 'swipe_left', 'timestamp': 15590.828}

#### Fields
event_type - Identifies the payload as a gesture event
gesture - contains the standardized name of the detected gesture (Ex: swipe_right, swipe_left)
timestamp - Stores the time at which the gesture was detected (Generate using Python's time.monotonic())

## Landmark Event
Landmark events contain the normalized hand landmark information returned from MediaPipe

### Example
{'event_type': 'landmarks', 'timestamp': 17789.906, 'landmarks': NormalizedLandmark(x=0.18580153584480286, y=0.9860022664070129, z=-0.044394489377737045, visibility=None, presence=None, name=None)}

#### Fields
event_type - Identifies the payload as a landmark event
timestamp - Stores the time associated with the detected frame
landmarks - Contains the detected hand landmarks
id - Represents the MediaPipe landmark index from 0 through 20
x - Stores the normalized horizontal position of the landmark
y - Stores the normalized vertical position of the landmark
z - Stores the relative depth value of the landmark

## Event Flow
Webcam -> OpenCV Frame -> MediaPipe Gesture Recognition -> Hand Landmarks / Dynamic Swipe Detection -> events.py -> Standardized SlideKick Event -> Callback Interface -> Application Consumer

## Prototype Verification

# Gesture Event Verification - Run the SlideKick camera prototype and perform a clear left or right swipe in front of the webcam. Verify that the terminal outputs a standardized gesture event containing the event type, detected gesture name, and timestamp.

# Landmark Event Verification - Run the SlideKick camera prototype with a hand visible in the webcam. Verify that the terminal outputs a standardized landmark event containing the event type, timestamp, and normalized x, y, and z coordinates for the detected hand landmarks.

# Example Output (Gesture Event)
{'event_type': 'gesture', 'gesture': 'swipe_left', 'timestamp': 15578.531}
{'event_type': 'gesture', 'gesture': 'swipe_right', 'timestamp': 15581.156}
{'event_type': 'gesture', 'gesture': 'swipe_left', 'timestamp': 15582.14}
{'event_type': 'gesture', 'gesture': 'swipe_right', 'timestamp': 15584.14}
{'event_type': 'gesture', 'gesture': 'swipe_left', 'timestamp': 15584.906}
{'event_type': 'gesture', 'gesture': 'swipe_right', 'timestamp': 15590.015}
{'event_type': 'gesture', 'gesture': 'swipe_left', 'timestamp': 15590.828}

# Example Output (Landmark Event)
{'event_type': 'landmarks', 'timestamp': 17789.687, 'landmarks': NormalizedLandmark(x=0.19670352339744568, y=0.7824712991714478, z=-0.0781472772359848, visibility=None, presence=None, name=None)}
{'event_type': 'landmarks', 'timestamp': 17789.718, 'landmarks': NormalizedLandmark(x=0.16408580541610718, y=0.831932783126831, z=-0.06370619684457779, visibility=None, presence=None, name=None)}
{'event_type': 'landmarks', 'timestamp': 17789.75, 'landmarks': NormalizedLandmark(x=0.15623152256011963, y=0.8613454103469849, z=-0.04807988926768303, visibility=None, presence=None, name=None)}
{'event_type': 'landmarks', 'timestamp': 17789.781, 'landmarks': NormalizedLandmark(x=0.1571214199066162, y=0.9024664759635925, z=-0.017981544137001038, visibility=None, presence=None, name=None)}
{'event_type': 'landmarks', 'timestamp': 17789.812, 'landmarks': NormalizedLandmark(x=0.16441921889781952, y=0.9386788010597229, z=-0.03822655603289604, visibility=None, presence=None, name=None)}
{'event_type': 'landmarks', 'timestamp': 17789.843, 'landmarks': NormalizedLandmark(x=0.17367976903915405, y=0.9637101292610168, z=-0.031171495094895363, visibility=None, presence=None, name=None)}
{'event_type': 'landmarks', 'timestamp': 17789.906, 'landmarks': NormalizedLandmark(x=0.18580153584480286, y=0.9860022664070129, z=-0.044394489377737045, visibility=None, presence=None, name=None)}

