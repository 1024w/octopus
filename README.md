# Octopus - 加密货币情绪监控系统

Octopus是一个加密货币情绪监控系统，用于收集、处理和分析社交媒体上关于加密货币的讨论，提供趋势分析和警报功能。

## 系统架构

系统由以下几个主要部分组成：

1. **收集器（Collectors）** - 从各种社交媒体平台（如Twitter、Telegram、Reddit、Discord）收集数据
2. **处理器（Processors）** - 处理收集到的数据，提取代币提及和情绪
3. **服务（Services）** - 提供核心业务逻辑，如代币管理、趋势分析和警报
4. **API** - 提供RESTful API接口，供前端应用使用
5. **任务（Tasks）** - 后台定时任务，用于数据收集和处理

## API接口文档

### 代币API

- `GET /api/v1/token/tokens` - 获取代币列表
- `GET /api/v1/token/tokens/<token_id>` - 获取代币详情
- `POST /api/v1/token/tokens` - 创建新代币
- `PUT /api/v1/token/tokens/<token_id>` - 更新代币
- `DELETE /api/v1/token/tokens/<token_id>` - 删除代币
- `GET /api/v1/token/tokens/search` - 搜索代币
- `GET /api/v1/token/tokens/<token_id>/sentiment` - 获取代币情绪分析
- `GET /api/v1/token/tokens/<token_id>/trends` - 获取代币趋势分析
- `GET /api/v1/token/tokens/<token_id>/correlation` - 获取代币相关性分析
- `GET /api/v1/token/tokens/trending` - 获取热门代币
- `GET /api/v1/token/tokens/sentiment/top` - 获取情绪最积极的代币

### 收集器API

- `GET /api/v1/collector/collectors` - 获取收集器列表
- `GET /api/v1/collector/collectors/<collector_id>` - 获取收集器详情
- `POST /api/v1/collector/collectors` - 创建新收集器
- `PUT /api/v1/collector/collectors/<collector_id>` - 更新收集器
- `DELETE /api/v1/collector/collectors/<collector_id>` - 删除收集器
- `POST /api/v1/collector/collectors/<collector_id>/run` - 手动运行收集器
- `GET /api/v1/collector/collectors/tasks/<task_id>` - 获取任务状态
- `GET /api/v1/collector/collectors/types` - 获取支持的收集器类型

### 处理器API

- `GET /api/v1/processor/processors/types` - 获取支持的处理器类型
- `POST /api/v1/processor/processors/message/process` - 处理单条消息
- `POST /api/v1/processor/processors/message/batch` - 批量处理消息
- `POST /api/v1/processor/processors/message/unprocessed` - 处理未处理的消息
- `POST /api/v1/processor/processors/message/collector/<collector_id>` - 处理特定收集器的消息

### 消息API

- `GET /api/v1/message/messages` - 获取消息列表
- `GET /api/v1/message/messages/<message_id>` - 获取消息详情
- `GET /api/v1/message/messages/<message_id>/mentions` - 获取消息中的代币提及
- `GET /api/v1/message/messages/search` - 搜索消息
- `GET /api/v1/message/messages/stats` - 获取消息统计数据
- `GET /api/v1/message/messages/platforms` - 获取所有消息平台

### 趋势API

- `GET /api/v1/trend/trends/mentions` - 获取提及趋势
- `GET /api/v1/trend/trends/tokens/trending` - 获取热门代币
- `GET /api/v1/trend/trends/platforms/activity` - 获取平台活动数据
- `GET /api/v1/trend/trends/correlation` - 获取相关性分析
- `GET /api/v1/trend/trends/overview` - 获取趋势概览

### 警报API

- `GET /api/v1/alert/alerts` - 获取警报列表
- `GET /api/v1/alert/alerts/<alert_id>` - 获取警报详情
- `POST /api/v1/alert/alerts` - 创建新警报
- `PUT /api/v1/alert/alerts/<alert_id>` - 更新警报
- `DELETE /api/v1/alert/alerts/<alert_id>` - 删除警报
- `POST /api/v1/alert/alerts/check` - 手动检查警报

### 用户API

- `POST /api/v1/user/users/register` - 用户注册
- `POST /api/v1/user/users/login` - 用户登录
- `GET /api/v1/user/users/profile` - 获取用户个人资料
- `PUT /api/v1/user/users/profile` - 更新用户个人资料
- `POST /api/v1/user/users/change-password` - 修改密码
- `GET /api/v1/user/users` - 获取用户列表（仅管理员）

## 运行项目

### 环境要求

- Python 3.8+
- Redis（用于Celery）
- PostgreSQL（或其他数据库）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

创建`.env`文件，设置必要的环境变量：

```
FLASK_APP=wsgi.py
FLASK_ENV=development
DATABASE_URL=postgresql://user:password@localhost/octopus
SECRET_KEY=your-secret-key
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 初始化数据库

```bash
flask db upgrade
```

### 运行应用

```bash
flask run
```

### 运行Celery Worker

```bash
celery -A app.tasks.celery worker --loglevel=info
```

### 运行Celery Beat（定时任务）

```bash
celery -A app.tasks.celery beat --loglevel=info
```

## 贡献

欢迎提交Pull Request或Issue。

## 许可证

MIT 