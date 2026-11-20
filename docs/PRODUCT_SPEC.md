# Rage-to-Reply — Product Specification

## 1. Project Overview

**Project Name:** Rage-to-Reply  
**Type:** AI-powered workplace communication assistant  
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

### Feature 1: Rage-to-Professional

**Priority: P0**

Users provide:
- The manager's original message.
- Their unfiltered emotional response.
- Their preferred communication tone.

The AI generates a professional response while preserving the user's actual concerns and intended message.

Supported tones:
- Diplomatic
- Neutral
- Assertive

The output must not automatically accept blame, invent information or change the user's intended meaning.

### Feature 2: Manager Message Interpreter

**Priority: P0**

The AI analyses the manager's original message and identifies:
- Explicit requests.
- Possible intended actions.
- Missing information.
- Potential misunderstandings.

The application must distinguish interpretations from confirmed facts.

It must not claim to know the manager's emotions or intentions.

### Feature 3: Replies with Receipts

**Priority: P0 — Main Differentiator**

Users can import previous workplace conversations.

The application:
1. Extracts relevant factual claims from the employee's message.
2. Searches imported conversation history.
3. Retrieves related messages.
4. Evaluates which claims have supporting evidence.
5. Generates a reply using the verified context.

Supporting evidence should be displayed separately from the generated reply.

Evidence must include source references where available.

The AI must never invent historical messages, dates or supporting evidence.

### Feature 4: Communication Memory

**Priority: P0**

The application supports persistent memory of explicitly imported workplace conversations.

Memory can store:
- Message content.
- Sender.
- Timestamp.
- Conversation identifier.
- Source identifier.

Users should be able to review and delete imported history.

Emotional drafts should not be stored permanently by default.

### Feature 5: Tone Adjustment

**Priority: P1**

Allow the user to regenerate a response using different communication styles.

Changing the tone must not change the underlying facts.

### Feature 6: Rage Meter

**Priority: P1 — Demo Feature**

Display a visual indicator comparing the emotional language of the original draft with the rewritten message.

The meter is a playful representation of writing tone, not a clinical measure of anger or mental wellbeing.

### Feature 7: Communication Preferences

**Priority: P1**

Allow users to save preferences such as:
- Preferred tone.
- Response length.
- Formality.
- Directness.

Preferences must be user-controlled rather than inferred as permanent facts about other people.

---

## 4. Main User Workflow

1. User opens the application.
2. User enters the manager's original message.
3. User enters their unfiltered response.
4. User selects a desired tone.
5. User clicks "Generate Reply".
6. AI analyses the messages.
7. The memory system retrieves relevant conversation history.
8. AI evaluates factual support.
9. AI generates a professional response.
10. The application displays the reply, evidence and uncertainty warnings.
11. User edits or regenerates the response.
12. User manually copies the final response.

**The application must never automatically send messages.**

---

## 5. MVP Scope

The hackathon MVP must demonstrate:

- Working message input.
- Professional response generation with Claude.
- Three selectable tones.
- Importing sample conversation history.
- Contextual memory retrieval.
- Evidence-supported reply generation.
- Display of retrieved evidence.
- Copy-to-clipboard functionality.
- Basic error handling.

### Stretch Goals

- Rage meter animation.
- Voice-to-text input.
- Manager communication preferences.
- Conversation timeline visualisation.
- Browser extension integration.
- Semantic memory retrieval.

Do not implement stretch goals until the complete MVP workflow is functioning.

---

## 6. Non-Goals

The hackathon version will not implement:

- Automatic message sending.
- Full Slack or Gmail integration.
- Employee performance monitoring.
- Psychological diagnosis or emotion profiling.
- Employment law advice.
- Enterprise HR administration.
- Complex multi-agent architectures.

---

## 7. Success Criteria

The MVP is successful when a user can:

1. Input an emotionally charged workplace response.
2. Import or select relevant historical conversations.
3. Generate a professional reply.
4. See real supporting evidence where available.
5. Distinguish verified evidence from unverified claims.
6. Adjust the tone without changing the facts.
7. Copy the response for personal review and use.

The complete workflow should function without requiring manual intervention by a developer.

---

## 8. Product Principles

- Preserve the employee's voice and intention.
- Prioritise factual accuracy over polished wording.
- Do not invent evidence.
- Do not automatically blame the employee.
- Respect user privacy.
- Keep the user in control.
- Prefer practical functionality over unnecessary complexity.

**The application's purpose is to help people communicate clearly, not to silence legitimate workplace concerns.**