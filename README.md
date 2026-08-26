# LoveCards

基于 Flask 的卡片分享平台，支持卡片发布、点赞、评论、标签分类、匿名发布及后台审核管理。

## 技术栈

| 类别 | 技术 |
|------|------|
| 后端框架 | Flask 3.1 |
| ORM | Flask-SQLAlchemy 3.1 + SQLAlchemy 2.0 |
| 数据库 | MySQL (utf8mb4) |
| 数据库迁移 | Flask-Migrate 4.1 (Alembic) |
| 用户认证 | Flask-Login 0.6 |
| 密码加密 | Werkzeug (bcrypt) |
| 表单验证 | WTForms 3.2 |
| 后台管理 | Flask-Admin 2.2 |

## 项目结构

```
LoveCards/
├── app.py                      # Flask 应用入口，注册蓝图、初始化扩展
├── config.py                   # 应用配置（数据库、密钥、Session 等）
├── wsgi.py                     # 生产环境入口（Gunicorn: wsgi:application）
├── model/                      # 数据模型
│   ├── db.py                   # SQLAlchemy 实例
│   ├── User.py                 # 用户模型
│   ├── Card.py                 # 卡片模型
│   ├── Comment.py              # 评论模型
│   ├── Good.py                 # 点赞模型
│   ├── Tags.py                 # 标签模型
│   ├── TagsMap.py              # 标签映射模型
│   ├── Images.py               # 图片模型
│   ├── BanRecord.py            # 封禁记录模型
│   ├── DeletedUser.py          # 已注销用户归档模型
│   └── System.py               # 系统配置模型
├── route/                      # 路由蓝图
│   ├── public.py               # 前台页面路由
│   ├── auth.py                 # 认证路由（登录/注册/登出）
│   ├── admin.py                # 后台管理路由
│   └── api.py                  # RESTful API 路由（/api/v1）
├── templates/                  # Jinja2 模板
│   ├── public/                 # 前台页面模板
│   └── admin/                  # 后台管理模板
├── static/                     # 静态资源（CSS/JS）
├── utils/                      # 工具函数
│   └── upload.py               # 文件上传工具
├── system/                     # 系统模块
├── uploads/                    # 用户上传文件目录（运行时创建）
├── migrate_manager.py          # Flask-Migrate 迁移入口 + 管理员初始化
├── requirements.txt            # Python 依赖
├── API.md                      # API 接口文档
├── .flaskenv                   # Flask 环境变量
└── .gitignore
```

## 数据模型

### users — 用户表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | Integer | PK, 自增 | — | 用户 ID |
| number | String(32) | NOT NULL | — | 系统分配编号 |
| avatar | String(255) | NOT NULL | `''` | 头像 URL |
| email | String(320) | NOT NULL | — | 邮箱（登录凭证） |
| phone | String(20) | NOT NULL | `''` | 手机号 |
| username | String(255) | NOT NULL | — | 用户名 |
| password | String(255) | NOT NULL | — | 密码哈希 |
| status | Integer | NOT NULL | `0` | 状态：0=正常，1=禁用 |
| roles_id | JSON | NOT NULL | `[]` | 角色：[0]=超管，[1]=管理员，[2]=普通用户 |
| created_at | DateTime | NOT NULL | `now` | 创建时间 |
| updated_at | DateTime | NOT NULL | `now` | 更新时间 |
| deleted_at | DateTime | nullable | `NULL` | 软删除时间 |

### cards — 卡片表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | Integer | PK, 自增 | — | 卡片 ID |
| is_top | Integer | NOT NULL | `0` | 置顶：0=否，1=是 |
| status | Integer | NOT NULL | `0` | 状态：0=待审核，1=已通过，2=已拒绝，3=已封禁 |
| user_id | Integer | FK→users.id | `0` | 作者 ID |
| data | JSON | nullable | `NULL` | 扩展数据（如匿名标识） |
| cover | String(2083) | nullable | `NULL` | 封面图 URL |
| content | Text | nullable | `NULL` | 正文内容 |
| tags | JSON | nullable | `NULL` | 标签 ID 列表 |
| good | Integer | NOT NULL | `0` | 点赞数 |
| views | Integer | NOT NULL | `0` | 浏览数 |
| comments | Integer | NOT NULL | `0` | 评论数 |
| post_ip | String(39) | nullable | `NULL` | 发布者 IP |
| created_at | DateTime | NOT NULL | `now` | 创建时间 |
| updated_at | DateTime | NOT NULL | `now` | 更新时间 |
| deleted_at | DateTime | nullable | `NULL` | 软删除时间 |

### comments — 评论表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | Integer | PK, 自增 | — | 评论 ID |
| aid | Integer | NOT NULL | `0` | 应用 ID |
| pid | Integer | NOT NULL | `0` | 条目 ID（如卡片 ID） |
| parent_id | Integer | nullable | `0` | 父评论 ID（嵌套评论） |
| is_top | Integer | NOT NULL | `0` | 置顶 |
| status | Integer | NOT NULL | `0` | 状态：0=待审核，1=已通过 |
| user_id | Integer | FK→users.id | `0` | 评论者 ID |
| data | JSON | nullable | `NULL` | 扩展数据 |
| content | Text | nullable | `NULL` | 评论内容 |
| goods | Integer | NOT NULL | `0` | 点赞数 |
| post_ip | String(39) | nullable | `NULL` | 评论者 IP |
| created_at | DateTime | NOT NULL | `now` | 创建时间 |
| updated_at | DateTime | NOT NULL | `now` | 更新时间 |
| deleted_at | DateTime | nullable | `NULL` | 软删除时间 |

### good — 点赞表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | Integer | PK, 自增 | — | 点赞 ID |
| aid | Integer | NOT NULL | — | 应用 ID（1=卡片，2=评论） |
| pid | Integer | NOT NULL | — | 条目 ID |
| uid | Integer | NOT NULL | — | 点赞用户 ID |
| ip | String(32) | NOT NULL | — | 点赞者 IP |
| created_at | DateTime | NOT NULL | `now` | 点赞时间 |

### tags — 标签表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | Integer | PK, 自增 | — | 标签 ID |
| aid | Integer | NOT NULL | — | 应用 ID |
| user_id | Integer | FK→users.id | `0` | 创建者 ID |
| name | String(255) | nullable | `''` | 标签名称 |
| status | Integer | NOT NULL | `0` | 状态：0=启用，1=禁用 |
| created_at | DateTime | nullable | `now` | 创建时间 |
| updated_at | DateTime | nullable | `now` | 更新时间 |
| deleted_at | DateTime | nullable | `NULL` | 软删除时间 |

### images — 图片表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | Integer | PK, 自增 | — | 图片 ID |
| aid | Integer | NOT NULL | — | 应用 ID |
| pid | Integer | NOT NULL | — | 条目 ID |
| user_id | Integer | FK→users.id | — | 上传者 ID |
| url | String(256) | NOT NULL | — | 图片 URL |
| created_at | DateTime | NOT NULL | `now` | 创建时间 |
| updated_at | DateTime | nullable | `now` | 更新时间 |
| deleted_at | DateTime | nullable | `NULL` | 软删除时间 |

### ban_records — 封禁记录表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | Integer | PK, 自增 | — | 记录 ID |
| user_id | Integer | NOT NULL | — | 被封禁用户 ID |
| username | String(255) | NOT NULL | `''` | 被封禁用户名 |
| reason | String(500) | NOT NULL | `''` | 封禁原因 |
| tags | JSON | NOT NULL | `[]` | 封禁标签 |
| banned_by | Integer | NOT NULL | — | 执行封禁的管理员 ID |
| banned_by_name | String(255) | NOT NULL | `''` | 执行封禁的管理员名 |
| created_at | DateTime | NOT NULL | `now` | 封禁时间 |
| unbanned_at | DateTime | nullable | `NULL` | 解封时间 |

### deleted_users — 已注销用户归档表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | Integer | PK, 自增 | — | 归档 ID |
| original_id | Integer | NOT NULL | — | 原用户 ID |
| number | String(32) | NOT NULL | `''` | 原编号 |
| avatar | String(255) | NOT NULL | `''` | 原头像 |
| email | String(320) | NOT NULL | `''` | 原邮箱 |
| phone | String(20) | NOT NULL | `''` | 原手机号 |
| username | String(255) | NOT NULL | `''` | 原用户名 |
| roles_id | JSON | NOT NULL | `[]` | 原角色 |
| cards_count | Integer | NOT NULL | `0` | 原卡片数 |
| comments_count | Integer | NOT NULL | `0` | 原评论数 |
| goods_count | Integer | NOT NULL | `0` | 原点赞数 |
| delete_scheduled_at | DateTime | NOT NULL | — | 计划删除时间（3天冷静期） |
| created_at | DateTime | NOT NULL | `now` | 归档时间 |

### system — 系统配置表

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| id | Integer | PK, 自增 | — | 配置 ID |
| name | String(255) | nullable | `''` | 配置项名称 |
| value | String(2555) | NOT NULL | `''` | 配置项值 |

## 功能概览

### 前台功能
- 用户注册/登录/登出（邮箱登录）
- 卡片浏览（分页、标签筛选、搜索）
- 卡片发布（支持匿名、多图上传、标签选择）
- 卡片点赞/取消点赞
- 评论发布、评论点赞
- 个人中心（资料编辑、头像上传、密码修改、邮箱/手机修改）
- 账号注销（3天冷静期，可恢复）

### 后台管理
- 仪表盘（统计数据概览）
- 卡片管理（审核/拒绝/封禁/置顶/删除/批量操作）
- 用户管理（禁用/封禁/解封/删除/角色设置）
- 评论管理（删除）
- 标签管理（创建/禁用/删除）
- 封禁记录查看
- 已注销用户管理（恢复/永久删除）
- 系统配置（超级管理员）

### RESTful API
- 完整的 `/api/v1` 接口，支持 JSON 交互
- 详见 [API.md](API.md)

## 快速开始

### 1. 克隆项目

```bash
git clone https://git.imyxj.xyz/Jay/lovecard.git
cd LoveCards
```

### 2. 创建虚拟环境并安装依赖

```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

### 3. 配置数据库

编辑 `config.py`，修改数据库连接信息：

```python
DB_USER = 'your_username'
DB_PASSWORD = 'your_password'
DB_HOST = '127.0.0.1'
DB_PORT = 3306
DB_NAME = 'lovecard'
```

同时修改 `SECRET_KEY` 为安全随机值：

```python
SECRET_KEY = '使用 python -c "import secrets; print(secrets.token_hex(32))" 生成'
```

### 4. 初始化数据库

```bash
flask db init
flask db migrate
flask db upgrade
```

然后创建初始管理员账号：

```bash
python migrate_manager.py
```

默认管理员：用户名 `admin`，密码 `admin`，角色超级管理员。

### 5. 启动应用

**开发环境：**

```bash
flask run --port 8000
```

**生产环境（Gunicorn）：**

```bash
pip install gunicorn
gunicorn -b 0.0.0.0:8000 -w 4 app:app
```

应用默认运行在 `http://127.0.0.1:8000`。

## 文件上传

- 上传目录：`uploads/`（运行时自动创建）
- 支持格式：png, jpg, jpeg, gif, webp, svg
- 最大文件大小：16 MB
- 文件命名规则：`{日期}_{8位随机hex}.{扩展名}`