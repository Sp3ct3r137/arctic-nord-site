# Colour Reference — Arctic Nord

All colours used in this project, their Nord names, hex values, and roles.

## Polar Night (Backgrounds)

| Token   | Hex       | CSS Variable        | Role                                |
|---------|-----------|---------------------|-------------------------------------|
| nord0   | `#2E3440` | `--nord0`           | Page background                     |
| nord1   | `#3B4252` | `--nord1`           | Elevated surfaces (cards, nav)      |
| nord2   | `#434C5E` | `--nord2`           | Hover states, selection, inputs     |
| nord3   | `#4C566A` | `--nord3`           | Borders, muted / disabled text      |

## Snow Storm (Text)

| Token   | Hex       | CSS Variable        | Role                                |
|---------|-----------|---------------------|-------------------------------------|
| nord4   | `#D8DEE9` | `--nord4`           | Secondary / muted text              |
| nord5   | `#E5E9F0` | `--nord5`           | Primary body text                   |
| nord6   | `#ECEFF4` | `--nord6`           | Headings / high-emphasis text       |

## Frost (Interactive / Accent)

| Token   | Hex       | CSS Variable        | Role                                |
|---------|-----------|---------------------|-------------------------------------|
| nord7   | `#8FBCBB` | `--nord7`           | Calm accent, icons                  |
| nord8   | `#88C0D0` | `--nord8`           | Primary interactive accent          |
| nord9   | `#81A1C1` | `--nord9`           | Links, secondary accent             |
| nord10  | `#5E81AC` | `--nord10`          | Deep accent, badges                 |

## Orange Accent (from Aurora / nord12)

| Token         | Hex       | CSS Variable        | Role                                |
|---------------|-----------|---------------------|-------------------------------------|
| orange (nord12) | `#D08770` | `--orange`        | ⚡ CTA buttons, highlights, active states |
| orange-light  | `#E09880` | `--orange-light`    | Hover state for orange              |
| orange-dim    | `#A06050` | `--orange-dim`      | Pressed / active state              |

## Semantic Aliases

These are what component CSS should actually reference:

```css
--color-bg:         var(--nord0);   /* page background */
--color-surface:    var(--nord1);   /* raised surfaces */
--color-surface-2:  var(--nord2);   /* deeper raised */
--color-border:     var(--nord3);   /* dividers, borders */
--color-text:       var(--nord5);   /* body text */
--color-text-muted: var(--nord4);   /* secondary text */
--color-heading:    var(--nord6);   /* headings */
--color-accent:     var(--nord8);   /* primary accent (frost) */
--color-accent-dim: var(--nord9);   /* secondary accent */
--color-cta:        var(--orange);  /* call-to-action (orange) */
--color-cta-hover:  var(--orange-light);
```

## Why orange?

Nord's Aurora palette includes `nord12` (`#D08770`) — a warm muted orange.
It sits naturally against the cold blue-grey Polar Night backgrounds and
creates instant visual contrast for calls-to-action without breaking the
Arctic aesthetic. It reads as "warm" against the cold palette, drawing the
eye without screaming.
