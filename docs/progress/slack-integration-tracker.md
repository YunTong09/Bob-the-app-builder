# Rage-to-Reply Slack App Integration Plan

Last updated: 2026-11-21

## Delivery goal

Build on the deployed [Rage-to-Reply Web App](https://ragetoreply.tech) with two entry points that share FastAPI's generation, Memory, evidence verification and usage controls.

| Entry point | User flow |
| --- | --- |
| Slack App | Open App Home in Slack to start a rewrite or go to the website. Alternatively, open a Modal from the **Rewrite with Rage-to-Reply** shortcut on a message, confirm the selected message, enter a draft, pick a tone and preview the AI reply inside Slack. The user decides how to use the reply. |
| Website | After signing in, go to **Memory → Import from Slack**, paste an authorized **Slack Channel ID**, preview the messages, select them and confirm the import. The website can then generate replies that cite this data. |

In this plan, Slack ID means the channel ID. A user ID or workspace ID cannot directly identify which conversation to read. The channel ID only locates the resource; reading it still requires workspace authorization, server-side Slack credentials and the user's own access to the channel. P0 is limited to a single invited Slack workspace and one controlled public test channel containing synthetic messages. Real chat content, private channels and DMs are added only after their authorization is separately accepted. [Slack conversations.history](https://docs.slack.dev/reference/methods/conversations.history/)

Inside Slack, the app uses App Home and Block Kit Modals. The website's existing animations, voice input and full Memory management are reached through an App Home link to the HTTPS website. P0 is installed in a team-managed workspace and does not need a Slack Marketplace listing first. [Slack App Home](https://docs.slack.dev/surfaces/app-home/) · [Slack shortcuts](https://docs.slack.dev/interactivity/implementing-shortcuts/)

## Current state

- Website deployment and invite sign-in have team verification records. The cross-account acceptance scope for Web accounts and Memory data is in the [Web App tracker](web-app-integration.md).
- The website already has the Slack Channel ID input, preview, selection and confirm-import UI. FastAPI already has `POST /api/slack/preview` and the Memory import API. Preview currently supports only the one channel configured on the server. This code is reusable, but the deployed environment still needs to verify the Slack token, scopes and authorization of invited accounts. [API Contract](../API_CONTRACT.md#slack-channel-preview-single-user-demo-extension)
- `slack/` contains an early Bolt, Socket Mode, Modal and Mock prototype. Confirmed Modal fields and components can be reused. In the new P0, generation is wired back to the deployed FastAPI so it shares the Claude and evidence flow.

## P0 tasks

| Task ID | Task | Status | Dependencies |
| --- | --- | --- | --- |
| SLACK-01 | Install the Slack App, verify callbacks and link accounts | TODO | Deployed Web App, test workspace admin |
| SLACK-02 | Generate and review replies inside Slack | TODO | SLACK-01 |
| SLACK-03 | Enter a channel ID on the website, preview and import selected messages | IN PROGRESS | SLACK-01 provides installation and test authorization; the existing UI can be verified first |
| SLACK-04 | Deployment integration and acceptance of both entry points | TODO | SLACK-02, SLACK-03 |

### SLACK-01 — Workspace installation and trust boundary

- [ ] Install the Slack App in the test workspace, enable the Home tab, message shortcut and Interactivity, and create an App manifest that deployments can reproduce.
- [ ] Receive Slack callbacks through the existing HTTPS deployment. If Bolt is reused, use the HTTP receiver to keep a single callback ingress. Callbacks verify the Slack signature, timestamp and workspace against the raw request body, and are handled separately from the website sign-in page. Slack credentials live in the server's secret management.
- [ ] On the server, create an approved mapping between each invited Web account and a `team_id + user_id`. Accept first with admin-approved mappings in a single workspace; unlinked Slack users are directed to the website or to contact an admin before generating. Both the Slack requester identity and the Web owner are resolved by the server, and they share the generation quota.
- [ ] Update authorization correctly when the App is installed or removed. Accept the shortcut and required channel reads with the minimum scopes; P0 does not need permission to send messages. [Slack request signature verification](https://docs.slack.dev/authentication/verifying-requests-from-slack/) · [Slack App Home](https://docs.slack.dev/surfaces/app-home/)

**Acceptance** Both invited users can open App Home. Invalid signatures, unauthorized workspaces and unlinked accounts are rejected before Claude is called. Slack callbacks are not redirected to the website's invite-code sign-in page.

### SLACK-02 — Rewrite directly inside Slack

- [ ] App Home offers starting a rewrite and opening the website. From the Home entry the user types the work message; from the message shortcut the selected Slack message is used as the work message.
- [ ] The Modal supports a draft, three tones and an explicit Generate. Acknowledge Slack interactions immediately, run the slower Claude work afterwards, and use `views.update` to show waiting, result or retry states. If the deployment needs to hand results across processes, use trackable job state and deduplicate repeated submissions. [Slack acknowledgement deadline](https://docs.slack.dev/tools/bolt-js/concepts/acknowledge/) · [Slack views.update](https://docs.slack.dev/reference/methods/views.update/)
- [ ] Reuse FastAPI's generation and evidence flow. The Modal shows a reviewable suggested reply, key points and any required warnings. The App does not send Slack messages and does not write into the original Composer.

**Acceptance** In a real Slack workspace, open the Modal and use a synthetic case to generate, regenerate with a different tone and retry after a verification failure. The reply is visible only to the requester. Duplicate callbacks do not cause duplicate billing or generation.

### SLACK-03 — Website import by channel ID

- [x] The existing website provides the channel ID input, preview, selection and confirm-import UI.
- [x] The existing FastAPI provides single-channel allowlist preview and the Memory import API.
- [x] Added the least-privilege App manifest [deploy/slack/manifest.yaml](../../deploy/slack/manifest.yaml) (only `channels:history`, no message sending, no Socket Mode), and added steps to the [README](../../README.md#preview-and-import-a-slack-test-channel) for creating the App from the manifest, finding the channel ID and bot token, and verifying locally through the website's **History → Import from Slack**.
- [ ] Verify preview, selection and import locally (`demo_local`) with a real test workspace. Requires a test workspace admin to create and install the App and provide the bot token and channel ID.
- [ ] At deployment, configure the bot token from the Slack installation and the test channel allowlist. Public channel history uses `channels:history`, and the bot must be in the channel. Add only the minimum scope needed to verify users, as the design requires.
- [ ] Bind the signed-in website user to an approved Slack account. Before reading, the server confirms the channel belongs to that workspace and that the user can read it. The bot being able to read a channel does not mean the website user can. Reject when authorization cannot be confirmed, and stop further previews after a user is removed or authorization is revoked.
- [ ] Verify paginated preview, read failures, Slack rate limiting, empty results, retry and selection. Store selected messages only after confirmation, keep owner isolation, and preserve the original timestamp and source fields. [Slack channel history permissions](https://docs.slack.dev/reference/methods/conversations.history/)

**Acceptance** Two people test with their own invited accounts. The authorized user can preview and import selected messages; the other cannot read the unauthorized channel and cannot see the first user's imported data in their own Memory or generation evidence.

**Blocker (deployment)** The hosted site cannot enable preview through configuration alone. In invite mode, `POST /api/slack/preview` only checks that the user is signed in, so once `SLACK_BOT_TOKEN` is set, every invited account can read the allowlisted channel, which fails the acceptance above. The [deployment guide](../../deploy/gce/README.md#operations) therefore keeps the token unset. Account binding and the pre-read authorization check must be completed, and the [API Contract](../API_CONTRACT.md#slack-channel-preview-single-user-demo-extension) (currently defined as a single-user demo) updated, before the token can be set on the hosted site.

### SLACK-04 — Deployment and delivery

- [ ] From the same deployed version, test generation inside Slack and generation after a website import by Channel ID. Record the commit, workspace, test account types and results.
- [ ] Verify account and data isolation, revocation, 429s, upstream errors, duplicate submissions and logging. Logs keep only the events and outcomes needed for diagnosis, with no tokens, raw drafts or chat content.
- [ ] Update the deployment operations guide and any required API Contract changes, then have a teammate verify both entry points from another computer.

**Acceptance** Using the same deployed version, an invited teammate completes a rewrite in Slack and can also preview and import a synthetic conversation by channel ID on the website. Failure handling, the final round of authorization tests and data isolation tests are all recorded.

## Later releases

Multi-workspace installation will add the OAuth install flow, per-workspace token and authorization isolation, uninstall and revocation, and Slack Marketplace publishing. Private channels, DMs, sync or other read scopes will be reviewed separately based on actual need. [Slack OAuth installation](https://docs.slack.dev/authentication/installing-with-oauth/)

## Verification and updates

This plan was revised based on the current code, the Web API Contract, existing deployment records and the official Slack documentation. No real installation of the new Slack App, Claude generation or deployment test has been run yet. After each item is completed, record the commit, test environment, scopes and verification result before changing it to DONE.

| Date | Change |
| --- | --- |
| 2026-11-21 | Replaced the old Socket Mode / Mock Prototype tasks with a two-entry-point delivery plan built on the deployed Web App. |
| 2026-11-21 | SLACK-03: added the Slack App manifest and local real-Slack verification steps; recorded that the hosted site must complete the account authorization check first. Docs and config only; the manifest has not been imported into Slack yet, and no real Slack verification has been done. |
