# LoveCards 后端 API 接口文档

> 基础地址：`http://localhost:8000`

---

## 目录

- [1. 公共页面](#1-公共页面)
- [2. 认证模块](#2-认证模块)
  - [2.1 用户登录](#21-用户登录)
  - [2.2 用户注册](#22-用户注册)
- [3. 后台管理模块](#3-后台管理模块)
  - [3.1 管理员登录页](#31-管理员登录页)
  - [3.2 用户列表（分页）](#32-用户列表分页)
- [4. 数据模型](#4-数据模型)
  - [4.1 User 用户表](#41-user-用户表)
  - [4.2 Card 卡片表](#42-card-卡片表)
  - [4.3 Comment 评论表](#43-comment-评论表)
- [5. 通用响应格式](#5-通用响应格式)

---

## 1. 公共页面

| 方法 | 路径 | 说明 | 返回类型 |
|------|------|------|----------|
| GET | `/` | 首页 | HTML |
| GET | `/about` | 关于页面 | HTML |
| GET | `/terms` | 服务条款页面 | HTML |
| GET | `/privacy` | 隐私政策页面 | HTML |

---

## 2. 认证模块

### 2.1 用户登录

| 属性 | 值 |
|------|-----|
| **URL** | `/login` |
| **方法** | `GET` / `POST` |

#### GET - 获取登录页面

- **返回**：登录页面 HTML

#### POST - 提交登录

- **Content-Type**：`application/x-www-form-urlencoded`

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `username` | string | 是 | 用户名 |
| `password` | string | 是 | 密码（至少 6 位） |

**成功响应：**

```json
{
  "success": true,
  "message": "登录成功"
}
```

**失败响应：**

```json
{
  "success": false,
  "message": "用户名或密码错误"
}
```

---

### 2.2 用户注册

| 属性 | 值 |
|------|-----|
| **URL** | `/register` |
| **方法** | `GET` / `POST` |

#### GET - 获取注册页面

- **返回**：注册页面 HTML

#### POST - 提交注册

- **Content-Type**：`application/x-www-form-urlencoded`

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `username` | string | 是 | 用户名（3-20 个字符） |
| `email` | string | 是 | 邮箱地址 |
| `password` | string | 是 | 密码（至少 6 位） |

**成功响应：**

```json
{
  "success": true,
  "message": "注册成功，3 秒后跳转到登录页"
}
```

**失败响应：**

```json
{
  "success": false,
  "message": "用户名已存在"
}
```

---

## 3. 后台管理模块

> 所有后台接口前缀：`/admin`

### 3.1 管理员登录页

| 属性 | 值 |
|------|-----|
| **URL** | `/admin/` |
| **方法** | `GET` / `POST` |

#### GET - 获取管理员登录页面

- **返回**：管理员登录页面 HTML

#### POST - 管理员登录

- **Content-Type**：`application/x-www-form-urlencoded`

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `username` | string | 是 | 管理员用户名 |
| `password` | string | 是 | 管理员密码 |

- **返回**：管理员登录页面 HTML

---

### 3.2 用户列表（分页）

| 属性 | 值 |
|------|-----|
| **URL** | `/admin/users` 或 `/admin/users/<page>` |
| **方法** | `GET` |

**路径参数：**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `page` | int | 否 | 1 | 页码，从 1 开始 |

**固定配置：** 每页 10 条记录（`PER_PAGE = 10`）

**返回**：用户列表页面 HTML，包含以下模板变量：

| 变量 | 类型 | 说明 |
|------|------|------|
| `users` | list[User] | 当前页的用户对象列表 |
| `pagination` | Pagination | SQLAlchemy 分页对象 |
| `page` | int | 当前页码 |
| `per_page` | int | 每页条数 |

**pagination 对象属性：**

| 属性 | 类型 | 说明 |
|------|------|------|
| `total` | int | 总记录数 |
| `pages` | int | 总页数 |
| `has_prev` | bool | 是否有上一页 |
| `has_next` | bool | 是否有下一页 |
| `prev_num` | int | 上一页页码 |
| `next_num` | int | 下一页页码 |

**访问示例：**

```
/admin/users       → 第 1 页
/admin/users/2     → 第 2 页
/admin/users/5     → 第 5 页
```

---

## 4. 数据模型

### 4.1 User 用户表

**表名：** `user`

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | Integer | 主键, 自增 | — | 用户ID |
| `username` | String(80) | 唯一, NOT NULL | — | 用户名 |
| `email` | String(120) | 唯一 | — | 邮箱 |
| `password` | String(80) | 唯一, NOT NULL | — | 密码 |
| `is_admin` | Boolean | NOT NULL | `False` | 是否为管理员 |
| `is_active` | Boolean | NOT NULL | `True` | 账号是否激活 |
| `create_time` | DateTime | NOT NULL | `datetime.now` | 创建时间 |
| `server_time` | DateTime | NOT NULL | `datetime.now` | 服务器记录时间 |
| `update_time` | DateTime | NOT NULL | `datetime.now` | 更新时间 |
| `delete_time` | DateTime | NOT NULL | `datetime.now` | 删除时间（软删除） |

---

### 4.2 Card 卡片表

**表名：** `card`

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | Integer | 主键 | — | 卡片ID |
| `title` | String(50) | NOT NULL | — | 卡片标题 |
| `content` | String(200) | NOT NULL | — | 卡片内容 |
| `author_id` | Integer | 外键 → `user.id` | — | 作者ID |
| `server_time` | DateTime | NOT NULL | `datetime.now` | 服务器记录时间 |
| `create_time` | DateTime | NOT NULL | `datetime.now` | 创建时间 |
| `delete_time` | DateTime | NOT NULL | `datetime.now` | 删除时间（软删除） |
| `like_count` | Integer | NOT NULL | `0` | 点赞数 |
| `commnet_count` | Integer | NOT NULL | `0` | 评论数 |
| `coument_id` | Integer | NOT NULL | `0` | 评论关联ID |
| `statue` | Boolean | NOT NULL | `False` | 审核状态 |
| `is_top` | Boolean | NOT NULL | `False` | 是否置顶 |

---

### 4.3 Comment 评论表

**表名：** `comment`

| 字段 | 类型 | 约束 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | Integer | 主键 | — | 评论ID |
| `content` | String(200) | — | — | 评论内容 |
| `user_id` | Integer | 外键 → `user.id` | — | 评论者ID |
| `card_id` | Integer | 外键 → `card.id` | — | 所属卡片ID |
| `server_time` | DateTime | NOT NULL | `datetime.now` | 服务器记录时间 |
| `comment_time` | DateTime | NOT NULL | `datetime.now` | 评论发布时间 |

---

## 5. 通用响应格式

所有 JSON 接口统一使用以下格式：

### 成功响应

```json
{
  "success": true,
  "message": "操作成功描述"
}
```

### 失败响应

```json
{
  "success": false,
  "message": "错误原因描述"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | bool | 操作是否成功 |
| `message` | string | 提示信息，成功时为操作结果，失败时为错误原因 |