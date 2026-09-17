# Keyboard Navigation Testing

Manual test of the dashboard shell from SCRUM-76, run against
`http://localhost:5173` (via `lando frontend-dev`).

## What was tested

Tabbed through the page from load, on each of the three routes
(Dashboard, Session, Settings).

## Findings

- **Tab order**: Tab moves through the three nav links in order (Dashboard,
  Session, Settings), left to right, matching the visual order. No hidden or
  out-of-order elements.
- **Focus visibility**: Each nav link shows a visible focus outline when
  tabbed to (browser default outline, not suppressed by any CSS).
- **Enter**: Pressing Enter on a focused nav link activates it and navigates
  to that page. Works correctly.
- **Space**: Pressing Space on a focused nav link does nothing. This is
  expected, not a bug — the nav items are `<a>` links (via React Router's
  `NavLink`), and standard browser behavior only treats Space as an activate
  key for `<button>` elements, not links.
- **Active page indicator**: The current page's nav link is visually marked
  (underline + color) so a keyboard user tabbing through can tell which page
  they're on, not just sighted mouse users.
- **Page title**: `<title>` was still the generic "frontend" placeholder from
  the Vite template — fixed to "SlideKick" during this pass so screen reader
  users and browser tab switching get a meaningful title.

## Not yet testable

There's only one focusable region right now (the nav). Once real page
content is built out (buttons, forms, camera controls on the Session page),
this doc should be revisited to test tab order and focus through that
content too — headings, ARIA landmarks, and any custom controls added for
gesture settings.

## Known gaps

- No skip-to-content link yet. Not a problem with only 3 nav items, but
  worth adding once page content grows, so keyboard users don't have to tab
  through the whole nav on every page.
- No ARIA landmarks beyond the default `<header>`/`<nav>`/`<main>` HTML
  elements used in `Layout.tsx`. These already get implicit ARIA roles
  (banner/navigation/main) from the browser, so this is fine as-is for now.
