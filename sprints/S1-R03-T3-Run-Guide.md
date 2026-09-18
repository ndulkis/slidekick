# S1-R03-T3 Recognition Prototype Run Guide

# Purpose

This guide documents the steps required to reproduce and run the SlideKick Sprint 1 recognition prototype.

# Prerequisites
-Git
-Docker Desktop
-Lando
-Python 3.11
-Python virtual environment
-Working webcam

# Repository Setup
Navigate to the SlideKick repository:

cd C:\SchoolProjects\SlideKick\slidekick

Switch to the Sprint 1 recognition branch if needed:

git switch s1-r03-t2-recognition-prototype

Pull the latest changes:

git pull

Confirm that the MediaPipe model exists at:

models/gesture_recognizer.task

# Lando Environment

Start Docker Desktop.

From the repository root, start Lando:

lando start

Verify the project environment:

lando verify

A successful verification should confirm that the project dependencies, linting, formatting, tests, and frontend build pass.

# Running the Recognition Prototype

Activate the Python virtual environment:

.\.venv\Scripts\Activate.ps1

The terminal should show (.venv) when the virtual environment is active.

Run the recognition prototype:

python src\slidekick\recognition\camera.py

The webcam window should open.

When a hand is visible, MediaPipe should detect the hand landmarks and display the hand skeleton.

The current Sprint 1 prototype recognizes:

swipe_right

swipe_left

# Expected Output

When a right swipe is detected:

{'event_type': 'gesture', 'gesture': 'swipe_right', 'timestamp': 15590.828}

When a left swipe is detected:

{'event_type': 'gesture', 'gesture': 'swipe_left', 'timestamp': 15592.431}

The prototype can also generate landmark events containing the normalized x, y, and z coordinates of the detected hand landmarks.

# Stopping the Prototype

Close the webcam window or stop the program with:

Ctrl + C

Deactivate the Python virtual environment:

deactivate

Lando can be stopped with:

lando stop

# Verification

Run:

lando verify

A successful result should show that all environment, linting, formatting, testing, and frontend build checks pass.

The prototype should also be manually checked by:

Confirming the webcam opens

Confirming hand landmarks are displayed

Performing a right swipe

Performing a left swipe

Confirming normal non-swipe movement does not usually trigger a swipe

# Known Limitations

The webcam prototype currently runs through the host Python virtual environment instead of directly inside the Lando container.

Poor lighting can cause the hand landmark skeleton to flicker or disappear.

Losing hand tracking can reset the swipe movement history.

Swipe detection currently uses fixed thresholds for distance, duration, direction consistency, and cooldown.

The current thresholds have not been tested across multiple users or different camera setups.

Only left and right swipe gestures are included in the Sprint 1 prototype.

Current latency results measure recognition processing latency only and not full end-to-end presentation control latency.