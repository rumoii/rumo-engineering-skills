# Accessibility

Read this before handing back any UI change. It covers the checks that catch most real barriers; follow the product's stated accessibility standard when it sets a stricter target.

## Structure

- Use native elements for their purpose: `button` for actions, `a` for navigation, real headings in order, lists for lists, tables for tabular data.
- Give every form control a visible label tied to it. Placeholder text is not a label.
- Give meaningful images a short text alternative; mark decorative ones as decorative.
- Add ARIA only when no native element expresses the role or state, and keep its state in sync with the UI.

## Keyboard And Focus

- Every action reachable by mouse is reachable by keyboard, in a sensible tab order, with no traps.
- Focus is always visible. Do not remove the outline without providing an equally clear replacement.
- A dialog moves focus into itself on open, keeps it inside while open, closes on Escape when dismissal is safe, and returns focus to the control that opened it.
- After an action changes the page (a row deleted, a step completed, a route changed), place focus somewhere predictable.

## Color And Text

- Contrast: at least 4.5:1 for normal text and 3:1 for large text, icons, focus indicators, and control boundaries, in every supported theme and state.
- Never carry meaning by color alone; pair it with text, an icon, or a pattern.
- The layout stays usable at 200% zoom and with larger system text: nothing clipped, overlapping, or hidden behind fixed bars.

## Forms And Feedback

- Mark required fields in text, not only with a symbol or color.
- Associate each error message with its field, describe how to fix it, and move focus or announce the summary when submission fails.
- Announce asynchronous results (saved, failed, loading finished) through a live region or an equivalent mechanism the component library provides.

## Motion And Timing

Honor the reduced-motion preference, avoid flashing content, and give users a way to extend or disable time limits.

## How To Check

1. Walk the main flow with the keyboard only, watching focus.
2. Run an automated checker such as axe when the project or browser tooling provides one; treat its result as a floor, not proof.
3. Check contrast of new colors in each theme.
4. Zoom to 200% at a narrow viewport.

Report which of these ran. Automated checks and source inspection do not prove screen-reader behavior; say so when no screen reader was used.
