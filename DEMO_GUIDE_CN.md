# AssetGuard AI 中文演示文档（数据库 + 新增内容 + 运行指南）

> 目标：用于项目汇报、客户演示、团队交接。  
> 版本：Demo 版（含评估看板 + 轻量邮件通知）。

---

## 1. 系统概览（你可以先讲这个）

当前仓库包含两个核心后端相关项目 + 一个前端演示模块：

1. **主后端：`AssetGuard AI/`**
   - 提供认证、资产管理、评估计算、评估历史、dashboard summary、邮件 demo API。
2. **AI 提取工具：`gjp-assetguard-extraction-tool/`**
   - 从文档提取资产信息并产出 JSON。
3. **邮件前端模块：`email-notification-react/`**
   - React 页面，用于维护邮件偏好、模板、日志查看（演示用）。

---

## 2. 数据库讲解（重点）

### 2.1 当前数据库核心实体

- `users`：用户与角色（System_Admin / Asset_Manager / Contractors）
- `locations`：地点
- `assets`：资产
- `load_capacities`：资产承载指标
- `evaluation_logs`：评估日志（审计核心）

### 2.2 为什么 `evaluation_logs` 是核心

每次调用评估接口都会写入 `evaluation_logs`，字段包含：

- 谁做的（`user_id`）
- 对哪个资产（`asset_id`）
- 用什么设备（`equipment`, `equipment_model`）
- 输入值和单位（`load_parameter_value`, `load_parameter_metric`）
- 匹配了哪个承载规则（`matched_capacity_name`）
- 结果是什么（`status`, `overload_percentage`）
- 备注和时间（`remark`, `evaluated_at`）

这保证了：

1. **evaluation history**（可回溯）
2. **persistent storage**（落库持久化）
3. **traceable records**（审计追踪）

### 2.3 轻量邮件 Demo 的存储策略

- 当前采用 **内存存储**（`AlertService` 的 in-memory store）保存：
  - 邮件偏好
  - 邮件模板
  - 邮件发送日志（demo）
- 适用于 demo 与功能验证；生产建议升级到数据库表（如 `email_notifications`）。

---

## 3. 你新增了什么（可直接汇报）

## 3.1 评估看板能力（后端）

新增聚合接口：

- `GET /api/v1/evaluations/dashboard-summary`
  - 返回：总评估数、合规率、超载统计、设备分布、Top 资产、最近评估。

并保留历史分页接口：

- `GET /api/v1/evaluations/history`

## 3.2 内置 Dashboard 页面（后端内嵌前端）

- 页面地址：`/dashboard`
- 可登录后查看 summary 与 recent evaluations。

## 3.3 轻量邮件通知 Demo（后端）

新增 `alerts` 路由：

- `GET /api/v1/alerts/email-logs`
- `GET /api/v1/alerts/email-preferences`
- `PUT /api/v1/alerts/email-preferences`
- `GET /api/v1/alerts/email-template`
- `PUT /api/v1/alerts/email-template`

业务联动：

- 当 `POST /api/v1/evaluations/check` 结果为 `Non-Compliant` 时，触发通知逻辑并记录日志。

SMTP 行为：

- 默认 `SMTP_SUPPRESS_SEND=true`：仅记录日志，不真实发信（适合演示）。
- 配置 SMTP 后可改为真实发送。

## 3.4 React 邮件模块（前端）

`email-notification-react/` 提供：

- 通知偏好编辑
- 邮件模板编辑
- 沟通日志查看

可与上述 `/api/v1/alerts/*` 对接。

---

## 4. 如何运行系统（一步步）

## 4.1 启动主后端（必须）

```bash
cd "AssetGuard AI"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m flask --app assetguard_app.py db upgrade
python -m flask --app assetguard_app.py seed
python -m flask --app assetguard_app.py run --port 5000
```

启动后地址：

- Health: `http://127.0.0.1:5000/api/v1/health`
- Dashboard: `http://127.0.0.1:5000/dashboard`

## 4.2 启动 AI 提取工具（可选）

```bash
cd "gjp-assetguard-extraction-tool"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

地址：`http://127.0.0.1:5001`

## 4.3 启动 React 邮件模块（可选）

```bash
cd email-notification-react
npm install
npm run dev
```

通常地址：`http://127.0.0.1:5173`

---

## 5. 演示脚本（推荐顺序）

### Step 1：登录

使用 demo 账号：

- Admin：`admin@demo.com / admin123`
- Manager：`manager@demo.com / manager123`

### Step 2：制造评估数据

调用 `POST /api/v1/evaluations/check` 两次：

1. 一次 Compliant
2. 一次 Non-Compliant

### Step 3：展示“历史可追溯”

调用：

- `GET /api/v1/evaluations/history?page=1&pageSize=20`

讲解重点：

- 记录了谁、何时、设备、参数、结果、备注。

### Step 4：展示“管理看板”

打开：

- `http://127.0.0.1:5000/dashboard`

讲解重点：

- 总量、合规率、超载统计、最近评估。

### Step 5：展示“邮件 Demo”

调用并展示：

- `GET /api/v1/alerts/email-logs`
- `PUT /api/v1/alerts/email-preferences`
- `PUT /api/v1/alerts/email-template`

讲解重点：

- 非合规触发后可看到通知日志；
- 当前是轻量 demo，默认不真实发信（可后续切换到真实 SMTP）。

---

## 6. 风险与后续规划（汇报加分项）

### 当前 Demo 限制

- 邮件偏好/模板/日志是内存存储，服务重启会丢失。
- 默认不开真实外发（`SMTP_SUPPRESS_SEND=true`）。

### 下一步建议（生产化）

1. 新增 `email_notifications` 表持久化日志；
2. 接入供应商回执（delivered/bounce）；
3. 增加重试机制与告警；
4. 模板版本管理与审批流程。

---

## 7. 30 秒汇报话术（可直接读）

“本次我们先满足客户最关心的可追溯能力：每次评估都写入 `evaluation_logs`，并提供历史查询与管理看板。其次在邮件部分提供了轻量 demo：非合规评估可触发通知并记录日志，同时支持前端页面维护通知偏好和模板。当前方案适合演示和验证业务流程，后续可平滑升级到持久化邮件日志和生产级发送链路。” 

---

## 8. 邮件系统 Demo（具体演示脚本）

> 目标：在 5 分钟内向客户展示“可配置、可触发、可追踪”。

### 8.1 演示前准备

1. 启动后端（见第 4.1）。
2. 登录获取管理员 token（`POST /api/v1/auth/login`）。
3. 准备好一个可以触发 Non-Compliant 的评估请求。

建议先确认默认行为：

- `SMTP_SUPPRESS_SEND=true`：只记录日志，不真实发邮件（最稳妥演示模式）。

### 8.2 第一步：展示“可配置”

#### A) 读取当前偏好

```http
GET /api/v1/alerts/email-preferences
Authorization: Bearer <admin_or_manager_token>
```

你可以讲：

- 可以配置阈值、接收人、是否非合规即时通知。

#### B) 修改偏好（现场操作）

```http
PUT /api/v1/alerts/email-preferences
Authorization: Bearer <admin_or_manager_token>
Content-Type: application/json

{
  "sendOnNonCompliant": true,
  "recipientsCsv": "asset.manager@demo.com,safety@demo.com",
  "digestTimeUtc": "09:30",
  "escalationThresholdPercent": 20
}
```

#### C) 修改模板（现场操作）

```http
PUT /api/v1/alerts/email-template
Authorization: Bearer <admin_or_manager_token>
Content-Type: application/json

{
  "subject": "[AssetGuard Demo] {status} - {assetName}",
  "body": "Asset={assetName}\\nStatus={status}\\nOverload={overloadPercent}%"
}
```

你可以讲：

- 邮件主题与正文可由业务方自行调整。

### 8.3 第二步：展示“可触发”

调用一次超载评估（Non-Compliant）：

```http
POST /api/v1/evaluations/check
Authorization: Bearer <token>
Content-Type: application/json

{
  "locationId": 1,
  "assetId": 1,
  "equipment": "Crane with outriggers",
  "equipmentModel": "Demo Crane X1",
  "loadParameterValue": 5000,
  "remark": "demo non-compliant trigger"
}
```

预期：

- 返回 `status = "Non-Compliant"`。
- 后端触发通知逻辑并生成通知日志记录。

### 8.4 第三步：展示“可追踪”

读取邮件日志：

```http
GET /api/v1/alerts/email-logs?limit=20
Authorization: Bearer <admin_or_manager_token>
```

重点展示字段：

- `sentAt`（触发时间）
- `assetName`（关联资产）
- `evaluationStatus`（是否 Non-Compliant）
- `recipient`（发给谁）
- `deliveryStatus`（Delivered/Failed）
- `errorMessage`（失败原因，若有）

你可以讲：

- 即使在 suppress 模式，也能完整保留通知行为轨迹，支持审计回溯。

### 8.5 React 页面演示（可选）

1. 打开 `http://127.0.0.1:5173`。
2. 在页面中填入 token。
3. 点 `Sync Logs`，展示日志表格。
4. 调整偏好和模板并保存，返回后再次触发一条 Non-Compliant，刷新日志。

### 8.6 常见问答（现场应对）

**Q1：现在是真发邮件吗？**  
A：默认不是（`SMTP_SUPPRESS_SEND=true`），这是为了保证演示稳定；切换配置后可真实外发。  

**Q2：日志会不会重启就没？**  
A：当前 demo 是内存存储，重启会清空；生产化会落库到 `email_notifications`。  

**Q3：是否支持失败重试？**  
A：demo 阶段不做复杂重试；生产阶段可加队列与重试策略。  
