# Design Quality

Read this before designing a page, component, or application that has no existing pattern to follow, or when the user asks for a better-looking interface. When the product already has a design system, brand guide, or adjacent pages, follow them; use the defaults here only to fill gaps.

## Set The Direction First

Before writing markup, state in a few lines:

- who uses the screen, how often, and on which devices;
- the main task the screen exists for and its single primary action;
- tone and density: a dense operations console and a calm onboarding page need different spacing, type, and color;
- fixed constraints: brand colors, fonts, component library, supported browsers, light and dark themes.

Every later choice should trace back to this direction. If the user gave none and the product offers no reference, propose one and treat it as an assumption to confirm.

## Hierarchy And Type

- Use a small type scale (four to six sizes) and keep to it. Build hierarchy with size, weight, and spacing before reaching for color.
- Choose the typeface deliberately: the product's font, a system stack, or a well-supported web font that fits the tone. Do not mix more than two families.
- Keep body text readable: about 45-80 characters per line and a line height around 1.4-1.6.
- One clear heading per region; the eye should find the primary action within a second.

## Spacing And Layout

- Take spacing from one base unit (commonly 4 or 8 pixels) and its multiples. Related items sit closer together than unrelated ones.
- Align to a grid or a small set of columns. Ragged left edges and one-off offsets read as mistakes.
- Give each region one primary action; secondary actions are visibly quieter, destructive ones are separated and confirmed.
- Design the narrow viewport too: decide what stacks, what collapses, and what scrolls, instead of letting it fall out of the wide layout.

## Color

- Start from neutral surfaces and text, add one accent for primary actions and focus, and reserve semantic colors (success, warning, danger, info) for status.
- Define colors as tokens or theme variables and reuse them; never invent a page-only palette.
- Check contrast for every text and control state, in each supported theme. Status must not rely on color alone.

## Components And States

Each interactive element needs its full set of states: default, hover, focus-visible, active, disabled, and, where data is involved, loading, empty, error, and partial data. Write the empty and error copy as real guidance: what happened and what the user can do next.

## Motion

Use motion only to explain a change: something appearing, moving, or updating. Keep it short (roughly 150-300 ms), avoid animating layout on every interaction, and honor the reduced-motion preference.

## Avoid The Template Look

These signal an interface nobody designed:

- decorative gradients, glows, or glass effects with no role in the hierarchy;
- emoji or mismatched icon sets standing in for a consistent icon family;
- everything centered, or every block wrapped in an identical card;
- default fonts and colors kept by inertia rather than choice;
- placeholder copy, fake metrics, or sample data left in a deliverable;
- several competing primary buttons on one screen.

## Check The Result

Render the page at a wide and a narrow viewport with realistic data, including a long name, an empty list, and an error; prefer Playwright with two viewport sizes for the screenshots, and say so when no browser automation is available. Compare the screenshots with the direction you set: hierarchy, spacing rhythm, color roles, and states. Fix what drifted, then run the accessibility check.
