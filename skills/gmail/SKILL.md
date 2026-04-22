---
generated: false
type: data
name: gmail-secretary
description: "信件秘書：每小時讀 inbox，逐 thread 判斷行動（待回覆、截止日、預約）→ Calendar 通知 + skill dispatch，再 Gmail-as-state 歸檔。僅由 claude.ai Routines 觸發。MANDATORY TRIGGERS：gmail-secretary、信件秘書、信件處理、inbox 處理、email triage、收信。"
---

# Gmail Secretary

信件秘書。每小時讀一次 inbox，核心價值排序：

1. **行動偵測**：待回覆、待辦、有截止日 → Calendar 通知
2. **醫學電子報 dispatch**：PubMed alerts → `pubmed-digest` skill
3. **安靜歸檔**：加 label、標已讀、歸檔，不打擾

分類是歸檔的副產品，不是目的。Label 的長期價值是給 agent 未來做 mass review 的索引。

> **術語校正**：產出中文時 apply `tw-terminology` skill。

---

## Architecture: Gmail-as-state (v4.0, 2026-04-19)

**Gmail labels are the single source of truth.** 沒有人類維護的規則表。`rules.tsv` 從 "authority" 降級為 agent runtime 的 ephemeral cache，每次執行前從 Gmail 當前狀態重建。

### 核心不變式

```
Copper 手動 label/archive 一封信
  = 直接教 agent（下一輪 rebuild 就學到）

Agent 學規則的方式：
  SELECT sender, label, COUNT(*)
  FROM Gmail threads
  WHERE has:userlabels AND -in:inbox AND newer_than:90d
  GROUP BY sender, label
  → sender_label_share > 0.8 → strong rule（直接套用）
  → 0.5–0.8           → weak rule（LLM 複核）
  → < 0.5 / no data   → LLM judge from subject+snippet
```

### 為什麼這樣做

| 問題 | 舊架構（rules.tsv 為 authority） | 新架構（Gmail-as-state） |
|---|---|---|
| Copper 手動 label | agent 下輪會依 rules.tsv 覆蓋 | agent 下輪把 Copper 的 label 當教材吸收 |
| 維護規則表 | 人類要編 TSV / YAML / GSheet | 零維護；label 即是規則 |
| 衝突仲裁 | rules.tsv 贏 | Copper 永遠贏（最新 label 即最新意圖） |
| Cold start | seed 規則可用，快 | 初期無歷史 → 全靠 LLM，慢但自學 |
| 一致性 | 強（規則固定） | 隨歷史自然漂移 |

### 取消項目

- ❌ `rules-candidates.tsv`（不再需要人類 approve 層）
- ❌ `feedback.md`（Gmail 手動 label 即回饋；不需自然語言檔）
- ❌ "每次執行最多自動新增 5 條規則" 的限制（rebuild 無上限概念）
- ❌ GSheet `Gmail Signal` 259 條 rules（authority 轉移到 Gmail；GSheet 可留作歷史參考）
- ❌ `copper/gmail_rules.yaml` 的 pending export（不再需要）

### 保留項目

- ✅ `action-patterns.tsv`（行動偵測，與 label 分類正交，自我迭代）
- ✅ 📬 Inbox 日曆的 event description 回饋管道（專用於 action-patterns 調參）
- ✅ `spam-rules.tsv`（垃圾信白名單較穩定，可持續使用）
- ✅ `rules.tsv`（意義重新定義：agent 每次 rebuild 寫入的 cache，Copper 可讀可忽略）
- ✅ `gate.tsv`（有新信才執行的開關）
- ✅ `log.tsv`（執行記錄）

---

## 執行模式

| 參數 | 值 |
|---|---|
| 觸發 | claude.ai **Routines** (cloud, hourly) — 取代舊 hm4 cron + Mail.app |
| 時長上限 | 10 分鐘 (Routines per-run budget) |
| 處理單位 | **逐 thread**（同 threadId 只處理最新一封） |
| 品質原則 | 寧可慢，不可漏掉需要行動的信 |

---

## Data Access: Gmail MCP (cloud Routines) / Gmail API (hm4 fallback)

**Mail.app AppleScript 禁用於排程任務** (Copper directive 2026-04-15, memory `feedback_no_mail_app.md`).
原因：macOS 更新每次撤銷 Automation 權限，launchd/cron 靜默 broken。AppleScript 只在互動 session OK。

### Primary: cloud Routines + Gmail MCP connector

預設觸發模式。Routines 用 Anthropic 託管 OAuth，免 macOS 權限互動。排程 via claude.ai Routines UI (cron_expression in UTC)。

Connector tools：
```
search_threads / get_thread          → 讀 thread
label_message / label_thread          → 加 Gmail label (= Mail.app mailbox)
unlabel_message (name="INBOX")        → 歸檔 (remove INBOX label)
create_draft                          → 草擬回覆
list_labels                           → 查 label 列表
```

**去重：** Gmail `threadId`（原生）。比 subject+sender+date hash 精確。

### Fallback: Gmail API (hm4 local Python)

若 cloud Routines 不可用（quota、API 暫斷），hm4 cron/launchd 可用 `google-api-python-client`，scope `gmail.modify`，token at `~/.local/share/deck/token.json`。

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
creds = Credentials.from_authorized_user_file("~/.local/share/deck/token.json")
svc = build("gmail", "v1", credentials=creds)
# svc.users().messages().list(userId="me", q="is:unread in:inbox newer_than:1h")
# svc.users().messages().modify(userId="me", id=..., body={"removeLabelIds":["INBOX"]})
```

### AppleScript: interactive only

當 Copper 在終端主動呼 `gmail-secretary`（macOS 可能 prompt Automation 權限，人類可點 Allow），**可**用 Mail.app AppleScript。
**不得在 cron/launchd/Routines 使用。**

## 核心流程

```
每小時 trigger：

  Phase 0 — Rebuild rules cache + 行動回饋吸收
    a. Gmail-as-state rebuild
       search_threads("has:userlabels -in:inbox newer_than:90d")
       → aggregate by sender → {sender: {label: count}} map
       → overwrite rules.tsv (cache, not authority)
       → strong: share > 0.8; weak: 0.5–0.8; none: < 0.5

    b. action-patterns 回饋
       掃 📬 Inbox 日曆 event descriptions（手機端 Copper 註記）
       → 修正 action-patterns.tsv（調 confidence、加 exclude、新增 pattern）
       → 已處理的註記標記 ✅
       (cold start: skip，用 seed action-patterns)

  Phase 1 — 逐 thread 判斷（一次一封好好想）
    search_threads("in:inbox") → 按 threadId 去重，保留最新一封
    逐 thread：
      a. get_thread → sender, subject, snippet, date
      b. 行動偵測：比對 action-patterns.tsv
         → 命中 → 建 📬 Inbox Calendar event / dispatch skill
      c. 歸檔判斷：
         strong rule (>0.8 sender→label history)  → label_message + unlabel("INBOX")
         weak rule (0.5–0.8)                      → LLM 看內容複核 → 套用或改 label
         no history                               → LLM 看 subject+snippet 判斷新 label → 直接套用
         spam-rules.tsv 命中                       → 歸 spam label

  Phase 2 — 收工
    寫 session summary 到 log.tsv
    記錄：處理封數、行動建立數、新 sender→label 對應數、cache rebuild 摘要
```

**沒有 Phase「歸檔維護」**：Gmail 自身就是歸檔狀態，不需另外維護規則表。Copper 任何時候手動改 label，下一輪 Phase 0 就吸收。

---

## 行動偵測

行動模式定義在 `action-patterns.tsv`（agent 內部檔，使用者不需維護）。

Seed 版隨 skill 打包，詳見 `references/action-patterns-seed.tsv`。

偵測後的 Calendar event 一律建在 📬 Inbox 日曆，格式：

```
標題：📬 {類型}：{from 姓名} — {subject 前 30 字}
描述：
- Gmail 連結：https://mail.google.com/mail/u/0/#inbox/{message_id}
- Thread ID: {thread_id}
- 偵測依據：{pattern_id} / {signal 摘要}
- （截止日類）截止：{extracted_date}
```

📬 Inbox 日曆 ID: `ef055539013afbb7fedd50abbfff381cc7d710d792be0d2a51194ce4870e83f8@group.calendar.google.com`

---

## 回饋迴路

Gmail-as-state 後只剩**一個**回饋管道，且只用於 action-patterns（label 分類靠 Gmail 手動操作即可）：

| 情境 | 回饋方式 | Agent 怎麼讀 | 修正對象 |
|---|---|---|---|
| 手機 / 桌面 | 📬 Inbox Calendar event description 加註記 | 掃 event descriptions | action-patterns.tsv |
| 任何裝置 | 直接在 Gmail UI 改 label / archive 狀態 | 下一輪 Phase 0 rebuild 自動吸收 | rules.tsv (cache) |

`feedback.md` (deprecated v4.0)：自然語言檔案不再需要，因為 label 變動已是直接訊號。

---

## TSV 檔案

所有 TSV 路徑：`~/我的雲端硬碟/appscript-projects/gmail-secretary/`

> **local-fs only**：所有 TSV 讀寫一律走本機路徑（GDrive sync 已同步至本機）。禁止透過 GDrive MCP 讀取。

| 檔案 | 誰寫 | 誰讀 | 用途 |
|---|---|---|---|
| gate.tsv | Apps Script(=1) + agent(=0) | agent | 有新信才執行的開關 |
| rules.tsv | **agent (rebuild each run)** | agent | **Cache** — Gmail-as-state 派生，非 authority。Copper 不需編輯 |
| spam-rules.tsv | agent | agent | 垃圾信過濾（白名單較穩定，可長期累積） |
| action-patterns.tsv | agent 自己 | agent 自己 | 行動偵測模式庫（自我迭代核心；與 label 分類正交） |
| log.tsv | agent | agent | 執行記錄 |

Deprecated (v4.0): `rules-candidates.tsv`, `feedback.md`. 如有舊檔可保留為歷史紀錄，但 agent 不再讀寫。

### rules.tsv 欄位（v4.0 cache schema）

```
sender	label	count	share	action	last_seen	confidence
```

- `sender`：full email address (e.g., `noreply@nejm.org`)
- `label`：Gmail label path (e.g., `學術/NEJM`)
- `count`：past 90d 命中數
- `share`：此 sender 的所有 labels 中 label 占比 (0.0–1.0)
- `action`：`archive` (default) / `keep` (此 sender 歷史曾保留 inbox 比例 > 30%)
- `last_seen`：最近一次此 (sender, label) 對應出現的日期
- `confidence`：strong (>0.8) / weak (0.5–0.8)

Cache 每次 Phase 0 rebuild，schema 變動可隨意 (agent 自寫自讀)。Copper 不需編輯。

label 層級不限（1 層 `合作邀約`、2 層 `學術/NEJM`、3 層 `學術/PubMed/ESRD` 皆可）。data-driven：tag 體系靠 Copper 在 Gmail UI 直接命名建立。

### action-patterns.tsv 欄位

```
id	pattern_type	signal	action_template	confidence	exclude	note
```

詳見 `references/action-patterns-seed.tsv`。

---

## 與現有 skill 的整合

| 信件類型 | dispatch | 備註 |
|---|---|---|
| PubMed Alert | `pubmed-digest` | 觸發摘要生成 |
| NEJM TOC / NEJM AI / NEJM Clinician | `proj/journal` pipeline (Tier 1) | 全文下載 + /note-writer |
| NEJM Evidence / JAMA / BMJ / Lancet / AIM | `proj/journal` pipeline (Tier 2) | /appraise 篩選 → selected fulltext |
| Nephrology TOC (JASN/CJASN/KI/NDT等) | `proj/journal` pipeline (Tier 2) | /appraise 篩選 |
| 其他 | — | 歸檔或行動偵測 |

---

## 自我迭代治理約束

- **迭代標的**：action-patterns 品質（漏報↓ 誤報↓），label 分類交給 Gmail-as-state 自然演化
- **No rules cap**：rules.tsv = rebuild cache，無「每次新增上限」概念
- **新 label 創建**：LLM 在 Phase 1c 判斷「需新 label 表達此類」即直接 `label_message` + 留下 log，不再走 candidates 確認流程；Copper 事後在 Gmail UI 看到新 label，可手動合併/重命名/刪除
- **無聲衝突優先 Copper**：若 agent 之前 label 為 X，Copper 改成 Y，下輪 sender→label 統計 Y 計數提升，最終取代 X
- **Sender domain 公用** (gmail.com / yahoo.com)：強制要求 subject 線索，不能僅靠 sender 域名套規則

---

## Changelog

| Version | Date | Changes |
|---|---|---|
| v4.0 | 2026-04-19 | **BREAKING — Gmail-as-state**: Gmail labels 升格為 single source of truth。`rules.tsv` 從 authority 降為 ephemeral cache，每次執行前 rebuild from Gmail current state。Copper 手動 label 即直接教學，零維護。**Deprecated**: `rules-candidates.tsv`、`feedback.md`、「每次新增 5 條規則」上限、GSheet `Gmail Signal` 259 條 authority、`copper/gmail_rules.yaml` pending export。**Kept**: action-patterns.tsv (與 label 分類正交) + 📬 Inbox 日曆回饋管道 (專用 action-patterns 調參) + spam-rules.tsv。 |
| v3.0 | 2026-04-15 | **BREAKING, reverse of v2.0**: Mail.app AppleScript 禁用於排程 (Copper 2026-04-15, `feedback_no_mail_app.md` — macOS 更新撤權)。主路徑改 cloud Routines + Gmail MCP connector。Fallback = hm4 Python Gmail API。AppleScript 保留僅限互動 session (人類可點 Allow)。threadId 去重回歸 Gmail 原生。執行時長上限改 10 分鐘 (Routines per-run budget)。 |
| v2.0 | 2026-04-05 | (superseded by v3.0) Gmail MCP 禁用。全面遷移至 Mail.app AppleScript（§2.13）。0 token data access。threadId 去重改為 subject+sender+date。 |
| v1.2 | 2026-03-16 | basepath 確認 gmail-secretary。TSV access: local-fs only, no GDrive MCP。新增 gate.tsv 至檔案表。 |
| v1.0 | 2026-03-15 | 初版。行動偵測優先架構。逐 thread 處理。三階段流程。回饋迴路。自我迭代 action-patterns。 |
