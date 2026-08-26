# LoveCards

一个基于 Flask 的卡片分享平台，用户可以创建、浏览、点赞和评论卡片内容。

## 技术栈

- **后端框架**: Flask 3.1
- **ORM**: Flask-SQLAlchemy 3.1 + SQLAlchemy 2.0
- **数据库**: MySQL
- **数据库迁移**: Flask-Migrate 4.1 (Alembic)
- **表单**: WTForms 3.2
- **认证**: Flask-Login 0.6
- **后台管理**: Flask-Admin 2.2

## 项目结构

```
LoveCards/
├── app/
│   ├── app.py              # Flask 应用入口
│   ├── config.py           # 应用配置
│   ├── model/              # 数据模型
│   │   ├── db.py           # 数据库初始化
│   │   ├── User.py         # 用户模型
│   │   ├── Card.py         # 卡片模型
│   │   └── Comment.py      # 评论模型
│   ├── route/              # 路由蓝图
│   │   ├── public.py       # 公开页面路由
│   │   ├── auth.py         # 认证路由（登录/注册）
│   │   └── admin.py        # 管理后台路由
│   ├── templates/          # Jinja2 模板
│   │   ├── public/         # 公开页面模板
│   │   └── admin/          # 管理后台模板
│   └── static/             # 静态资源
│       ├── css/
│       └── js/
├── migrate_manager.py      # Flask-Migrate 迁移入口
├── requirements.txt        # Python 依赖
├── .flaskenv               # Flask 环境变量
└── .gitignore
```

## 数据模型

### User（用户）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键，自增 |
| username | String(80) | 用户名，唯一 |
| email | String(120) | 邮箱，唯一 |
| password | String(80) | 密码 |
| is_admin | Boolean | 是否管理员 |
| is_active | Boolean | 账号是否激活 |
| create_time | DateTime | 创建时间 |
| delete_time | DateTime | 删除时间（软删除） |

### Card（卡片）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| title | String(50) | 卡片标题 |
| content | String(200) | 卡片内容 |
| author_id | Integer | 作者 ID（外键 → User） |
| like_count | Integer | 点赞数 |
| commnet_count | Integer | 评论数 |
| statue | Boolean | 审核状态 |
| is_top | Boolean | 是否置顶 |

### Comment（评论）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| content | String(200) | 评论内容 |
| user_id | Integer | 评论者 ID（外键 → User） |
| card_id | Integer | 所属卡片 ID（外键 → Card） |
| comment_time | DateTime | 评论发布时间 |

## 路由说明

| 路由 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 首页 |
| `/about` | GET | 关于页面 |
| `/terms` | GET | 服务条款 |
| `/privacy` | GET | 隐私政策 |
| `/login` | GET/POST | 用户登录 |
| `/register` | GET/POST | 用户注册 |
| `/admin/` | GET/POST | 管理后台首页 |
| `/admin/users` | GET | 用户管理 |

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
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

编辑 `app/config.py`，修改数据库连接信息：

```python
DB_USER = 'your_username'
DB_PASSWORD = 'your_password'
DB_HOST = '127.0.0.1'
DB_PORT = 3306
DB_NAME = 'lovecards'
```

### 4. 初始化数据库

```bash
flask db init
flask db migrate
flask db upgrade
```

### 5. 启动应用

```bash
flask run
```

应用默认运行在 `http://127.0.0.1:8000`。