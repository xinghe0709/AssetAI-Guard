# Email Notification 设计建议（是否建表 + 技术选型）

## 1) 目前是否“必须”新建表？

### 结论（给汇报可直接说）

- **如果只要求“发出去”**：技术上可以不建表（直接 SMTP/API 调用）。
- **如果要求可审计、可追踪、可重试、可统计投递成功率**：**建议新建表**。

你的客户已经明确强调 traceable records，因此推荐建表。

---

## 2) 推荐最小数据库设计

建议新增一张表：`email_notifications`

字段建议：

- `id`（主键）
- `evaluation_log_id`（FK -> `evaluation_logs.id`，关联触发来源）
- `recipient`
- `subject`
- `template_version`（可选）
- `status`（`PENDING` / `SENT` / `FAILED` / `RETRYING`）
- `provider`（如 `sendgrid` / `ses` / `smtp`）
- `provider_message_id`（供应商回执 ID）
- `error_message`（失败原因）
- `attempt_count`
- `sent_at`
- `created_at`
- `updated_at`

这样你就能在 dashboard/email logs 页面准确展示“发没发、发给谁、失败原因、重试次数”。

---

## 3) 发邮件技术怎么选更合适

### 推荐方案（生产优先）

1. **邮件供应商 API**：`SendGrid` 或 `AWS SES`
2. **异步任务队列**：`Celery + Redis`
3. **后端框架内发送层**：在 Flask service 中封装 `EmailSender`

为什么：

- 比裸 SMTP 更稳定（配额、投递监控、回执更完整）
- 失败可重试（网络抖动不影响主业务请求）
- 易做告警与统计（成功率、延迟、失败类型）

### 轻量方案（Demo / 内网）

- `Flask-Mail` + 企业 SMTP（如 Office365）
- 不上队列，先同步发送（或简单线程）

适合 PoC，但不建议长期生产使用。

---

## 4) 与你当前系统的落地建议（分两阶段）

### Phase 1（你现在可快速交付）

1. 新建 `email_notifications` 表
2. 在 `POST /evaluations/check` 结果为 `Non-Compliant` 时写一条 `PENDING` 记录
3. 用后台任务发送邮件，回填 `SENT/FAILED`
4. React 邮件模块改为读取真实日志接口

### Phase 2（生产增强）

1. 加 webhook（供应商回执：delivered/bounce/spam）
2. 加重试退避策略（指数退避）
3. 加模板版本管理与审批
4. 加 tenant/org 级别通知策略

---

## 5) 一句话建议（汇报版）

“如果只是临时发邮件，可以不建表；但在客户强调审计可追踪的前提下，建议新增 `email_notifications` 表，并采用 `邮件供应商 API + 异步队列`，这样才能保证可追踪、可重试、可统计。” 

