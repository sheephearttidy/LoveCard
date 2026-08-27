# LoveCards

Flask 写的表白墙/卡片分享平台。

## 部署

需要 Python 3.10+ 和 MySQL。

```bash
git clone https://git.imyxj.xyz/Jay/lovecard.git
cd LoveCards
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux
source .venv/bin/activate
pip install -r requirements.txt
```

### 配置

所有配置走环境变量，别改 config.py。开发环境设 `FLASK_ENV=development` 就能用默认值直接跑起来。

生产环境必须设这些，不然启动直接报错：

```bash
export SECRET_KEY="$(python -c 'import secrets;print(secrets.token_hex(32))')"
export DB_USER=lovecard
export DB_PASSWORD=你的密码
export DB_HOST=127.0.0.1
export DB_PORT=3306
export DB_NAME=lovecard
```

也可以写 `.env` 文件（已 gitignore）。

### 初始化

```bash
python db_init.py reset   # 建表 + 种子数据，一步到位
```

或者用 Flask-Migrate：

```bash
flask db init && flask db migrate && flask db upgrade
python migrate_manager.py  # 创建管理员
```

初始管理员 admin/admin，上线记得改密码。

### 启动

```bash
# 开发
flask run --port 8000

# 生产
gunicorn -c gunicorn.conf.py wsgi:app
```

宝塔面板用 `wsgi:app`。

## 环境变量

| 变量 | 生产必填 | 默认值 | 说明 |
|------|---------|--------|------|
| SECRET_KEY | 是 | dev-secret-key... | 会话签名 |
| DB_USER | 是 | lovecard | |
| DB_PASSWORD | 是 | lovecard | |
| DB_HOST | | 127.0.0.1 | |
| DB_PORT | | 3306 | |
| DB_NAME | 是 | lovecard | |
| DB_DRIVER | | mysqldb | |
| FLASK_ENV | | | development 启用默认值 |

## 功能

**前台**：注册登录、发卡片（支持匿名/多图/标签）、点赞、评论、个人中心、账号注销（3天冷静期）

**后台**：仪表盘、卡片审核/批量操作、用户封禁/角色管理、评论管理、标签管理、站点配置

**API**：`/api/v1` 完整接口，见 [API.md](API.md)

## 项目结构

```
├── app.py              # 入口，蓝图注册 + CSRF + 扩展初始化
├── config.py           # 配置，环境变量驱动
├── wsgi.py             # 生产入口 wsgi:app
├── db_init.py          # 建表/种子/重置
├── gunicorn.conf.py    # gunicorn 配置
├── migrate_manager.py  # flask-migrate + 管理员种子
├── model/              # ORM 模型
│   ├── db.py           # SQLAlchemy 实例
│   ├── User.py
│   ├── Card.py
│   ├── Comment.py
│   ├── Good.py
│   ├── Tags.py / TagsMap.py
│   ├── Images.py
│   ├── BanRecord.py
│   ├── DeletedUser.py
│   └── System.py       # 键值对配置
├── route/
│   ├── public.py       # 前台页面
│   ├── auth.py         # 登录注册
│   ├── admin.py        # 后台管理
│   └── api.py          # /api/v1
├── templates/          # Jinja2
├── static/             # CSS/JS
├── utils/
│   ├── upload.py       # 上传工具
│   └── system.py       # 站点配置读写
└── uploads/            # 上传目录，运行时创建
```

## 数据表

### users

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | |
| number | String(32) | 1000000000+id |
| avatar | String(255) | |
| email | String(320) UNIQUE | 登录用 |
| phone | String(20) | |
| username | String(255) UNIQUE | |
| password | String(255) | scrypt 哈希 |
| status | Integer | 0正常 1禁用 |
| roles_id | JSON | [0]超管 [1]管理员 [2]用户 |
| created_at / updated_at / deleted_at | DateTime | deleted_at 软删除 |

### cards

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | |
| is_top | Integer | 置顶 |
| status | Integer | 0待审核 1通过 2拒绝 3封禁 |
| user_id | FK→users | |
| data | JSON | 扩展数据，anonymous=true 为匿名 |
| cover | String(2083) | 封面图 |
| content | Text | |
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
| goods | Integer | |
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

### tags

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | |
| aid | Integer | 应用ID |
| user_id | FK→users | |
| name | String(255) | |
| status | Integer | 0启用 1禁用 |
| created_at / updated_at / deleted_at | DateTime | |

### images

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | |
| aid / pid | Integer | |
| user_id | FK→users | |
| url | String(256) | |
| created_at / updated_at / deleted_at | DateTime | |

### ban_records

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | |
| user_id | Integer | 被封禁用户 |
| username | String(255) | |
| reason | String(500) | |
| tags | JSON | |
| banned_by / banned_by_name | | 执行封禁的管理员 |
| created_at | DateTime | 封禁时间 |
| unbanned_at | DateTime | 解封时间，null=未解封 |

### deleted_users

用户注销后的归档，配合3天冷静期。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | |
| original_id | Integer | 原用户ID |
| number / avatar / email / phone / username / roles_id | | 原用户信息快照 |
| cards_count / comments_count / goods_count | Integer | 统计快照 |
| delete_scheduled_at | DateTime | 计划删除时间 |
| created_at | DateTime | 归档时间 |

### system

键值对配置，name UNIQUE。

内置项：siteName, siteSubTitle, siteDesc, siteUrl, siteIcp, siteFooter, siteKeyword, siteAllowRegister, siteAllowPublish, siteCardNeedReview, siteCommentNeedReview

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