# Web App Frontend Contract

Rage-to-Reply is a browser-based workplace reply assistant with two modes. See [Product Specification](PRODUCT_SPEC.md) for product behaviour and [API Contract](API_CONTRACT.md) for the current wire format.

## Reply Modes

| Mode | Input | Result |
| --- | --- | --- |
| Rewrite with Evidence | Explicitly import conversation history from Slack in the supported JSON format. Enter the manager message and a draft, then choose a tone. | Editable reply, manager interpretation, supporting evidence, unverified claims and warnings. |
| Quick Tone Rewrite | Type a draft and choose a tone. No manager message or Slack import is required. | Editable tone-adjusted text generated from the current draft. |

## Reply Flow

1. **Choose a mode.** Explain the inputs and expected result before the user enters text.
2. **Enter the draft.** In Rewrite with Evidence, show the history import and manager-message fields. In Quick Tone Rewrite, show the draft and tone controls.
3. **Generate.** Offer Diplomatic, Neutral and Assertive. Start generation when the user selects the primary action. Announce processing and retain the inputs for retry or regeneration.
4. **Review and edit.** Keep the previous reply visible until regeneration succeeds. In Rewrite with Evidence, display source-backed claims, unverified claims and warnings separately.
5. **Finish in the web workspace.** Users review and edit the final text in the browser.

**Hosted sign-in.** In the hosted build (`NEXT_PUBLIC_R2R_AUTH=invite`), visitors without a session open `/login`. There they enter their invite code, then return to the workspace. A personal sign-in link (`/login#<invite code>`) signs in without typing. The code stays in the URL fragment, which is never sent to the server, and the page removes it from the address bar immediately. If the API reports an expired session, the browser returns to `/login`. Show readable errors for an invalid code and for too many attempts. The local demo and the browser mock never show sign-in. See [Hosted invite-code sessions](API_CONTRACT.md#hosted-invite-code-sessions).

Quick Tone Rewrite requires backend support for draft-only generation without memory retrieval. The existing evidence endpoint requires a manager message and searches imported history. Confirm the draft-only API with the backend owner before connecting the mode.

## Data Handling and Acceptance Criteria

- The typed reply workflow runs in a normal browser tab without microphone or Slack permissions. Optional dictation starts only on user request, discloses possible browser-provider processing, and appends final text to the editable draft. The app stores no audio and generation still requires the primary action.
- Keep the emotional draft in page state for the current interaction. Keep draft content out of browser storage and logs. Save conversation history only through explicit import.
- Show field errors, timeouts and retry actions with readable text. Guard against duplicate submissions while a request is pending.
- Verify generation and regeneration in all three tones, editable results, loading and retry in both modes. In Rewrite with Evidence, verify separate evidence and uncertainty states, empty history, and history import, review and deletion. In Quick Tone Rewrite, verify that previously imported history is excluded from generation.
- A result has no required clipboard or messaging action. The web app never sends workplace messages.

## Visual Design System

The current Web App uses a **pixel-inspired editorial workspace**. Midnight is the default appearance. Daylight uses the same layout and visual hierarchy with cooler, lighter surfaces. Shared styles are loaded first, and the [pixel workspace stylesheet](../src/frontend/styles/pixel-workspace.css) supplies the active theme values.

### Colour tokens

| Role | CSS token | Midnight | Daylight |
| --- | --- | --- | --- |
| Page and sidebar | `--background` | `#151A2C` | `#F0F2F4` |
| Cards and dialogs | `--surface` | `#20283E` | `#FFFFFF` |
| Inputs | `--input` | `#181F32` | `#F7F9FA` |
| Primary text | `--text` | `#F8EFD8` | `#20283E` |
| Secondary text | `--muted` | `#A8B4C7` | `#526077` |
| Input and control borders | `--border` | `#58657D` | `#79869B` |
| Panel dividers | `--line` | `#344158` | `#D7DEE6` |
| Primary action | `--primary` | `#64BFA8` | `#29705F` |
| Primary action hover | `--primary-hover` | `#83D6BE` | `#225F50` |
| Primary action pressed | `--primary-pressed` | `#52A992` | `#1C5144` |
| Text on primary controls | `--primary-text` | `#102721` | `#FFFFFF` |
| Keyboard focus | `--focus` | `#8DE3B6` | `#29705F` |
| Draft edge | `--draft-accent` | `#EE8B76` | `#B65F43` |

| Shared status role | CSS token | Both themes |
| --- | --- | --- |
| Supported evidence | `--calm` | Mint `#8DE3B6` |
| Warning or uncertainty | `--warning` | Amber `#EFB957` |
| Generation error | `--rage` | Coral `#EE8B76` |
| Text on solid status badges | `--accent-text` | Navy `#151A2C` |

### Applying the palette

- Use the page background for navigation and the surface colour for the draft and reply panels. The draft has a coral or rust top edge, and the reply panel has a teal top edge. Use dividers for grouping.
- Use teal for Generate, Regenerate, selected states and the pixel wordmark. Primary buttons use the theme's primary text colour and a small offset shadow. Secondary buttons use a transparent background with a visible border.
- Keep the editable **Suggested Reply** above Insights, Warnings and supporting evidence. Show one concern and one priority warning by default. Prefer a conflicting-history warning when one exists. Keep the remaining analysis and warnings in native expandable details.
- Use mint for a labelled, source-backed claim. Use amber for warnings and coral for failed generation. Keep evidence excerpts readable in normal text and place available sender, timestamp and source beside the record.

Measured text contrast on the card surface is 12.78:1 in Midnight and 14.64:1 in Daylight. The lowest checked contrast across the primary button states is 5.58:1 in Midnight and 5.87:1 in Daylight. Keep status labels readable with navy text on their solid fills. The current mint outline badge on white measures 1.52:1 for text, and the Midnight input border measures 2.79:1 against the input fill. These existing pairings still need accessibility review.

### Layout and typography

The sidebar contains **Reply workspace**, **How it works**, and the **Appearance** selector. At 980px and below, the two-column workspace stacks into one column. At 680px and below, the fixed sidebar becomes top navigation. History and settings open in dialogs.

Use system sans-serif for draft and reply text, and monospace for compact pixel-style labels. At the default text setting, body text is `1rem`, workspace panel titles are `1.25rem`, and labels and input text are `0.875rem`. Use rem units so **Small**, **Default**, **Large**, and **Extra large** scale the workspace together. Use near-square corners, fine borders and restrained offset shadows.

### Animation and waiting states

- The angry pixel face eats one decorative word per click or focused Enter or Space. It swells, bursts into pixel fragments, and returns as a smile. Automatic feeding, Skip, and reduced-motion support keep the interaction optional.
- The 24-block pixel wait meter tracks the API request independently of the face. It initially shows elapsed time. When previous successful requests provide a basis, it shows labelled estimated time. It reaches full only after API success.
- The **Suggested Reply** appears after API success and animation completion. On failure, show a message and Retry and retain the draft and any previous reply.
- The shared [PixelAnimation component](../src/frontend/shared/PixelAnimation.tsx) uses transparent animated PNG assets for the folder and evidence graphics. A picture media query chooses a still image for reduced motion. Keep waiting states and errors readable as text.

### Availability and accessibility

Quick Tone Rewrite remains unavailable pending the draft-only API. The supported evidence workflow retains all three tones, editable results, source-backed evidence, uncertainty labels, retries and explicit history import/deletion.

Use accessible labels, native radio controls, focus indicators, responsive layouts and semantic status/error regions. The existing browser mock remains explicitly labelled Synthetic demo.
