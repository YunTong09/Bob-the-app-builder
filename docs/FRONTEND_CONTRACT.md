# Web App Frontend Contract

Rage-to-Reply is a browser-based workplace reply assistant. Users provide a manager's message and their own draft, choose a tone, and review an editable professional reply backed by authorised evidence when available. See [Product Specification](PRODUCT_SPEC.md) for feature priorities and [API Contract](API_CONTRACT.md) for request and response formats.

## Reply Flow

1. **Enter the context.** Provide labelled text fields for the manager's message and the employee's draft. Users type or paste text into the fields. Conversation history is managed through a separate, explicit import flow.
2. **Choose a tone and generate.** Offer Diplomatic, Neutral and Assertive. Validate required fields, submit through the web API client and announce the processing state. Keep the input and tone available for retry or regeneration.
3. **Review and edit.** Show the suggested reply in an editable field. Display the manager interpretation, supporting evidence, unverified claims and warnings separately. Include source details when available. On regeneration, keep the existing reply visible until the new request succeeds.
4. **Finish in the web workspace.** Users can review and edit the final text in the browser. The workspace ends at review and editing.

## Data Handling and Acceptance Criteria

- The reply workflow uses explicit form input and runs in a normal browser tab without system or Slack permissions.
- Keep the emotional draft in page state for the current interaction. Keep draft content out of browser storage and logs. Save conversation history only through explicit import.
- Show field errors, timeouts and retry actions with readable text. Guard against duplicate submissions while a request is pending.
- Verify generation and regeneration in all three tones, editable results, and separate evidence and uncertainty states. Verify loading, retry, empty history, and history import, review and deletion.
- A result has no required clipboard or messaging action. The web app never sends workplace messages.

## Visual Design System

- **Theme** — Corporate Chaos
- **Style** — Minimal, Playful & Clean

Use neutral surfaces, generous spacing, and clear hierarchy for a modern workplace AI assistant. Bring the theme through concise office-themed copy and subtle state changes. Keep violet accents small and reserve bright violet for primary actions and selected states. Use the dark background and surface in the dark theme. Avoid large purple fills, saturated gradients, decorative clutter, and heavy enterprise styling.

### Colour Tokens

| Token | Value | Use |
| --- | --- | --- |
| Primary | `#A78BFA` | Primary actions and selected states |
| Rage | `#FF6B6B` | Small rage indicators with a label or value |
| Warning | `#FFC857` | Small warning indicators with explanatory text |
| Calm | `#54D6BE` | Small calm or completion indicators with a label |
| Light Background | `#F7F7F8` | Light theme page background |
| Light Surface | `#FFFFFF` | Light theme cards and input surfaces |
| Dark Background | `#171326` | Dark theme page background |
| Dark Surface | `#251F39` | Dark theme cards and input surfaces |

| Token | Light theme | Dark theme |
| --- | --- | --- |
| Primary Text | `#211C2C` | `#F8F6FC` |
| Secondary Text | `#514B5D` | `#C6BED3` |
| Border | `#82798A` | `#8B809D` |
| Focus Indicator | `#503391` | `#D9CCFF` |

#### Approved Foreground and Background Pairings

Ratios below are the minimum across the explicitly listed backgrounds, rounded to two decimal places.

| Foreground | Background | Minimum contrast |
| --- | --- | --- |
| Light Primary Text | Light Background or Light Surface | 15.48:1 |
| Light Secondary Text | Light Background or Light Surface | 7.80:1 |
| Dark Primary Text | Dark Background or Dark Surface | 14.68:1 |
| Dark Secondary Text | Dark Background or Dark Surface | 8.78:1 |
| `#211C2C` text in either theme | Primary, Rage, Warning, or Calm fill | 5.97:1 |
| Light Border | Light Background or Light Surface | 3.88:1 |
| Dark Border | Dark Background or Dark Surface | 4.25:1 |
| Light Focus Indicator | Light Background or Light Surface | 8.82:1 |
| Dark Focus Indicator | Dark Background or Dark Surface | 10.52:1 |

Use a solid 2px focus outline with a 2px offset so it is adjacent to the approved theme background or surface, including around accent-filled controls. Keep the outline visible and unclipped. On light surfaces, use the theme border where an accent-filled control needs a visible boundary. Use accent swatches as supplementary cues alongside readable text. Render text on brand fills with `#211C2C`, since white text falls below 3:1 on each brand fill. Check any new pairing, transparency, or state variant against its actual adjacent colours. [WCAG 2.2 contrast requirements](https://www.w3.org/TR/WCAG22/#contrast-minimum) · [Non-text contrast](https://www.w3.org/TR/WCAG22/#non-text-contrast)

### Typography

Use the system font stack with a sans-serif fallback. Use 16px for body text, 14px for labels, and 20px for section headings. Keep body line height around 1.5.

### Spacing and Border Radius

Use the spacing scale `4 / 8 / 12 / 16 / 24 / 32px`. Use 8px radii for buttons and inputs, 12px for cards, and a pill radius for status badges.

### Animation

Use 120–200ms transitions for ordinary state changes. Use a subtle colour transition and fade for Rage → Calm. Keep controls operable during animations. Honour `prefers-reduced-motion` by replacing nonessential animations with immediate state changes and preserving the same status text.

### Accessibility

- Meet WCAG 2.2 AA contrast thresholds of at least 4.5:1 for normal text and 3:1 for large text and essential non-text interface components against adjacent colours.
- Support keyboard operation, a logical focus order, and a visible focus indicator.
- Pair error, success, and warning colours with explicit text.
- Give inputs descriptive labels. Expose AI processing and completion via an accessible status region such as `role="status"` in web interfaces. Communicate failures in accessible text.

### Platform Constraints

**React Web App.** Apply the full design system using CSS tokens, transitions and interactive components. Support responsive browser layouts and keyboard-first use. The active product UI runs in the browser. Archived Slack design and implementation notes live in the [Slack prototype tracker](progress/slack-integration-tracker.md).
