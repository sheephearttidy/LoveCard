# LoveCards

Flask 卡片墙/表白墙平台，支持内容审核、通知推送、审计日志等企业级功能。

## 快速开始

需要 Python 3.10+ 和 MySQL。

```bash
git clone https://github.com/sheephearttidy/LoveCard.git
cd LoveCards
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux
source .venv/bin/activate
pip install -r requirements.txt
```

### 环境变量

所有配置走环境变量。开发环境设 `FLASK_ENV=development` 即可用默认值运行。

生产环境必须设置：

```bash
export SECRET_KEY="$(python -c 'import secrets;print(secrets.token_hex(32))')"
export DB_USER=lovecard
export DB_PASSWORD=你的密码
export DB_HOST=127.0.0.1
export DB_PORT=3306
export DB_NAME=lovecard
```

也可写 `.env` 文件（已 gitignore），参考 `.env.example`。

### 初始化

```bash
python db_init.py reset   # 建表 + 种子数据
```

初始管理员 admin/admin，上线后务必修改密码。

### 启动

```bash
# 开发
flask run --port 8000

# 生产
gunicorn -c gunicorn.conf.py wsgi:app
```

宝塔面板用 `wsgi:app`。

## 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| SECRET_KEY | 是 | dev-secret-key... | 会话签名密钥 |
| DB_USER | 是 | lovecard | 数据库用户名 |
| DB_PASSWORD | 是 | lovecard | 数据库密码 |
| DB_HOST | | 127.0.0.1 | 数据库地址 |
| DB_PORT | | 3306 | 数据库端口 |
| DB_NAME | 是 | lovecard | 数据库名 |
| DB_DRIVER | | mysqldb | 数据库驱动 |

## 功能概览

### 前台

- 注册登录（支持用户名/邮箱登录、验证码、邀请码、注册审核）
- 忘记密码（邮箱重置链接，1小时有效）
- 发布卡片（匿名/多图/标签/封面）
- 点赞（卡片+评论）
- 评论（支持审核）
- 个人中心（资料编辑、密码修改、邮箱/手机变更、账号注销 3天冷静期）
- 通知系统（审核结果、新评论等实时通知，未读计数）
- 封禁公示

### 后台

- 仪表盘（统计数据概览、待审核待办）
- 卡片管理（审核/封禁/置顶/批量操作）
- 用户管理（封禁/解封/角色设置/注册审核）
- 评论管理（审核/删除/批量操作）
- 标签管理
- 邀请码管理（生成/启停/删除）
- 封禁记录
- 已注销用户（恢复/永久删除）
- 审计日志（记录所有管理员操作）
- 站点配置（基本设置/页脚备案/功能开关/邮件服务）

### 安全

- CSRF 防护（所有 POST 请求校验令牌）
- 登录频率限制（基于 IP，5次/5分钟前台，10次/5分钟 API）
- 密码哈希存储（Werkzeug PBKDF2）
- 内容审核（卡片/评论/注册均支持审核机制）
- 审计日志（记录操作人、操作类型、目标、IP、时间）

### API

`/api/v1` 完整 RESTful 接口，详见 [API.md](API.md)

## 项目结构

```
├── app.py              # 应用入口，蓝图注册 + CSRF + 扩展初始化
├── config.py           # 配置，环境变量驱动
├── wsgi.py             # 生产入口
├── db_init.py          # 建表/种子/重置
├── gunicorn.conf.py    # gunicorn 配置
├── model/              # ORM 模型
│   ├── db.py           # SQLAlchemy 实例
│   ├── User.py         # 用户（角色/认证/软删除）
│   ├── Card.py         # 卡片（审核/置顶/匿名）
│   ├── Comment.py      # 评论（嵌套/审核）
│   ├── Good.py         # 点赞（多应用/唯一约束）
│   ├── Tags.py         # 标签
│   ├── TagsMap.py      # 标签映射
│   ├── Images.py       # 图片
│   ├── BanRecord.py    # 封禁记录
│   ├── DeletedUser.py  # 注销归档（冷静期）
│   ├── InviteCode.py   # 邀请码
│   ├── Notification.py # 通知
│   ├── AuditLog.py     # 审计日志
│   └── System.py       # 键值对配置
├── route/
│   ├── public.py       # 前台页面
│   ├── auth.py         # 登录/注册/忘记密码
│   ├── admin.py        # 后台管理
│   └── api.py          # /api/v1
├── templates/          # Jinja2 模板
├── static/             # CSS/JS
├── utils/
│   ├── upload.py       # 文件上传
│   ├── system.py       # 站点配置读写
│   ├── notification.py # 通知推送
│   ├── audit.py        # 审计日志记录
│   ├── rate_limit.py   # 登录频率限制
│   ├── email.py        # 邮件发送
│   └── captcha.py      # SVG 验证码
└── uploads/            # 上传目录，运行时创建
```

## 数据表

### users

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | |
| number | String(32) | 1000000000+id |
| avatar | String(255) | 头像 URL |
| email | String(320) UNIQUE | 登录用邮箱 |
| phone | String(20) | 手机号 |
| username | String(255) UNIQUE | 用户名 |
| nickname | String(255) | 昵称/显示名 |
| password | String(255) | PBKDF2 哈希 |
| status | Integer | 0正常 1禁用 2待审核 |
| roles_id | JSON | [0]超管 [1]管理员 [2]用户 |
| created_at / updated_at / deleted_at | DateTime | 软删除 |

### cards

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | |
| is_top | Integer | 置顶 |
| status | Integer | 0待审核 1通过 2拒绝 3封禁 |
| user_id | FK→users | |
| data | JSON | anonymous=true 为匿名 |
| cover | String(2083) | 封面图 |
| content | Text | 正文 |
| tags | JSON | 标签ID列表 |
| good / views / comments | Integer | 冗余计数 |
| post_ip | String(39) | |
| created_at / updated_at / deleted_at | DateTime | |

### comments

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | |
| aid / pid | Integer | 应用ID/条目ID |
| parent_id | Integer | 嵌套评论 |
| status | Integer | 0待审核 1通过 |
| user_id | FK→users | |
| content | Text | |
| goods | Integer | 点赞数 |
| post_ip | String(39) | |
| created_at / updated_at / deleted_at | DateTime | |

### good

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | |
| aid / pid / uid | Integer | UNIQUE(aid,pid,uid) |
| ip | String(32) | |
| created_at | DateTime | |

aid=1 卡片，aid=2 评论。

### notifications

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | |
| user_id | FK→users | 接收用户 |
| type | String(50) | 通知类型 |
| title | String(255) | 标题 |
| content | String(1000) | 内容 |
| data | JSON | 附加数据 |
| is_read | Integer | 0未读 1已读 |
| created_at | DateTime | |

### audit_logs

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | |
| user_id | Integer | 操作人ID |
| username | String(255) | 操作人用户名 |
| action | String(100) | 操作类型 |
| target_type | String(50) | 目标类型 |
| target_id | Integer | 目标ID |
| detail | String(500) | 详情 |
| ip | String(39) | 操作IP |
| created_at | DateTime | |

### invite_codes

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | |
| code | String(32) UNIQUE | 邀请码 |
| created_by | Integer | 创建人 |
| max_uses | Integer | 最大使用次数，0=无限 |
| used_count | Integer | 已使用次数 |
| expires_at | DateTime | 过期时间 |
| status | Integer | 0启用 1禁用 |
| created_at | DateTime | |

### ban_records / deleted_users / tags / images / system

详见源码 `model/` 目录。

## db_init.py

```bash
python db_init.py create     # 建表
python db_init.py drop       # 删表
python db_init.py recreate   # 删了重建
python db_init.py seed       # 种子数据
python db_init.py reset      # drop + create + seed
```

## 上传

- 目录 `uploads/`，运行时自动创建
- 格式：png/jpg/jpeg/gif/webp/svg
- 大小：16MB
- 命名：`{日期}_{8位hex}.{ext}`

## 通知类型

| type | 说明 | 接收者 |
|------|------|--------|
| card_approved | 卡片审核通过 | 作者 |
| card_rejected | 卡片审核拒绝 | 作者 |
| card_banned | 卡片被封禁 | 作者 |
| comment_approved | 评论审核通过 | 评论者 |
| comment_rejected | 评论审核拒绝 | 评论者 |
| comment_banned | 评论被封禁 | 评论者 |
| new_comment | 新评论通知 | 卡片作者 |
| card_pending | 新卡片待审核 | 管理员 |
| comment_pending | 新评论待审核 | 管理员 |
| user_pending | 新用户待审核 | 管理员 |

## 审计日志操作类型

| action | 说明 |
|--------|------|
| card_approve / card_reject / card_ban / card_unban | 卡片审核 |
| card_delete / card_toggle_top | 卡片管理 |
| cards_batch | 卡片批量操作 |
| comment_unban / comment_delete / comments_batch | 评论管理 |
| user_ban / user_unban / user_toggle_status | 用户管理 |
| user_set_role | 角色设置 |
| pending_user_approve / pending_user_reject / pending_users_batch | 注册审核 |
| tag_create / tag_delete / tag_toggle_status | 标签管理 |
| invite_codes_generate / invite_code_toggle / invite_code_delete | 邀请码管理 |
| cards_ban_user | 封禁用户所有卡片 |
| settings_update | 系统配置修改 |

## 许可证

MIT License