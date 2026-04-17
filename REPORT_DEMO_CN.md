# AssetGuard AI 汇报提纲（数据库更新 + 工作内容 + 演示脚本）

> 适合你在汇报时直接照着讲，5~10 分钟版本。

---

## 1) 数据库更新了什么

### 核心结论

- **evaluation 数据是持久化保存**的（不是临时内存）。
- 本次 dashboard / history 功能基于现有 `evaluation_logs` 表做查询聚合，**不需要新增表结构迁移**。

### `evaluation_logs` 表关键字段（用于可追踪）

- `asset_id`：关联资产
- `user_id`：谁发起的评估
- `equipment` / `equipment_model`：设备与型号
- `load_parameter_value` / `load_parameter_metric`：输入参数值与单位
- `matched_capacity_name`：匹配到的承载指标
- `status`：`Compliant` / `Non-Compliant`
- `overload_percentage`：超载比例
- `remark`：备注
- `evaluated_at`：评估时间

这套字段满足客户强调的三点：

1. evaluation history  
2. persistent database storage  
3. traceable records

---

## 2) 你做了什么（可直接汇报）

### 后端

1. 新增接口：`GET /api/v1/evaluations/dashboard-summary`
   - 权限：`System_Admin` / `Asset_Manager`
   - 参数：`limit`（1~100）
   - 返回：总评估数、合规/不合规、合规率、超载统计、设备分布、Top 资产、最近评估

2. 保留并强化历史查询：`GET /api/v1/evaluations/history`
   - 用于分页回溯所有评估日志（按时间倒序）

3. 评估写入逻辑确认
   - 每次调用 `POST /api/v1/evaluations/check` 都会写入 `evaluation_logs`，保证审计链完整

### 前端（演示层）

1. 后端内置页面：`/dashboard`
   - 管理员/资产经理登录后可看汇总与最近记录

2. React 邮件模块（独立）
   - `email-notification-react/`
   - 包含：通知偏好、邮件模板、沟通日志表格（适合你负责的 email scope）

---

## 3) 演示脚本（现场一步步操作）

> 推荐用管理员账号：`admin@demo.com / admin123`

### Step A：启动服务

```bash
# Terminal 1: backend
cd "AssetGuard AI"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m flask --app assetguard_app.py db upgrade
python -m flask --app assetguard_app.py seed
python -m flask --app assetguard_app.py run --port 5000
```

（可选）邮件 React 模块：

```bash
cd email-notification-react
npm install
npm run dev
```

### Step B：健康检查

- 打开：`http://127.0.0.1:5000/api/v1/health`
- 预期：返回 `{"status":"ok"}`

### Step C：制造可展示的数据（1 条合规 + 1 条不合规）

1. 登录拿 token：`POST /api/v1/auth/login`
2. 调用两次 `POST /api/v1/evaluations/check`
   - 一次低于阈值（Compliant）
   - 一次高于阈值（Non-Compliant）

### Step D：展示“可追溯历史”

- 打开（或用 Postman）：
  - `GET /api/v1/evaluations/history?page=1&pageSize=20`
- 重点讲：
  - 能看到谁、何时、对哪个资产、用什么参数做了评估
  - 日志是持续累积的，不会丢失

### Step E：展示“管理看板”

- 打开：`http://127.0.0.1:5000/dashboard`
- 重点讲：
  - 总评估数、合规率、超载统计
  - 最近评估列表可快速回溯

### Step F（你负责的 email 部分）

- 打开 React 页面（通常 `http://127.0.0.1:5173`）
- 演示：
  - 修改通知偏好
  - 修改邮件模板
  - 查看沟通日志（mock 或后端同步）

---

## 4) 汇报话术（30 秒版本）

“本次重点不是复杂邮件流程，而是先满足客户最关心的评估可追溯能力。我们已经把每次评估完整落库到 `evaluation_logs`，并提供了历史查询与管理看板。管理角色可以按时间回溯每条记录，看到设备、参数、结果和时间。邮件模块方面，我已经准备了 React 的独立页面，支持通知偏好、模板和沟通日志，后续可继续接后端发送链路。” 

