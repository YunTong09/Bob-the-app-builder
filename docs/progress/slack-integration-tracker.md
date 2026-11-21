# Rage-to-Reply Slack App 整合計畫

更新日期：2026-11-21

## 交付目標

沿用已部署的 [Rage-to-Reply Web App](https://ragetoreply.tech)，提供兩個入口，共用 FastAPI 的生成、Memory、佐證驗證及使用量控管。

| 入口 | 使用者流程 |
| --- | --- |
| Slack App | 在 Slack 開啟 App Home，可開始改寫或前往網站。也可從一則訊息的 **Rewrite with Rage-to-Reply** 捷徑開啟 Modal，確認選取的訊息、輸入草稿、選語氣，在 Slack 內預覽 AI 回覆。由使用者決定如何使用回覆。 |
| 網站 | 登入後到 **Memory → Import from Slack**，貼上經授權的 **Slack 頻道 ID（Channel ID）**，預覽訊息，選取後確認匯入。之後可在網站生成引用這些資料的回覆。 |

此計畫的 Slack ID 指頻道 ID。使用者 ID 或工作區 ID 無法直接指定要讀取的對話。頻道 ID 只定位資源；讀取仍需工作區授權、伺服器端 Slack 憑證及使用者自己的頻道存取權。P0 限單一受邀 Slack 工作區與一個受控的公開測試頻道，使用合成訊息。正式聊天內容、私人頻道和 DM 另行驗收授權後才納入。 [Slack conversations.history](https://docs.slack.dev/reference/methods/conversations.history/)

Slack 內使用 App Home 和 Block Kit Modal。網站原有的動畫、語音和完整 Memory 操作由 App Home 連到 HTTPS 網站使用。P0 透過團隊管理的工作區安裝，不需要先上 Slack Marketplace。 [Slack App Home](https://docs.slack.dev/surfaces/app-home/) · [Slack shortcuts](https://docs.slack.dev/interactivity/implementing-shortcuts/)

## 現況

- 網站部署和受邀登入已有團隊驗證紀錄。Web 帳號及記憶資料的跨帳號驗收範圍見 [Web App tracker](web-app-integration.md)。
- 網站已有 Slack Channel ID、預覽、勾選與確認匯入介面。FastAPI 已有 `POST /api/slack/preview` 和 Memory 匯入 API。預覽目前只支援伺服器設定的一個頻道。這些是可重用的程式碼，部署環境仍須驗證 Slack token、權限和受邀帳號的授權。 [API Contract](../API_CONTRACT.md#slack-channel-preview-single-user-demo-extension)
- `slack/` 有早期 Bolt、Socket Mode、Modal 和 Mock 原型。可重用經確認的 Modal 欄位及元件。新版 P0 的生成接回已部署的 FastAPI，共用 Claude 和佐證流程。

## P0 任務

| Task ID | 任務 | 狀態 | 相依 |
| --- | --- | --- | --- |
| SLACK-01 | 安裝 Slack App、驗證 callbacks 和帳號關聯 | TODO | 已部署 Web App、測試工作區管理員 |
| SLACK-02 | Slack 內生成及檢視回覆 | TODO | SLACK-01 |
| SLACK-03 | 網站輸入頻道 ID、預覽及選取匯入 | IN PROGRESS | SLACK-01 提供安裝及測試授權；可先驗現有 UI |
| SLACK-04 | 部署整合與雙入口驗收 | TODO | SLACK-02、SLACK-03 |

### SLACK-01 — 工作區安裝與信任邊界

- [ ] 在測試工作區安裝 Slack App，啟用 Home tab、訊息捷徑和 Interactivity，建立部署可重現的 App manifest。
- [ ] 以現有 HTTPS 部署接收 Slack callback。重新利用 Bolt 時採 HTTP receiver，維持單一 callback ingress。callback 驗證原始 request body 的 Slack 簽章、時間與工作區，和網站登入頁分開處理。Slack 憑證存在伺服器的秘密管理機制。
- [ ] 在伺服器建立每個受邀 Web 帳號和 `team_id + user_id` 的核准對應。先用單一工作區的管理員核准對應驗收，未綁定 Slack 使用者引導至網站或聯絡管理員後再生成。Slack 發出的請求身分和 Web owner 都由伺服器解析，並共用生成限額。
- [ ] 支援安裝／移除 App 後正常更新授權。以最小 scopes 驗收捷徑及必要的頻道讀取，P0 不需要發訊息權限。 [Slack 簽章驗證](https://docs.slack.dev/authentication/verifying-requests-from-slack/) · [Slack App Home](https://docs.slack.dev/surfaces/app-home/)

**驗收**　兩位受邀使用者都能開啟 App Home。錯誤簽章、未授權工作區及未綁定帳號在 Claude 呼叫前被拒絕。Slack callback 不會被網站邀請碼登入頁重導向。

### SLACK-02 — 直接在 Slack 內改寫

- [ ] App Home 提供開始改寫與開啟網站。首頁入口由使用者填工作訊息，訊息捷徑則用選取的 Slack 訊息作為工作訊息。
- [ ] Modal 支援草稿、三種語氣及明確的 Generate。即時回覆 Slack interaction，將較慢的 Claude 工作放在後續處理，以 `views.update` 顯示等待、結果或重試。若部署環境需要跨程序交付結果，使用可追蹤的工作狀態，並對重複提交做去重。 [Slack 確認時限](https://docs.slack.dev/tools/bolt-js/concepts/acknowledge/) · [Slack views.update](https://docs.slack.dev/reference/methods/views.update/)
- [ ] 沿用 FastAPI 的生成與佐證流程。Modal 顯示可檢視的建議回覆、重點與必要警告。App 不發送 Slack 訊息，也不寫入原本的 Composer。

**驗收**　使用真實 Slack 工作區開啟 Modal，以合成案例生成、換語氣重生及驗證失敗重試。回覆只對發起人可見。重複 callback 不會重複計費或生成。

### SLACK-03 — 網站以頻道 ID 匯入

- [x] 現有網站提供頻道 ID 輸入、預覽、選取和確認匯入 UI。
- [x] 現有 FastAPI 提供單頻道 allowlist 預覽及 Memory 匯入 API。
- [x] 新增最小權限 App manifest [deploy/slack/manifest.yaml](../../deploy/slack/manifest.yaml)（只有 `channels:history`，不發訊息、不用 Socket Mode），並在 [README](../../README.md#preview-and-import-a-slack-test-channel) 補上用 manifest 建 App、取得頻道 ID 與 bot token，以及用網站 **History → Import from Slack** 做本機驗收的步驟。
- [ ] 用真實測試工作區在本機（`demo_local`）驗收預覽、選取與匯入。需要測試工作區管理員建立並安裝 App，提供 bot token 與頻道 ID。
- [ ] 部署時配置 Slack 安裝的 bot token 和測試頻道 allowlist。公開頻道歷史使用 `channels:history` 且 bot 須在對應頻道。依設計所需加入驗證使用者所需的最小 scope。
- [ ] 綁定網站登入者與已核准的 Slack 帳號。伺服器在讀取前確認頻道屬於該工作區，且使用者可以讀取。Bot 能讀取不等同該網站使用者能讀取。授權無法確認時拒絕，移除使用者或撤回授權後停止後續預覽。
- [ ] 驗證按頁預覽、讀取失敗、Slack 限流、空結果、重試與選取。只在確認後儲存選取訊息，維持 owner 隔離，並保留原始時間和來源欄位。 [Slack 頻道歷史權限](https://docs.slack.dev/reference/methods/conversations.history/)

**驗收**　兩人用各自的受邀帳號測試。授權者能預覽與匯入選取訊息，另一人無法讀取未授權頻道，也無法在自己的 Memory 或生成佐證中看到對方的匯入資料。

**Blocker（部署）**　部署站目前不可只靠設定開啟預覽。`POST /api/slack/preview` 在 invite 模式只檢查登入，所以設了 `SLACK_BOT_TOKEN` 後，每個受邀帳號都能讀 allowlist 頻道，不符合上方驗收。[部署指南](../../deploy/gce/README.md#operations)因此維持不設 token。要先完成帳號綁定與讀取前的授權檢查，並更新 [API Contract](../API_CONTRACT.md#slack-channel-preview-single-user-demo-extension)（目前定義為單一使用者 demo），才能在部署站設定 token。

### SLACK-04 — 部署及交付

- [ ] 從同一部署版本測 Slack 內生成和網站以 Channel ID 匯入後生成。記錄 commit、workspace、測試帳號類型及結果。
- [ ] 驗收帳號與資料隔離、撤權、429、上游錯誤、重複提交與日誌。日誌只保留診斷所需的事件和結果，不包含 token、原始草稿或聊天內容。
- [ ] 更新部署操作說明及必要的 API Contract，再讓隊友從另一台電腦驗收兩個入口。

**驗收**　受邀隊友用同一個已部署版本，在 Slack 完成改寫，也能在網站用頻道 ID 預覽與匯入合成對話。失敗處理、最後一輪授權與資料隔離測試都有紀錄。

## 後續發布

多工作區安裝再做 OAuth 安裝流程、每個 workspace 的 token 與授權隔離、取消安裝與撤權，以及 Slack Marketplace 發布。私人頻道、DM、同步或其他讀取範圍依實際需求另外審查。 [Slack OAuth 安裝](https://docs.slack.dev/authentication/installing-with-oauth/)

## 驗證與更新

本次根據目前程式碼、Web API Contract、既有部署紀錄和 Slack 官方文件重新規劃。尚未執行新版 Slack App 的真實安裝、Claude 生成或部署測試。每項完成後記錄 commit、測試環境、scope 與驗證結果，再改成 DONE。

| 日期 | 變更 |
| --- | --- |
| 2026-11-21 | 以已部署 Web App 的雙入口交付計畫取代舊 Socket Mode／Mock Prototype 任務。 |
| 2026-11-21 | SLACK-03：新增 Slack App manifest 與本機真實 Slack 驗收步驟；記錄部署站需先完成帳號授權檢查。僅文件與設定檔，manifest 尚未在 Slack 實際匯入，也未做真實 Slack 驗收。 |
