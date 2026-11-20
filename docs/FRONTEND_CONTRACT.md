# Desktop Reply Assistant Frontend Contract

The assistant helps users reply to a manager in a supported desktop chat app. The user selects a chat window and starts a reply. The assistant reads the relevant visible message, rewrites the user's typed or spoken response, and fills the existing chat composer. The user can edit the draft and sends it using the chat app's own controls.

## Permissions and Reading Scope

- Before requesting system access, explain what access the assistant needs and why. The operating system controls the permission prompt. The assistant lets the user select the chat window for each reply, even if system access has already been granted.
- Start reading only after the user selects a window and chooses **Start Reply**. Show the selected app and conversation, the message used for rewriting, and a **Stop** control while access is active. Limit reading to the selected window and the visible message needed for the reply.
- If access is denied or revoked, stop reading and filling the composer. Explain how to restore access and allow the user to keep editing their draft. Selecting **Stop** ends the session and prevents pending results from being inserted.

## Reply Flow

1. **Read the message.** Automatically extract the relevant manager message from the selected conversation and show it to the user. If the assistant cannot identify the message reliably, let the user select or paste the correct text.
2. **Capture input.** Offer typed input and a microphone button. Start recording only after the user chooses the microphone and grants access. Show a recording indicator and a stop control. Let the user edit the transcript. Typing remains available if microphone access is denied or transcription fails.
3. **Rewrite.** When the user chooses **Rewrite**, use the selected manager message and the user's draft. Before any cloud processing, disclose which message text, draft text, or audio will be sent and why. Show progress and preserve the draft for retry if rewriting fails.
4. **Fill the composer.** Confirm that the original window and conversation still match before inserting the rewrite. If the composer contains text, ask before replacing it. If the destination has changed or cannot be verified, keep the rewrite in the assistant and show why it was held. Only the user sends the message.

## Data Handling and Acceptance Criteria

- Keep raw drafts and transcripts only for the current interaction. The frontend does not persist raw audio or raw draft text or insert either into the chat composer.
- With system access granted, the assistant starts reading only after the user selects a window and starts a reply. Denying access, revoking access, or choosing **Stop** prevents further reading and insertion.
- Both typing and voice input can produce an editable draft in the original conversation. The chat thread changes only after the user sends the reply.
- Switching conversations during a rewrite leaves the new conversation untouched. An existing composer draft stays intact unless the user confirms replacement.

The team still needs to choose the first supported desktop chat app, the integration method for reading and filling, and the transcription provider. The placement of the rage meter, extracted facts, and event history will be defined separately.

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

**React Web / Browser Extension.** Apply the full design system to the app or extension's own surfaces. These surfaces support custom CSS, transitions, and interactive components.

**Slack Native Block Kit.** Use Slack's native blocks and controls. Slack renders its own styles, type, spacing, and radii. Use headers, labels, grouped blocks, and plain-text status updates to carry the hierarchy into Slack. Treat the custom colour tokens and animation rules as React Web and extension guidance. [Slack Block Kit reference](https://docs.slack.dev/reference/block-kit/)
