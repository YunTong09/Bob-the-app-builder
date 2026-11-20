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
