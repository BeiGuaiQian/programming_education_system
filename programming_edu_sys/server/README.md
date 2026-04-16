# Server Backend

这个目录是当前规范化后的后端项目结构，提供：

- 多用户注册 / 登录
- SQLite 持久化用户、会话、聊天记录
- Access Token + Refresh Token
- 浏览器登录页和聊天页
- 学习中心页面（权威教材来源 + 知识点 + 习题 + 小型 IDE + 提交判题）
- 登录后访问编程教育智能体

## 目录结构

- `app.py`：FastAPI 主应用
- `run_server.py`：启动入口
- `store.py`：SQLite 存储层
- `static/index.html`：登录 / 注册页
- `static/chat.html`：对话页，带聊天记录列表
- `static/learn.html`：学习中心页
- `static/profile.html`：个人中心页，展示资料、学习水平、进度和智能推荐
- `static/questions.html`：题库大全页，展示推荐题、筛选题库和生成小测
- `static/question_detail.html`：单题做题页，包含题面、独立 IDE 和提交判题
- `runtime/app.db`：运行时数据库

## 启动

```bash
cd programming_edu_sys
pip install -r requirements.txt
python server/run_server.py
```

访问：

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/learn`（登录后）
- `http://127.0.0.1:8000/profile`（登录后）
- `http://127.0.0.1:8000/questions`（登录后）

## 环境变量

项目根目录 `.env` 示例：

```env
SERVER_ADMIN_USERNAME=admin
SERVER_ADMIN_PASSWORD=change_me_please
SERVER_TOKEN_EXPIRE_MINUTES=120
SERVER_REFRESH_TOKEN_EXPIRE_DAYS=14
SERVER_APP_DB=./server/runtime/app.db
```

## 主要接口

### 注册

`POST /auth/register`

### 登录

`POST /auth/login`

返回：

- `access_token`
- `refresh_token`

### 刷新登录状态

`POST /auth/refresh`

### 当前用户

`GET /auth/me`

### 退出登录

`POST /auth/logout`

### 会话列表

`GET /chat/conversations`

### 单个会话消息

`GET /chat/conversations/{conversation_id}`

### 智能体请求

`POST /agent/request`

支持：

- `request_type`
- `content`
- `conversation_id`

如果不传 `conversation_id`，系统会自动新建对话。

### 学习中心知识点列表

`GET /learning/lessons`

### 学习中心知识点详情

`GET /learning/lessons/{lesson_id}`

### 学习中心提交判题

`POST /learning/submit`

### 学习中心划词提问

`POST /learning/ask-selection`

登录后在学习中心页面选中文本，可以直接请求智能体解释该文本。请求体包含：

- `lesson_id`：当前知识点 ID
- `selected_text`：用户选中的文本
- `question`：可选，用户补充的具体问题
- `surrounding_context`：可选，选中文本附近的页面上下文

当前首个示例知识点：

- `python-functions-basics`（教材来源：Python 官方教程 Defining Functions）

### 个人中心总览

`GET /profile/overview`

返回用户资料、学习水平、统计数据、知识点进度、最近练习和智能推荐。

### 修改个人资料

`PATCH /profile`

支持修改：

- `nickname`
- `avatar_url`
- `bio`

### 题库大全总览

`GET /question-bank/overview`

返回题库统计、用户当前推荐难度、优先学习主题和推荐题目。

### 题库筛选

`GET /question-bank/questions`

支持查询参数：

- `topic`
- `difficulty`
- `question_type`
- `keyword`

### 单题详情

`GET /question-bank/questions/{question_id}`

返回题目详情和当前用户最近一次提交。

页面访问：

`GET /questions/{question_id}`

### 单题提交判题

`POST /question-bank/questions/{question_id}/submit`

请求体：

- `code`

返回隐藏测试结果、得分和判题反馈。

### 生成个性化小测

`POST /question-bank/quiz`

根据用户进度、当前水平和需求描述生成小测。请求体包含：

- `topic`
- `difficulty`
- `count`
- `requirement`

## 兼容说明

旧的 `sever/` 目录保留为兼容入口，新的开发和运行请统一使用 `server/`。
