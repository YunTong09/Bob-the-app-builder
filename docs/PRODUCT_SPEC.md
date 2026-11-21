# Rage-to-Reply — Product Specification

This document defines product behaviour, feature priorities and MVP acceptance criteria. See [ARCHITECTURE.md](ARCHITECTURE.md) for components and data flow, [API_CONTRACT.md](API_CONTRACT.md) for endpoint behaviour and schemas, and [AGENTS.md](../AGENTS.md) for development rules and ownership.

## 1. Project Overview

**Project Name:** Rage-to-Reply  
**Type:** Browser-based AI workplace communication assistant  
**Development Context:** 18-hour hackathon  
**Team Size:** 3 developers

### Product Vision

Rage-to-Reply helps employees transform emotionally charged workplace messages into calm, professional and factually grounded responses.

The application allows employees to express what they genuinely feel in a private space before generating a professional response suitable for workplace communication.

Unlike conventional AI tone rewriters, Rage-to-Reply uses contextual memory to identify relevant information from past workplace conversations.

**Core differentiator: Replies with Receipts.**

The application does not simply rewrite messages. It helps users support their responses with evidence.

### Value Proposition

"Say what you feel. Send what you mean. Back it up with facts."

---

## 2. Target Users

### Primary Users

Employees who:
- Experience frustrating or difficult workplace communication.
- Struggle to formulate professional responses.
- Want to communicate assertively without escalating conflict.
- Need to reference previous conversations or instructions.
- Want to maintain a record of important workplace interactions.

### Secondary Users

- University students entering the workforce.
- Interns and graduate employees.
- Professionals navigating difficult conversations.
- Workers communicating with supervisors and managers.

---

## 3. Core Application Features

These six features define the current scope. P0 features form the required MVP; P1 features follow once the complete P0 workflow is stable.

| Priority | Feature | Key requirements |
| --- | --- | --- |
| P0 | Rage-to-Professional | Turn the user's emotional draft into a professional reply while preserving their intent. Support Diplomatic, Neutral and Assertive tones, with regeneration from the same input. Do not accept blame, invent facts or change meaning. |
| P0 | Manager Message Interpreter | Identify explicit requests, possible actions, missing information and potential misunderstandings. Label interpretations clearly; do not claim to know the manager's emotions or intentions. |
| P0 | Replies with Receipts — Main Differentiator | Search imported conversations for evidence supporting claims in the user's draft. Show evidence separately with source references where available. Never invent messages, dates or evidence. |
| P0 | Communication Memory | Let users import, review and delete conversation history. Store available message details and leave missing timestamps or sources blank. Do not save emotional drafts by default. |
| P1 | Enhanced Tone Adjustment | Add tone controls beside generated replies. Tone changes must preserve the underlying facts. |
| P1 | Communication Preferences | Let users save their preferred tone, response length, formality and directness. Keep preferences user-controlled. |

The Web App offers two reply modes:

- **Rewrite with Evidence.** Users provide an emotional draft and choose a tone. They may add the manager's message for context and explicitly import conversation history for source-backed evidence. Neither is required to generate a reply. Without a manager message, the app states that no manager request can be interpreted rather than inventing one.
- **Quick Tone Rewrite.** Users type a draft and choose a tone. The rewrite uses the current draft without retrieving imported history.

P0 regeneration reuses the same input form. The dedicated controls beside a generated reply are P1. The numbered workflow below describes Rewrite with Evidence. Quick Tone Rewrite uses draft input, generation, review and editing.

Communication Memory persists only explicitly imported history, including message content, sender, conversation identifier and available timestamps or source information. A basic message list is sufficient for review and deletion. Missing metadata remains blank in the interface and uses the null or omitted representations defined in [API_CONTRACT.md](API_CONTRACT.md).

For Slack imports, users select an extracted export folder containing top-level `users.json` (or `user.json`), `channels.json` and channel-name subfolders with dated message JSON files. The app resolves participant names and channel IDs from those registries automatically, combines message days by channel and ignores unrelated export metadata and attachments. The synthetic test export follows this same directory structure. Preview converted messages before confirming import. Sender IDs remain the authoritative message authors; display names never imply a workplace role. In the reply workspace, users explicitly select themselves and their manager as distinct participants, choose a conversation and select the manager's saved message to use as current reply context. The app fills that original text without requiring a paste and restricts evidence retrieval to its conversation. Roles and display-name metadata last for the current page session only and are not a manager profile. Changing roles, conversation or deleting history clears the selected message. Manual context and generation from a draft alone remain available.

The synthetic export provides a complete seven-day workplace conversation sample, with at least ten distinct situations for users to answer in their own words. Include relevant prior messages, natural unrelated conversation, supported claims, a contradicted claim and a claim with missing proof. Keep the complete sample within one import batch. [TEST_SITUATION.md](../TEST_SITUATION.md) guides manual exploration using original manager messages and open writing prompts; it does not supply emotional drafts or finished replies.

The restricted single-user demo may also preview one explicitly configured Slack channel, then let the user select messages for import. Previewing does not save history or call Claude. This limited import extension uses the existing memory workflow; it does not add background synchronisation, message sending, thread/file crawling or access to arbitrary private conversations. Its request, response and failure behaviour are defined in [API_CONTRACT.md](API_CONTRACT.md#slack-channel-preview-single-user-demo-extension).

Replies with Receipts extracts factual claims, retrieves relevant history and validates whether source messages support those claims before using them as evidence. Missing or contradictory evidence must be distinguished from supported claims. Communication Preferences must not infer permanent facts about other people.

---

## 4. Main User Workflow

1. User opens the Web App in their browser.
2. User may import Slack JSON, identify themselves and their manager, and select the manager's message from a saved conversation; alternatively add context manually or leave it blank.
3. User enters their unfiltered response.
4. User selects a desired tone.
5. User clicks "Generate Reply".
6. AI analyses the messages.
7. The memory system retrieves relevant conversation history.
8. AI evaluates factual support.
9. AI generates a professional response.
10. The application displays the reply, evidence and uncertainty warnings.
11. User edits the response or selects a tone and generates again from the input form.
12. User reviews the final edited response in the web workspace.

**The application must never automatically send messages.**

---

## 5. MVP Scope

The hackathon MVP must demonstrate:

- Working message input.
- Professional response generation with Claude that preserves intent without accepting blame or inventing facts.
- Diplomatic, Neutral and Assertive tones, with regeneration from the same input form.
- Optional manager message interpretation covering explicit requests, possible actions, missing information and misunderstandings, with interpretations labelled. Generation from the employee draft alone remains available, with missing manager context clearly identified.
- Importing sample conversation history.
- Reviewing and deleting imported history through a basic message list.
- Contextual memory retrieval.
- Evidence-supported reply generation.
- Display of supporting evidence separately from the reply, with source references where available.
- Missing timestamps and sources left blank, and no default saving of emotional drafts.
- Editable reply preview in the browser.
- Basic error handling.

### P1 Scope

- Dedicated tone adjustment controls alongside a generated reply.
- User-controlled personal communication preferences.

Both P1 features must preserve the underlying facts. Do not implement P1 work until the complete P0 workflow is functioning. Features outside the six-feature list have no current implementation priority.

---

## 6. Non-Goals

The hackathon version will not implement:

- Automatic message sending.
- Desktop installers, system permissions, browser extensions and integrations with external messaging tools.
- Full Slack or Gmail integration; the limited, user-confirmed Slack channel import described above is permitted.
- Employee performance monitoring.
- Psychological diagnosis or emotion profiling.
- Persistent manager profiling.
- Employment law advice.
- Enterprise HR administration.
- Complex multi-agent architectures.

---

## 7. Success Criteria

The MVP is successful when a user can:

1. Enter an emotional draft and a preferred tone, optionally adding the manager's message.
2. See the manager's explicit requests, possible actions, missing information and potential misunderstandings, with interpretations clearly labelled and no claims about hidden emotions or intentions.
3. Preview, import, review and delete historical conversations while missing timestamps and sources remain blank and emotional drafts are not saved by default. Import Slack JSON using stable sender IDs, explicitly select participant roles and choose a saved manager message without pasting it.
4. Generate a professional reply that preserves their intent without accepting blame, inventing facts or changing meaning.
5. See real supporting evidence separately from the reply, with source references where available and no fabricated messages, dates or evidence.
6. Distinguish verified evidence from unverified or contradicted claims.
7. Select another tone and generate again from the same input form without changing the facts.
8. Review and edit the reply in the browser.

The hosted workflow should open from a browser URL and work without requiring users to install a runtime or start the backend. A shared release requires authenticated sessions and verified data isolation. An isolated local demo is tracked separately from hosted acceptance.

When P1 is implemented, users must also be able to adjust tone beside a generated reply without changing facts, and explicitly save or change their own tone, response length, formality and directness preferences.

---

## 8. Product Principles

- Preserve the employee's voice and intention.
- Prioritise factual accuracy over polished wording.
- Do not invent evidence.
- Do not accept blame on the employee's behalf.
- Respect user privacy.
- Keep the user in control.
- Prefer practical functionality over unnecessary complexity.

**The application's purpose is to help people communicate clearly, not to silence legitimate workplace concerns.**
