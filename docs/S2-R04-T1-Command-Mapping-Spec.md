# S2-R04-T1: Presentation Command Mapping Specification

## 1. Purpose

This document defines the command mappings and error behavior used by SlideKick's Native Helper to control presentation software.

The Native Helper runs directly on the host operating system and uses Python's `pyautogui` library to simulate keyboard input. Because the implementation sends standard presentation keyboard shortcuts rather than communicating with a platform-specific API, the MVP is designed to support presentation applications such as Microsoft PowerPoint, Google Slides, and Apple Keynote through a common keyboard-control interface.

## 2. Command Mappings

The Native Helper accepts the following presentation commands:

| SlideKick Command | Keyboard Input | Behavior |
|---|---|---|
| `next` | Right Arrow | Advances the presentation to the next slide. |
| `previous` | Left Arrow | Returns the presentation to the previous slide. |
| `pause` | `B` | Blacks out the presentation screen, temporarily hiding the current slide. |
| `resume` | `B` | Removes the black screen and returns to the current slide. |

### 2.1 Next

The `next` command maps to the **Right Arrow** key.

```text
next -> Right Arrow
```

When executed, the Native Helper sends a Right Arrow keystroke to the currently focused presentation application.

### 2.2 Previous

The `previous` command maps to the **Left Arrow** key.

```text
previous -> Left Arrow
```

When executed, the Native Helper sends a Left Arrow keystroke to the currently focused presentation application.

### 2.3 Pause

The `pause` command maps to the **B** key.

```text
pause -> B
```

The `B` shortcut blacks out the presentation screen. SlideKick treats this state as a paused presentation.

### 2.4 Resume

The `resume` command also maps to the **B** key.

```text
resume -> B
```

Because the black-screen shortcut behaves as a toggle, pressing `B` again restores the currently active slide.

For the Sprint 2 MVP, SlideKick does not independently track whether the presentation is currently blanked. The command assumes the presentation application is in the expected state when `pause` or `resume` is received.

## 3. Error Behavior

Because `pyautogui` simulates input at the operating-system level, it does not receive presentation state information from PowerPoint, Google Slides, Keynote, or other presentation applications.

The Native Helper therefore reports whether it successfully attempted to execute a command rather than whether the presentation application successfully changed state.

### 3.1 Successful Command

When a recognized command is received and the associated `pyautogui` operation completes without raising an exception, the Native Helper returns a success result.

Example:

```json
{
  "status": "success",
  "command": "next"
}
```

### 3.2 Invalid Command

If the Native Helper receives a command that is not one of the supported command strings:

- `next`
- `previous`
- `pause`
- `resume`

the command is rejected without sending a keyboard input.

Example:

```json
{
  "status": "error",
  "error": "Invalid Command",
  "command": "forward"
}
```

### 3.3 Native Execution Error

If `pyautogui` raises an exception while attempting to send the required keystroke, the Native Helper catches the exception and reports a Native Execution Error.

Possible causes include operating-system accessibility restrictions, permission problems, or another failure preventing simulated keyboard input.

Example:

```json
{
  "status": "error",
  "error": "Native Execution Error",
  "command": "next",
  "message": "Unable to execute native keyboard input."
}
```

The exception is handled by the Native Helper rather than allowing the process to terminate unexpectedly.

## 4. MVP Limitations

The Native Helper operates using simulated keyboard input and therefore does not directly communicate with the presentation application.

As a result:

1. The presentation window must have keyboard focus when a command is executed.
2. A successful Native Helper response means that the keystroke was successfully issued; it does not guarantee that the presentation application acted on the keystroke.
3. SlideKick does not currently verify the active presentation application.
4. The `pause` and `resume` operations both use the `B` toggle and depend on the presentation being in the expected state.
5. Presentation-state detection may be added in a future iteration if more precise control is required.

## 5. Command Flow

The command-processing flow for the Sprint 2 implementation is:

```text
Command Received
      |
      v
Validate Command
      |
      +---- Invalid ----> Return "Invalid Command"
      |
    Valid
      |
      v
Map Command to Keystroke
      |
      v
Execute with pyautogui
      |
      +---- Exception --> Return "Native Execution Error"
      |
    Success
      |
      v
Return Success Status
```

## 6. Summary

S2-R04-T1 establishes a platform-agnostic MVP command interface for presentation control.

The four supported commands are:

```text
next     -> Right Arrow
previous -> Left Arrow
pause    -> B
resume   -> B
```

The Native Helper reports one of three result conditions:

```text
Success
Invalid Command
Native Execution Error
```

This design keeps presentation-control logic independent from the higher-level SlideKick application while allowing the Native Helper to operate directly on the host machine without Docker or Lando.