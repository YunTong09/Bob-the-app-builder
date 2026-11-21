# Web App Frontend Contract

Rage-to-Reply is a browser-based workplace reply assistant with two modes. See [Product Specification](PRODUCT_SPEC.md) for product behaviour and [API Contract](API_CONTRACT.md) for the current wire format.

## Reply Modes

| Mode | Input | Result |
| --- | --- | --- |
| Rewrite with Evidence | Enter a draft and choose a tone. Optionally add the manager message and explicitly import conversation history. | Editable reply, manager interpretation when context is supplied, supporting evidence, unverified claims and warnings. |
| Quick Tone Rewrite | Type a draft and choose a tone. No manager message or Slack import is required. | Editable tone-adjusted text generated from the current draft. |

## Reply Flow

1. **Choose a mode.** Explain the inputs and expected result before the user enters text.
2. **Enter the draft.** In Rewrite with Evidence, show history import and a clearly optional manager-message field. A non-blank employee draft enables generation without a manager message or history. In Quick Tone Rewrite, show the draft and tone controls.
3. **Generate.** Offer Diplomatic, Neutral and Assertive. Start generation when the user selects the primary action. Announce processing and retain the inputs for retry or regeneration.
4. **Review and edit.** Keep the previous reply visible until regeneration succeeds. In Rewrite with Evidence, display source-backed claims, unverified claims and warnings separately.
5. **Finish in the web workspace.** Users review and edit the final text in the browser.

### Slack JSON and message selection

- The primary import is **folder selection** for an extracted Slack export. Read top-level `users.json` (also accept `user.json`) and `channels.json`; map channel-name subfolders and their `YYYY-MM-DD.json` files to known channel IDs automatically. Group multiple days under the same channel. Ignore ancillary root metadata such as `.slack-manifest.json`, `canvases.json`, `file_conversations.json`, `huddle_transcripts.json`, `integration_logs.json`, `lists.json`, and attachments. Folder metadata must identify the user and channel registries unambiguously; never guess an ID from a folder name. Unsupported or unmapped message folders produce a clear error before saving.
- The sample preview uses a synthetic extracted export with the same folder structure, not a combined JSON bundle. Parsing does not unzip archives or contact Slack. Preview valid messages and any skipped-record warnings, then explicitly confirm import. Enforce the API's batch/body limits on relevant JSON and converted messages; see [memory import](API_CONTRACT.md#4-memory-import). Show clear empty/export-only-system-event errors. Existing individual JSON conversion formats remain supported by the adapter for compatibility, while the UI uses a folder picker.
- The sample contains a week of varied conversations for at least ten manual test situations. Users select the original manager message and write their own draft; [TEST_SITUATION.md](../TEST_SITUATION.md) provides the scenario guide. All sample messages remain synthetic and the complete week fits one import.
- Preserve Slack user IDs in `sender`; participant and channel names are display metadata for the current page session only. Map each message's `user` ID to the matching `id` in `users.json` or `user.json`, using a non-blank profile display name, real name or username. Publish this lookup when the export is previewed, so existing saved messages can show their registered names without importing the messages again. Dropdowns show those names without appending IDs; selection values and API requests retain the original IDs. If no matching name is available, retain the original ID rather than inventing a participant name. Never infer who the manager is, including from names, Slack administrator status or message wording.
- Initialise the public synthetic sample's name lookup directly from its bundled `users.json` and `channels.json`, so previously imported sample records display names on a fresh page as well. A user-selected export's registry overrides those sample mappings. This requires no browser storage of user metadata.
- The reply form offers labelled selections for **You**, **Your manager**, **Conversation** and **Manager message**. The two participants must differ. Show only the selected manager's messages in the selected conversation, with known timestamps/source and original text. Explicitly using a selected message fills the optional context and restricts generation to that conversation.
- Keep role selections in workspace state across generation/regeneration, without storing imported texts or participant metadata in browser storage. Refresh saved history after import or deletion; clear stale message context when its record disappears or roles/conversation change. Editing context manually removes the imported-message selection and conversation restriction.
- Empty history, unavailable history, invalid role choices, no manager messages and unsupported JSON have readable states and a retry/import path. Manual context and draft-only generation remain available.

**Hosted sign-in.** In the hosted build (`NEXT_PUBLIC_R2R_AUTH=invite`), visitors without a session open `/login`. There they enter their invite code, then return to the workspace. A personal sign-in link (`/login#<invite code>`) signs in without typing. The code stays in the URL fragment, which is never sent to the server, and the page removes it from the address bar immediately. If the API reports an expired session, the browser returns to `/login`. Show readable errors for an invalid code and for too many attempts. The local demo and the browser mock never show sign-in. See [Hosted invite-code sessions](API_CONTRACT.md#hosted-invite-code-sessions).

Quick Tone Rewrite requires backend support for generation without memory retrieval. The existing evidence endpoint accepts an optional manager message and still searches imported history, including when only a draft is supplied. Confirm the no-retrieval API with the backend owner before connecting Quick Tone Rewrite.

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
