# TEST SITUATION - A week of Slack conversations

Synthetic week: **16-22 November 2026**, **Australia/Brisbane (AEST, UTC+10)**. The export contains **91 human messages**, five human participants, an automated reminder bot and **13 practice situations** across three channels. It includes ordinary chatter and thread replies, not just a list of requests.

## Start here

1. Open the app, then **History > Preview sample Slack export**. Alternatively, choose the extracted [sample folder](src/data/slack-export). Review and confirm the import.
2. Select **Sam Patel** (`U08EMP001AA`) as **You** and **Alex Chen** (`U08MGR001BB`) as **Your manager**. See the [README cast table](README.md#sample-user-roles) for the other participants.
3. For a situation below, select its conversation and find the quoted manager message. Choose **Use selected message**. Its complete ID is included for checking the saved history.
4. Type your own unfiltered draft: what you want to communicate, what you need and any facts you believe matter. The questions below are prompts, not text to copy into the draft.
5. Choose Diplomatic, Neutral or Assertive, generate, then review the editable reply, evidence, unverified claims and warnings. Try another tone without changing your facts.

The app is configured separately for mock or Claude replies. Mock modes exercise importing, selection and UI states with synthetic responses; they do not demonstrate tailored writing for these situations. For varied AI replies, use the [Claude setup in README](README.md#fastapi-backend-p0-api-in-progress). The raw draft is not saved to conversation memory.

All people, projects, amounts and messages are fictional. The context notes describe what is in this particular export; missing evidence is not proof an event never happened. A genuine source message does not automatically prove every claim made about it.

## Situation index

| # | Situation | Channel | Evidence exercise |
| --- | --- | --- | --- |
| 1 | A document link is not document access | #new-channel | supported |
| 2 | The deadline moved a day earlier | #new-channel | supported |
| 3 | Two urgent tasks and one person | #new-channel | supported |
| 4 | A workshop conflicts with approved time away | #all-new-workspace | supported |
| 5 | A last-minute Saturday request | #all-new-workspace | supported |
| 6 | Clarifying who built the dashboard | #new-channel | supported |
| 7 | A receipt is attached but finance is still waiting | #all-new-workspace | supported |
| 8 | More professional, but in what way? | #new-channel | unverified |
| 9 | A handover is blocked by an external feed | #new-channel | supported |
| 10 | 142 and 156 can both describe the same extract | #new-channel | supported |
| 11 | CSV was agreed; PDF is now requested too | #new-channel | supported |
| 12 | A missed meeting with an earlier acknowledgement | #all-new-workspace | contradicted |
| 13 | A remembered conversation is not written approval | #all-new-workspace | unverified |

## 1. A document link is not document access

**Select:** #new-channel (Thu, 19 Nov, 10:15 AEST). Conversation: `slack-export:C08PROJECT1`.

**Alex's message:**

> Can you confirm what is blocking your review of the shared documents and what you need from me to move forward? Please give me a clear update before we agree on the review timeline.

**Message ID:** `slack-export:C08PROJECT1:1795047300.000001`.

**Relevant earlier history:**

- **Alex Chen, Wed, 18 Nov, 10:30 AEST:** I've uploaded the project documents to the shared drive: <https://example.invalid/shared/project-docs|Project documents>. Please review the material before we agree on the next steps.
- **Sam Patel, Wed, 18 Nov, 10:35 AEST:** I can see the shared drive link, but the document asks for a password. I don't have the password, so I cannot start the review yet. Could you send it?
- **Priya Shah, Wed, 18 Nov, 10:40 AEST:** The project document also prompts me for a password when I open that link.
- **Alex Chen, Wed, 18 Nov, 10:45 AEST:** Thanks for flagging the access issue. The shared drive location is correct. Let's confirm document access before setting a review deadline.
- **Sam Patel, Thu, 19 Nov, 10:10 AEST:** I still do not have the document password. Once I can open the material, we can agree on a realistic review time.

**Write your own draft:** How would you explain the access blocker and ask for what you need, without accepting blame or promising an unagreed review deadline?

**Check the result:** The shared location and reported password prompt are documented. Priya independently reports the prompt; no message supplies a password. Missing proof of delivery is not proof that a password was never sent elsewhere.

## 2. The deadline moved a day earlier

**Select:** #new-channel (Wed, 18 Nov, 13:05 AEST). Conversation: `slack-export:C08PROJECT1`.

**Alex's message:**

> Sam, the client has brought the Beacon reconciliation discussion forward. Can you send the completed exception summary by 16:00 today instead of Thursday at 15:00? Tell me what that changes for your other work.

**Message ID:** `slack-export:C08PROJECT1:1794971100.000143`.

**Relevant earlier history:**

- **Alex Chen, Mon, 16 Nov, 09:35 AEST:** For the Beacon reconciliation summary, Thursday 19 November at 15:00 is the deadline. I need the exception list and a short explanation of the largest differences, not a slide deck.
- **Sam Patel, Mon, 16 Nov, 09:39 AEST:** Got it: exception list and notes for Thursday at 15:00. I will use the final ledger extract.
- **Jordan Lee, Mon, 16 Nov, 09:43 AEST:** The final ledger extract will be in the shared folder on Tuesday morning. Monday's extract still has three unposted adjustments.
- **Jordan Lee, Tue, 17 Nov, 09:05 AEST:** Final ledger extract is now available: <https://example.invalid/ledger/final-1711|final ledger>. The three adjustments are posted. The earlier Monday file is still there with DRAFT in its name.

**Write your own draft:** How would you respond to the earlier deadline and explain any trade-off or clarification you need?

**Check the result:** Alex originally set Thursday 19 November at 15:00 and now asks for Wednesday at 16:00. History supports the change, not a promise that Sam can meet it.

## 3. Two urgent tasks and one person

**Select:** #new-channel (Thu, 19 Nov, 11:05 AEST). Conversation: `slack-export:C08PROJECT1`.

**Alex's message:**

> Sam, I cannot see the Q4 slides ready for review yet. Can you explain where they stand and which task you need me to prioritise?

**Message ID:** `slack-export:C08PROJECT1:1795050300.000152`.

**Relevant earlier history:**

- **Alex Chen, Mon, 16 Nov, 10:30 AEST:** Sam, keep the support queue first this week until there are fewer than 10 open tickets. The Q4 client slides can wait while the queue is above that number.
- **Sam Patel, Mon, 16 Nov, 10:34 AEST:** There are 27 open tickets right now. I will stay on support and flag when it is below 10.
- **Jordan Lee, Wed, 18 Nov, 11:20 AEST:** Support queue is at 22 open tickets. Six came back from the overnight sync; the count is not below 10 yet.
- **Alex Chen, Thu, 19 Nov, 09:00 AEST:** Sam, can you also get the Q4 client slides into review by 11:00 today? The account team wants something to talk through this morning.
- **Sam Patel, Thu, 19 Nov, 09:08 AEST:** I am still handling the support queue and the latest count is 22. Is the slides review replacing that priority or being added to it?

**Write your own draft:** How would you ask for a clear priority while giving a factual update on the support queue and slide request?

**Check the result:** The original instruction puts support first until fewer than 10 tickets remain; the recorded count is still 22 when slides are requested. No later message resolves the priority conflict.

## 4. A workshop conflicts with approved time away

**Select:** #all-new-workspace (Wed, 18 Nov, 13:10 AEST). Conversation: `slack-export:C08WORKSP1`.

**Alex's message:**

> Sam, I have just added you to a 14:30 client workshop today. Can you join and take the action notes? Please let me know promptly if there is a clash.

**Message ID:** `slack-export:C08WORKSP1:1794971400.000144`.

**Relevant earlier history:**

- **Alex Chen, Mon, 16 Nov, 09:05 AEST:** Sam, your Wednesday 18 November appointment is approved: you can be away from 14:00 until the end of the day. Please leave a short handover before you go.
- **Sam Patel, Mon, 16 Nov, 09:08 AEST:** Thank you. I have blocked Wednesday afternoon and will leave the handover before 14:00.
- **Jordan Lee, Wed, 18 Nov, 12:05 AEST:** Sam's Wednesday afternoon handover is in the rota. I am covering incoming requests after 14:00; please put anything urgent in the shared queue.

**Write your own draft:** How would you flag the workshop clash and help arrange coverage without implying that you are available during approved time away?

**Check the result:** Alex explicitly approved Wednesday after 14:00 and Jordan confirms cover. The new workshop is at 14:30 on that same day.

## 5. A last-minute Saturday request

**Select:** #all-new-workspace (Fri, 20 Nov, 16:20 AEST). Conversation: `slack-export:C08WORKSP1`.

**Alex's message:**

> Sam, can you cover the client's launch check at 09:00 tomorrow? Please let me know your availability and what we would need to arrange before I commit us.

**Message ID:** `slack-export:C08WORKSP1:1795155600.000167`.

**Relevant earlier history:**

- **Alex Chen, Mon, 16 Nov, 08:50 AEST:** The published rota is Monday to Friday, 09:00-17:00. There is no weekend cover booked for this team; please flag any client request that would need extra cover.
- **Sam Patel, Mon, 16 Nov, 08:53 AEST:** Thanks, that matches my calendar. I have not put myself down for any weekend cover.
- **Morgan Blake, Fri, 20 Nov, 16:00 AEST:** The client has asked for a launch check at 09:00 Saturday. I have not confirmed a person or weekend cover; our rota still shows Monday-Friday.

**Write your own draft:** How would you answer based on your own availability and ask what arrangements are needed before anyone commits you?

**Check the result:** The published rota is Monday-Friday and no weekend cover has been booked. The history does not establish whether Sam is personally available on Saturday or whether extra work is compensated.

## 6. Clarifying who built the dashboard

**Select:** #new-channel (Thu, 19 Nov, 15:00 AEST). Conversation: `slack-export:C08PROJECT1`.

**Alex's message:**

> I have described the Beacon dashboard as Priya's build in the client notes. Sam, can you hand the calculations over to her and confirm who should get questions about the work?

**Message ID:** `slack-export:C08PROJECT1:1795064400.000156`.

**Relevant earlier history:**

- **Sam Patel, Tue, 17 Nov, 10:10 AEST:** Beacon dashboard v3 is pushed. I implemented the net-order calculation and the exception drill-down; the change log lists the formulas and the tests I ran.
- **Priya Shah, Tue, 17 Nov, 10:18 AEST:** Reviewed Sam's v3 calculations and test output. I changed two axis labels and the chart colours; I did not build the calculation or drill-down.
- **Jordan Lee, Tue, 17 Nov, 10:22 AEST:** The version history and change log are linked in the dashboard README, so we can tell which changes belong to which person.

**Write your own draft:** How would you correct the ownership description respectfully while recognising Priya's review contribution?

**Check the result:** Sam describes implementing the calculation and drill-down; Priya independently confirms that she reviewed those and changed labels/colours. Do not turn a credit correction into a claim about anyone's motives.

## 7. A receipt is attached but finance is still waiting

**Select:** #all-new-workspace (Thu, 19 Nov, 10:00 AEST). Conversation: `slack-export:C08WORKSP1`.

**Alex's message:**

> Sam, finance says R-1042 is waiting for a receipt. Did you submit it? Please send me the receipt location and what still needs to happen.

**Message ID:** `slack-export:C08WORKSP1:1795046400.000151`.

**Relevant earlier history:**

- **Jordan Lee, Mon, 16 Nov, 09:00 AEST:** Expenses note: add the receipt link and cost code in the expenses tracker by Thursday noon. A tracker entry without a receipt stays pending; no need to send the same file by email as well.
- **Sam Patel, Tue, 17 Nov, 14:02 AEST:** Expense R-1042 is in the tracker under cost code OPS-12. The $84.50 courier receipt is attached here: <https://example.invalid/expenses/R-1042/receipt|R-1042 receipt>.
- **Jordan Lee, Tue, 17 Nov, 14:10 AEST:** I can open the R-1042 receipt link and the amount matches $84.50. The tracker shows the receipt attached; finance has not approved reimbursement yet.

**Write your own draft:** How would you point Alex to the receipt and distinguish submitting it from approval or reimbursement?

**Check the result:** The tracker entry and receipt location are recorded and Jordan confirms the link and amount. Finance approval and payment have not been confirmed.

## 8. More professional, but in what way?

**Select:** #new-channel (Thu, 19 Nov, 13:00 AEST). Conversation: `slack-export:C08PROJECT1`.

**Alex's message:**

> Sam, the project update needs to sound more professional and have a bit more polish before I share it. Can you revise it this afternoon and tell me what you will change?

**Message ID:** `slack-export:C08PROJECT1:1795057200.000154`.

**Relevant earlier history:**

- **Alex Chen, Tue, 17 Nov, 15:00 AEST:** For the project status updates, use three short parts: progress, blocker and next step. Keep the detail in the linked task rather than pasting the whole activity log.
- **Sam Patel, Tue, 17 Nov, 15:07 AEST:** Today's Atlas update is in the task: progress = validator ready; blocker = corrected vendor feed; next step = run checks when Morgan receives the file.
- **Priya Shah, Tue, 17 Nov, 15:11 AEST:** That is the same three-part format I used for the engineering update this morning.

**Write your own draft:** How would you ask for a concrete example or criterion while keeping the revision moving?

**Check the result:** The three-part format is documented, but the later feedback does not identify what wording is unsuitable or what polish means. History cannot establish Alex's hidden expectations or feelings.

## 9. A handover is blocked by an external feed

**Select:** #new-channel (Thu, 19 Nov, 14:00 AEST). Conversation: `slack-export:C08PROJECT1`.

**Alex's message:**

> Sam, why is the Atlas handover not ready? Please give me a clear update on what is missing, who has the next action and when you can reassess it.

**Message ID:** `slack-export:C08PROJECT1:1795060800.000155`.

**Relevant earlier history:**

- **Morgan Blake, Mon, 16 Nov, 11:15 AEST:** Atlas handover: the vendor has committed to the corrected customer feed by Thursday at 12:00. Sam's validation comes after that delivery; I am the vendor contact.
- **Sam Patel, Mon, 16 Nov, 11:19 AEST:** Thanks Morgan. The validator is ready for a test feed. Please tag me when the corrected file lands.
- **Sam Patel, Tue, 17 Nov, 11:30 AEST:** Atlas validation checklist is ready. I cannot run the final customer checks without the corrected vendor feed.
- **Morgan Blake, Thu, 19 Nov, 12:08 AEST:** Atlas vendor update: the corrected feed missed the 12:00 delivery. They now expect 16:00. No corrected file has reached me yet; I will post it here when it does.

**Write your own draft:** How would you explain the dependency, identify the next action and avoid promising a delivery time you do not control?

**Check the result:** Morgan owns the vendor contact, the corrected feed missed noon and Sam cannot run final checks without it. The vendor's revised 16:00 estimate is not proof of delivery.

## 10. 142 and 156 can both describe the same extract

**Select:** #new-channel (Fri, 20 Nov, 09:05 AEST). Conversation: `slack-export:C08PROJECT1`.

**Alex's message:**

> Sam, the spreadsheet says 156 orders and your Beacon headline says 142. Why do the numbers disagree? Please check the definition and tell me which figure belongs in the board report.

**Message ID:** `slack-export:C08PROJECT1:1795129500.000161`.

**Relevant earlier history:**

- **Priya Shah, Mon, 16 Nov, 13:20 AEST:** Beacon dashboard note: the headline metric is net completed orders, excluding cancelled and refunded orders. The raw export also has a gross-order column, so check which one is being compared.
- **Sam Patel, Mon, 16 Nov, 13:24 AEST:** I have labelled the headline Net completed orders and left gross orders in the detail tab.
- **Sam Patel, Wed, 18 Nov, 11:45 AEST:** Beacon comparison for this extract: 156 gross orders, 8 cancellations and 6 refunds, giving 142 net completed orders. The dashboard headline is 142.
- **Jordan Lee, Wed, 18 Nov, 11:52 AEST:** Finance needs the 142 net number on the board report. The 156 gross total belongs in the supporting table, with the exclusions shown.

**Write your own draft:** How would you explain the difference between gross and net orders and clarify which number belongs in the report?

**Check the result:** The extract has 156 gross orders minus 8 cancellations and 6 refunds, giving 142 net. Jordan explicitly requests the net number for the board report; no arithmetic error is established.

## 11. CSV was agreed; PDF is now requested too

**Select:** #new-channel (Fri, 20 Nov, 09:25 AEST). Conversation: `slack-export:C08PROJECT1`.

**Alex's message:**

> Sam, can you include PDF export by 17:00 today as well as the CSV release? We have the same delivery slot and budget. Please tell me the impact before I confirm anything to the client.

**Message ID:** `slack-export:C08PROJECT1:1795130700.000162`.

**Relevant earlier history:**

- **Alex Chen, Mon, 16 Nov, 10:05 AEST:** The reporting release this week is CSV export only. PDF layout and scheduled email are outside this release; please estimate them separately if the client asks.
- **Sam Patel, Mon, 16 Nov, 10:09 AEST:** CSV only for this release. I have kept PDF and scheduled email out of the acceptance checklist.
- **Sam Patel, Tue, 17 Nov, 16:05 AEST:** CSV export passed 18 acceptance checks on the staging sample. The release checklist and output files are in the task.
- **Morgan Blake, Wed, 18 Nov, 13:15 AEST:** The client asked whether PDF export can be included in Friday's release too. I have not promised it; the agreed checklist I have is still CSV only.

**Write your own draft:** How would you explain the scope change and ask for a decision on time, scope or resources before committing?

**Check the result:** The recorded release scope is CSV only; Morgan says PDF has not been promised. Passing CSV tests does not establish that PDF can be added in the same slot or budget.

## 12. A missed meeting with an earlier acknowledgement

**Select:** #all-new-workspace (Fri, 20 Nov, 11:18 AEST). Conversation: `slack-export:C08WORKSP1`.

**Alex's message:**

> Sam, we could not find you at the 11:00 release review. Can you tell me what happened and how you will catch up on the decisions and your CSV test update?

**Message ID:** `slack-export:C08WORKSP1:1795137480.000164`.

**Relevant earlier history:**

- **Alex Chen, Mon, 16 Nov, 09:12 AEST:** Release review is Friday 20 November at 11:00 in Cedar, with a video link for remote attendees. Sam, please bring the CSV export test results.
- **Sam Patel, Mon, 16 Nov, 09:14 AEST:** Friday at 11:00 is in my calendar. I will bring the CSV test results.

**Write your own draft:** How would you respond after missing the review? Try checking a claim that nobody told you about it against the saved conversation.

**Check the result:** The assertion that Sam was never told about the Friday 11:00 review is contradicted by Alex's invitation and Sam's explicit acknowledgement. The history does not say why Sam missed it, so no excuse or admission should be invented.

## 13. A remembered conversation is not written approval

**Select:** #all-new-workspace (Fri, 20 Nov, 10:15 AEST). Conversation: `slack-export:C08WORKSP1`.

**Alex's message:**

> Sam, I heard you were considering the $450 reporting course. Have I actually approved that spend? Please check with me before booking; I cannot find an approval in writing.

**Message ID:** `slack-export:C08WORKSP1:1795133700.000163`.

**Relevant earlier history:**

- **Sam Patel, Tue, 17 Nov, 13:05 AEST:** I remember discussing the $450 reporting course with Alex in the kitchen yesterday and coming away thinking it sounded okay. I cannot find written approval, so I have not booked anything.
- **Jordan Lee, Tue, 17 Nov, 13:12 AEST:** Please get written budget approval before booking external training. A conversation about an option is not the same as a confirmed booking approval.
- **Sam Patel, Wed, 18 Nov, 13:22 AEST:** The course place is still available. I am waiting for confirmation before paying or booking it.

**Write your own draft:** How would you describe your recollection and request clear confirmation before booking the course?

**Check the result:** Sam recalls a kitchen conversation but has no written approval and has not booked. Jordan's policy is not evidence of what Alex said. Whether Alex approved the spend verbally remains unverified.

## What to compare

- Does the reply keep your request and meaning while changing the tone?
- Are evidence links from this conversation, and do the source messages actually support the associated claims?
- Does the reply avoid promising deadlines, accepting blame or asserting motives that you did not supply?
- For situation 12, does it recognise the conflicting invitation and acknowledgement rather than support "nobody told me"?
- For situations 8 and 13, does it keep uncertainty visible instead of inventing a precise instruction or a verbal approval?
- Can you edit the suggestion and regenerate in another tone while retaining the selected message and original draft?

Historical context remains unchanged when a situation is selected; selecting a manager message does not automatically mark that message or any other record as verified evidence. The app never sends the reply.
