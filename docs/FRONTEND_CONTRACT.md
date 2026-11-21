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

The user-approved direction is a professional pixel-inspired workspace, using deep navy, warm ivory and muted teal. The live components remain React/Next.js and retain the existing API contract.

### Palette

| Role | Midnight | Daylight |
| --- | --- | --- |
| Background | #151A2C | #F0F2F4 |
| Surface | #20283E | #FFFFFF |
| Text | #F8EFD8 | #20283E |
| Secondary text | #A8B4C7 | #526077 |
| Input border | #58657D | #79869B |
| Primary action | #64BFA8 | #29705F |
| Primary action text | #102721 | #FFFFFF |
| Focus | #8DE3B6 | #29705F |

Use coral #EE8B76 for the draft edge, mint #8DE3B6 for supported evidence, and amber #EFB957 for warnings. Pair each status with a readable label.

### Layout and type

A persistent sidebar contains the workspace, tutorial, and appearance control. The workspace uses two columns for draft and review on desktop, collapsing to a single column below 980px. Conversation history and settings remain accessible through dialogs. The review placeholder explains the result before generation. Both generation and regeneration display a dedicated processing view; component state retains drafts and the prior reply until completion or failure.

Use a clean system sans-serif for messages, small monospace labels for pixel character, square corners, restrained offset shadows, and crisp pixel artwork. Keep text fields and body content readable and expose keyboard focus.

### Animation integration

The original Remotion compositions are bundled as local MP4 assets in public/animations. A shared PixelAnimation component honours live changes to prefers-reduced-motion and pauses decorative video when reduced motion is requested.

- Rage meter: overall process on the dedicated processing view, for both initial generation and regeneration. Decorative only; it is not a measured emotion score or truthful completion percentage.
- Magnifying glass: evidence-review panel on the processing view and empty evidence/reply review state. The existing API has no live stage events; the UI describes the workflow without marking timed stages as complete.
- Folder/files: conversation history entry and import dialog.

Animations do not replace processing, completion, or error text. Manager messages and emotional drafts remain in component state and are not written to browser storage by these visuals. Generation and import continue to use the existing client.

### Availability and accessibility

Quick Tone Rewrite remains unavailable pending the draft-only API. The supported evidence workflow retains all three tones, editable results, source-backed evidence, uncertainty labels, retries and explicit history import/deletion.

Use accessible labels, native radio controls, focus indicators, responsive layouts and semantic status/error regions. The existing browser mock remains explicitly labelled Synthetic demo.
