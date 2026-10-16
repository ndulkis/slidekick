# SlideKick Native Integration Test Checklist

## Overview
This document outlines the repeatable baseline tests for the native Windows helper API (`windows_helper.py`). It ensures that physical slide navigation commands (Next, Previous, Pause, Resume) execute correctly on the host operating system via HTTP requests.

## Prerequisites
1. The Python virtual environment is active (`.\.venv\Scripts\Activate.ps1`).
2. Project dependencies (Flask, PyAutoGUI) are installed.
3. A target presentation (PowerPoint or Google Slides) is open and currently in Full Screen / Presentation mode.

## 1. Automated Validation (Recommended)
This uses the included PowerShell script to automatically fire commands at the local server.

**Steps:**
1. Start the native helper in your primary terminal:
   ```powershell
   python windows_helper.py

2. Open a second PowerShell terminal in the project root and execute the test script:

PowerShell
.\scripts\test_slide_commands.ps1

3. Immediately click on your presentation to give it window focus.

Expected Results:

After 5 seconds, the presentation advances one slide forward. The terminal outputs a success status for the next command.

After pressing Enter to continue, the script waits 5 seconds and the presentation moves one slide backward. The terminal outputs a success status for the previous command.

2. Manual Validation
Use these steps to manually verify individual endpoints without the PowerShell script.

Steps:

Start the native helper: python windows_helper.py

Open a web browser and position it so you can still see your presentation window.

Trigger the following endpoints by navigating to them in the browser:

Next Slide: http://localhost:8000/next

Previous Slide: http://localhost:8000/previous

Pause (Black Screen): http://localhost:8000/pause

Resume: http://localhost:8000/resume

Expected Results:

The presentation must physically respond to each command.

The browser must display a 200 OK JSON response matching this structure: {"command": "<action>", "status": "success"}