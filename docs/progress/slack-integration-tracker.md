# Rage-to-Reply Slack Integration Tracker

## Progress Dashboard

| Metric | Value |
| --- | --- |
| Overall Progress | **0%** (0 / 7) |
| Completed Tasks | 0 |
| In Progress Tasks | 0 |
| Blocked Tasks | 1 · TASK-01 |
| Current Priority | 取得測試 workspace 的 Slack 憑證並完成 Socket Mode 連線驗收 |
| Next Recommended Task | TASK-01 · 完成真實連線驗收，通過後再開始 TASK-02 |
| Last Updated | 2026-11-21（Australia/Brisbane） |

`Progress = DONE Tasks / 7 × 100%`。只有實作完成且通過驗收的任務才計入。

## 目標與現況

本階段交付 **Slack 原生 Modal Mock Demo**。使用 Slack Bolt for JavaScript 搭配 TypeScript、Socket Mode、Message Shortcut 與 Block Kit。流程為 **Slack Message → Message Shortcut → Input Modal → Mock Rewrite → Result Modal**。Mock 不依賴真實 Claude API、Memory Database，也不自動發送 Slack 訊息。結果在 Modal 內呈現。Slack Composer 原地改寫屬於後續整合。

- 初次盤點時，本機 `main` 為 `4fc1fcd`，工作目錄乾淨，落後當時已取得的 `origin/main` 一筆。之後 `main` 與 `origin/main` 已同在 `4ac176e`。工作目錄有 Next.js 網頁原型和 `src/lib/mock.ts`。TASK-01 已新增 Slack Bolt 啟動入口，Modal handlers 由後續任務實作。
- `origin/main` 的 `4ac176e` 新增 Python/FastAPI 後端。`backend/api/app.py` 定義 `POST /api/reply/generate`，另有 mock model 和 API fixtures。已查閱 Git 中的原始碼並確認後端檔案現已在工作目錄，API 尚未執行或接入 Slack。此階段以既有網頁 mock 和 Python fixtures 為重用來源，由 Slack 的 mock adapter 回應，後續再切換到 Python API。
- 參考 [API Contract](../API_CONTRACT.md)、[Architecture](../ARCHITECTURE.md)、[Product Spec](../PRODUCT_SPEC.md) 與 [Frontend Contract](../FRONTEND_CONTRACT.md)。此追蹤表描述獨立的 Slack Mock Demo 範圍，現有產品與 API 規格由各自文件維護。

## 任務追蹤表

| ID | Task | Status |
| --- | --- | --- |
| TASK-01 | Project Setup & Slack Connection | BLOCKED |
| TASK-02 | Slack Message Shortcut | TODO |
| TASK-03 | Input Modal | TODO |
| TASK-04 | Mock AI Rewrite Service | TODO |
| TASK-05 | Processing & Result Modal | TODO |
| TASK-06 | Error Handling & Retry | TODO |
| TASK-07 | Team Testing & Demo Validation | TODO |

### TASK-01：Project Setup & Slack Connection

**Status:** BLOCKED

**Objective:** 建立可連到測試 workspace 的 TypeScript Slack Bolt 入口。

**Implementation Checklist:**

- [x] 檢查現有專案、依賴與 Git 基線。
- [x] 建立 Bolt TypeScript 入口、啟動與型別檢查指令。
- [x] 啟用程式端 Socket Mode，定義環境變數並確認本機憑證檔受 Git 忽略。
- [ ] 在 Slack 端確認測試 App 已安裝、Socket Mode 已開啟並提供有效憑證。
- [ ] 驗證測試 workspace 的真實連線並記錄去除敏感資訊的結果。

**Acceptance Criteria:**

- 使用測試 App 啟動後成功建立 Socket Mode 連線。
- 缺少必要環境變數時快速失敗，且輸出不含 token。

**Files:** 新增 `slack/app.mts`，修改 `package.json`、`package-lock.json`、`.env.example` 與本追蹤文件。

**Dependencies:** 無前置任務。真實驗收需要已安裝至測試 workspace 的 Slack App。

**Verification:**

- 在 Node.js 24 執行 `npm run slack:typecheck` 與 `node --check slack/app.mts`，皆通過。`npm ls @slack/bolt --depth=0` 確認安裝版為 5.1.0。
- 以空白及格式錯誤的測試值執行 `npm run slack:start`，入口載入 Bolt 後皆以狀態碼 1 結束，只提示環境變數名稱。
- `git check-ignore -v .env.slack.local` 確認既有 Git ignore 規則涵蓋該檔。
- 根目錄的全專案 `tsc --noEmit --incremental false` 等待期間未回傳結果，已中止。Slack 專用檢查已完成。
- 未執行真實 Socket Mode 連線測試。

**Blockers:** 目前執行環境及本機環境檔未提供 `SLACK_BOT_TOKEN` 與 `SLACK_APP_TOKEN`。Slack App 是否已安裝以及 Slack 端 Socket Mode 設定仍待確認。

**Notes:** 使用 Node.js 24 直接執行 TypeScript 入口，沿用根目錄的 npm 套件，可獨立於網頁和 Python 執行。將已安裝至測試 workspace 的 App 的 bot token 與具 `connections:write` 的 app-level token 設在執行環境，或填入 Git 忽略的 `.env.slack.local`，再從專案根目錄執行 `npm run slack:start`。入口先等待 Bolt 驗證 bot token，再等待 Socket Mode 啟動。 [Slack Socket Mode 設定](https://docs.slack.dev/tools/bolt-js/concepts/socket-mode/)

### TASK-02：Slack Message Shortcut

**Status:** TODO

**Objective:** 從指定 Slack 訊息開啟對應的 Rage-to-Reply Modal。

**Implementation Checklist:**

- [ ] 設定 Message Shortcut 與穩定的 callback ID。
- [ ] 取得選取訊息文字與必要的 workspace、使用者、對話和訊息識別資訊。
- [ ] 及時確認互動並用 trigger ID 開啟 Modal。

**Acceptance Criteria:**

- 使用者從指定訊息的選單啟動時，Modal 開啟且主管訊息與選取內容一致。
- 互動在 Slack 的 3 秒期限內確認，選取訊息不會被自動發送或儲存為 Memory。

**Files:** 尚無 Slack handler 或 manifest。現有 `docs/FRONTEND_CONTRACT.md` 提供原流程參考。

**Dependencies:** TASK-01。可先用最小 Modal 驗證入口，再由 TASK-03 補齊表單。

**Verification:** 已用 `rg` 搜尋 Slack 互動相關程式，未見 Shortcut handler。尚未測試 Slack 互動。

**Blockers:** 無已確認阻礙，等待 TASK-01。

**Notes:** 以本次明確選取的訊息作為上下文。

### TASK-03：Input Modal

**Status:** TODO

**Objective:** 在 Slack 原生 Modal 收集草稿與語氣。

**Implementation Checklist:**

- [ ] 用 Block Kit 顯示選取的主管訊息與多行草稿欄位。
- [ ] 提供 Diplomatic、Neutral、Assertive 與 Rewrite。
- [ ] 驗證空白輸入、長度與允許的語氣值。

**Acceptance Criteria:**

- 提交有效輸入時可取得原主管訊息、草稿與所選語氣。
- 空白或不合法輸入顯示欄位錯誤並保留輸入。

**Files:** Slack view 路徑待定。欄位與語氣參考 `docs/API_CONTRACT.md`。

**Dependencies:** TASK-02。

**Verification:** 已用 `rg` 比對程式碼和 API Contract，語氣已有規格，未見 Slack 輸入 view。尚未提交實際 Modal。

**Blockers:** 無已確認阻礙，等待 TASK-02。

**Notes:** 草稿輸入留在本次操作，避免寫入日誌或 Modal metadata。

### TASK-04：Mock AI Rewrite Service

**Status:** TODO

**Objective:** 提供可獨立呼叫且可日後替換成 Python API 的固定 mock 回覆。

**Implementation Checklist:**

- [ ] 在 Slack 呼叫處定義可切換的 Rewrite Service 介面。
- [ ] 重用合成案例，回傳固定的回覆及一筆確實支持主張的合成佐證。
- [ ] 支援離線測試，並提供可控制的失敗案例供 TASK-06 使用。

**Acceptance Criteria:**

- 同一測試輸入回傳固定結果，並保留呼叫時選擇的語氣供 UI 顯示。
- 無 Claude key、Python server 或 Memory DB 時仍可取得 mock 結果。

**Files:** 現有 `src/lib/mock.ts`、`src/lib/schema.ts`、`docs/API_CONTRACT.md`。`origin/main` 有 `backend/services/mock.py` 和 `backend/fixtures/generate_response.json`。Slack adapter 路徑待定。

**Dependencies:** 已有 API Contract 提供介面參考。可與 TASK-01 至 TASK-03 平行開發。

**Verification:** 已審閱現有 TypeScript mock 與 Git 中的 Python mock 和 fixture。未見 Slack 專用 adapter，未執行服務測試。

**Blockers:** 無已確認阻礙。

**Notes:** 舊網頁 mock 已存在，其 `relatedMemories` 不代表已驗證的 evidence。Slack 任務只追蹤新的介面與驗收。

### TASK-05：Processing & Result Modal

**Status:** TODO

**Objective:** 依序在同一個 Modal 顯示處理中與改寫結果。

**Implementation Checklist:**

- [ ] 提交後先確認互動並切換至處理中。
- [ ] Mock 完成後更新同一個 Modal，顯示專業回覆、語氣和一筆合成佐證。
- [ ] 將服務與畫面狀態串接並維持回覆和佐證分區。

**Acceptance Criteria:**

- 故意延遲 mock 時能看到處理中，完成後在同一個 Modal 看到回覆、正確語氣和佐證。
- 全程不發佈 Slack 訊息，也不需要自動寫入原 Composer。

**Files:** Slack views 和 handlers 路徑待定。網頁呈現參考 `src/app/page.tsx` 和 `src/components/ComparePanel.tsx`。

**Dependencies:** TASK-03、TASK-04。

**Verification:** 已檢查網頁原型結果入口與 Slack 相關檔案清單。尚未測試 Slack Modal 更新流程。

**Blockers:** 無已確認阻礙，等待輸入 Modal 和 mock adapter。

**Notes:** 舊網頁的 Copy reply 不屬於本 Demo 流程。

### TASK-06：Error Handling & Retry

**Status:** TODO

**Objective:** 讓使用者能從改寫失敗恢復，並正確處理重複操作和關閉。

**Implementation Checklist:**

- [ ] 涵蓋空白輸入與 mock 失敗。
- [ ] 提供 Retry，保留草稿和語氣。
- [ ] 防止同一操作重複發起改寫。
- [ ] 處理關閉、取消，並忽略已取消的延遲結果。

**Acceptance Criteria:**

- 空白輸入不呼叫服務。模擬失敗後能重試，且草稿與語氣保留。
- 重複提交只觸發一次改寫。取消後的結果不會更新 Modal。

**Files:** Slack handlers、views 和測試檔路徑待定。網頁錯誤處理可在 `src/app/page.tsx` 查閱。

**Dependencies:** TASK-03、TASK-04、TASK-05。

**Verification:** 已查閱網頁錯誤狀態，未見 Slack 專用重試或取消流程。尚未執行失敗與重複提交測試。

**Blockers:** 無已確認阻礙，等待 Slack 結果流程。

**Notes:** 重試狀態限於本次操作。取消後可清理或讓短效狀態過期，日誌不記錄原始草稿。

### TASK-07：Team Testing & Demo Validation

**Status:** TODO

**Objective:** 由另一名隊友在測試 workspace 完成兩分鐘內的 Slack Demo。

**Implementation Checklist:**

- [ ] 在測試 workspace 準備已安裝 App、合成主管訊息與測試案例。
- [ ] 由至少一名隊友使用自己的 Slack 帳號跑完整流程。
- [ ] 計時並測試至少一次重試，記錄結果、已知限制與是否通過。

**Acceptance Criteria:**

- 另一位隊友在兩分鐘內從指定訊息取得私人 mock 結果，畫面顯示語氣與佐證。
- 有可追溯的測試紀錄，並清楚標示 mock 範圍、未驗證的真實 API 與安裝範圍。

**Files:** 本追蹤文件。測試腳本或其他測試紀錄路徑待定。

**Dependencies:** TASK-01 至 TASK-06。

**Verification:** 尚未執行 Slack 團隊測試或計時。

**Blockers:** 無已確認阻礙。測試 workspace 和隊友參與仍待確認。

**Notes:** 同一測試 workspace 的驗收不涵蓋跨 workspace 安裝。

## AI 自動更新規則

1. 開始 Slack Integration 工作前讀取本文件，確認 Dashboard、任務與依賴。
2. 沿用已驗收的實作，避免重複開發或覆蓋隊友修改。
3. 完成工作後執行相關測試，更新任務狀態、Checklist、涉及檔案和實際指令。明列未驗證部分。
4. 狀態只使用 `TODO`、`IN PROGRESS`、`BLOCKED`、`DONE`。只有通過驗收才能標記 `DONE`。有確定阻礙時標記 `BLOCKED` 並說明原因，正常任務依賴留在 Dependencies。
5. 更新 Dashboard 的計數、日期與下一個建議任務，再補一筆 Change Log。
6. 未執行的測試不可記為通過。Mock 驗收與真實 API 整合分開記錄。
7. 只修改本次任務涉及的內容。文件與日誌不得記錄 API key、Slack token 或其他敏感資訊。

## Change Log

| 日期 | Task ID | 變更摘要 | 驗證結果 | Git Commit |
| --- | --- | --- | --- | --- |
| 2026-11-21 | TASK-01 至 TASK-07 | 建立基線與七項任務。TASK-01 完成 repo 盤點，確認遠端已有 FastAPI 程式碼。 | 以 `git status --short --branch`、`git ls-files`、`git diff --name-status HEAD..origin/main`、`git show origin/main:backend/api/app.py` 和程式碼搜尋完成唯讀盤點。尚無功能測試。 | 追蹤文件尚未提交。查閱基線為 `4fc1fcd`、`4ac176e`。 |
| 2026-11-21 | TASK-01 | 新增 TypeScript Slack Bolt 入口、Socket Mode 啟動指令和環境變數範例。 | TypeScript 檢查與無憑證啟動檢查通過，確認本機憑證檔受 Git 忽略。缺少憑證，未測試真實連線。 | 尚未提交。 |
