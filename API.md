# LoveCards API 接口文档

> 基础地址：`/api/v1`
>
> 所有接口统一返回 JSON，结构为 `{"code": int, "message": string, "data": object}`

---

## 目录

- [1. 认证模块](#1-认证模块)
  - [1.1 用户注册](#11-用户注册)
  - [1.2 用户登录](#12-用户登录)
  - [1.3 用户登出](#13-用户登出)
  - [1.4 获取当前用户信息](#14-获取当前用户信息)
- [2. 用户模块](#2-用户模块)
  - [2.1 修改个人资料](#21-修改个人资料)
  - [2.2 修改密码](#22-修改密码)
  - [2.3 上传头像](#23-上传头像)
- [3. 卡片模块](#3-卡片模块)
  - [3.1 获取卡片列表](#31-获取卡片列表)
  - [3.2 获取卡片详情](#32-获取卡片详情)
  - [3.3 发布卡片](#33-发布卡片)
  - [3.4 点赞/取消点赞](#34-点赞取消点赞)
  - [3.5 发表评论](#35-发表评论)
- [4. 标签模块](#4-标签模块)
  - [4.1 获取标签列表](#41-获取标签列表)
- [5. 通用模块](#5-通用模块)
  - [5.1 通用文件上传](#51-通用文件上传)
- [6. 前台页面路由](#6-前台页面路由)
- [7. 后台管理路由](#7-后台管理路由)
- [8. 通用响应格式](#8-通用响应格式)

---

## 1. 认证模块

### 1.1 用户注册

| 属性 | 值 |
|------|-----|
| **URL** | `/api/v1/auth/register` |
| **方法** | `POST` |
| **认证** | 无 |

**请求头：**

```
Content-Type: application/json
```

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `username` | string | 是 | 用户名（3-20位，字母/数字/下划线/中文） |
| `email` | string | 是 | 邮箱地址 |
| `password` | string | 是 | 密码（至少 6 位） |
| `captcha` | string | 是 | 图形验证码 |
| `invite_code` | string | 否 | 邀请码（站点开启时必填） |

**请求示例：**

```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "123456",
  "captcha": "a3b5"
}
```

**成功响应 (200)：**

```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "id": 2,
    "username": "testuser"
  }
}
```

当站点开启注册审核时，返回：

```json
{
  "code": 200,
  "message": "注册成功，账号正在审核中",
  "data": {
    "id": 2,
    "username": "testuser",
    "status": "pending_review"
  }
}
```

**失败响应：**

| code | message | 场景 |
|------|---------|------|
| 400 | 用户名、邮箱和密码不能为空 | 缺少必填字段 |
| 400 | 验证码错误 | 验证码不正确 |
| 400 | 验证码已过期，请刷新重试 | 验证码超过5分钟 |
| 400 | 用户名长度需在 3-20 个字符之间 | 用户名长度不符 |
| 400 | 用户名只能包含字母、数字、下划线和中文 | 用户名格式不符 |
| 400 | 密码至少6位 | 密码过短 |
| 400 | 邀请码不能为空 | 开启邀请码但未提供 |
| 400 | 邀请码无效或已过期 | 邀请码不合法 |
| 403 | 站点已关闭注册 | 注册已关闭 |
| 409 | 邮箱已被注册 | 邮箱重复 |
| 409 | 用户名已被占用 | 用户名重复 |
| 429 | 操作过于频繁，请稍后再试 | 10秒内重复请求 |

---

### 1.2 用户登录

| 属性 | 值 |
|------|-----|
| **URL** | `/api/v1/auth/login` |
| **方法** | `POST` |
| **认证** | 无 |

**请求头：**

```
Content-Type: application/json
```

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `account` | string | 是 | 用户名或邮箱 |
| `email` | string | 否 | 邮箱（兼容旧版，与account二选一） |
| `password` | string | 是 | 密码 |

**请求示例：**

```json
{
  "account": "test@example.com",
  "password": "123456"
}
```

**成功响应 (200)：**

```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "id": 2,
    "username": "testuser",
    "nickname": "测试用户",
    "display_name": "测试用户",
    "email": "test@example.com",
    "phone": "",
    "avatar": "",
    "status": 0,
    "roles_id": [2],
    "created_at": "2026-01-01T12:00:00"
  }
}
```

**失败响应：**

| code | message | 场景 |
|------|---------|------|
| 400 | 账号和密码不能为空 | 缺少必填字段 |
| 401 | 账号或密码错误 | 凭证错误 |
| 403 | 账号正在审核中，请等待管理员通过 | 账号待审核 |
| 403 | 账号已被禁用 | 账号被禁用 |
| 429 | 登录尝试过于频繁，请 N 秒后再试 | 频率限制（10次/5分钟） |

---

### 1.3 用户登出

| 属性 | 值 |
|------|-----|
| **URL** | `/api/v1/auth/logout` |
| **方法** | `POST` |
| **认证** | 需要登录 |

**成功响应 (200)：**

```json
{
  "code": 200,
  "message": "已退出登录"
}
```

---

### 1.4 获取当前用户信息

| 属性 | 值 |
|------|-----|
| **URL** | `/api/v1/auth/me` |
| **方法** | `GET` |
| **认证** | 需要登录 |

**成功响应 (200)：**

```json
{
  "code": 200,
  "data": {
    "id": 2,
    "username": "testuser",
    "nickname": "测试用户",
    "display_name": "测试用户",
    "email": "test@example.com",
    "phone": "",
    "avatar": "",
    "status": 0,
    "roles_id": [2],
    "created_at": "2026-01-01T12:00:00"
  }
}
```

---

## 2. 用户模块

### 2.1 修改个人资料

| 属性 | 值 |
|------|-----|
| **URL** | `/api/v1/user/profile` |
| **方法** | `POST` |
| **认证** | 需要登录 |

**请求头：**

```
Content-Type: application/json
```

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `nickname` | string | 否 | 昵称（最多30字符） |
| `email` | string | 否 | 新邮箱 |
| `phone` | string | 否 | 新手机号 |

> 只需传入需要修改的字段，未传入的字段不会被修改。

**请求示例：**

```json
{
  "nickname": "新昵称",
  "phone": "13800138000"
}
```

**成功响应 (200)：**

```json
{
  "code": 200,
  "message": "更新成功",
  "data": {
    "id": 2,
    "username": "testuser",
    "nickname": "新昵称",
    "display_name": "新昵称",
    "email": "test@example.com",
    "phone": "13800138000",
    "avatar": "",
    "status": 0,
    "roles_id": [2],
    "created_at": "2026-01-01T12:00:00"
  }
}
```

**失败响应：**

| code | message | 场景 |
|------|---------|------|
| 400 | 昵称长度不能超过 30 个字符 | 昵称过长 |
| 409 | 邮箱已被注册 | 邮箱重复 |

---

### 2.2 修改密码

| 属性 | 值 |
|------|-----|
| **URL** | `/api/v1/user/password` |
| **方法** | `POST` |
| **认证** | 需要登录 |

**请求头：**

```
Content-Type: application/json
```

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `old_password` | string | 是 | 旧密码 |
| `new_password` | string | 是 | 新密码（至少 6 位） |

**成功响应 (200)：**

```json
{
  "code": 200,
  "message": "密码修改成功，请重新登录"
}
```

> 修改密码后会自动登出，需重新登录。

**失败响应：**

| code | message | 场景 |
|------|---------|------|
| 400 | 旧密码和新密码不能为空 | 缺少必填字段 |
| 400 | 新密码至少6位 | 新密码过短 |
| 401 | 旧密码不正确 | 旧密码验证失败 |

---

### 2.3 上传头像

| 属性 | 值 |
|------|-----|
| **URL** | `/api/v1/user/avatar` |
| **方法** | `POST` |
| **认证** | 需要登录 |

**请求头：**

```
Content-Type: multipart/form-data
```

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `avatar` | file | 是 | 图片文件（png/jpg/jpeg/gif/webp/svg） |

**成功响应 (200)：**

```json
{
  "code": 200,
  "message": "头像上传成功",
  "data": {
    "avatar": "/uploads/avatars/20260101_a1b2c3d4.jpg"
  }
}
```

**失败响应：**

| code | message | 场景 |
|------|---------|------|
| 400 | 请上传有效的图片文件 | 文件为空或格式不支持 |

---

## 3. 卡片模块

### 3.1 获取卡片列表

| 属性 | 值 |
|------|-----|
| **URL** | `/api/v1/cards` |
| **方法** | `GET` |
| **认证** | 无 |

**查询参数：**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `page` | int | 否 | 1 | 页码 |
| `per_page` | int | 否 | 12 | 每页条数（最大 50） |
| `tag` | int | 否 | — | 按标签 ID 筛选 |

**请求示例：**

```
GET /api/v1/cards?page=1&per_page=12&tag=1
```

**成功响应 (200)：**

```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "content": "卡片内容",
        "cover": "/uploads/cards/20260101_a1b2c3d4.jpg",
        "good": 5,
        "views": 100,
        "comments": 3,
        "is_top": 1,
        "author": "testuser",
        "is_anonymous": false,
        "tags": [1, 2],
        "created_at": "2026-01-01T12:00:00"
      }
    ],
    "page": 1,
    "pages": 5,
    "total": 48,
    "has_prev": false,
    "has_next": true
  }
}
```

> 仅返回已通过审核且未删除的卡片，按置顶优先、创建时间倒序排列。
> 匿名卡片的 `author` 返回 `"匿名"`，`is_anonymous` 为 `true`。

---

### 3.2 获取卡片详情

| 属性 | 值 |
|------|-----|
| **URL** | `/api/v1/cards/<card_id>` |
| **方法** | `GET` |
| **认证** | 无（登录后可获取点赞状态） |

**路径参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `card_id` | int | 是 | 卡片 ID |

**成功响应 (200)：**

```json
{
  "code": 200,
  "data": {
    "id": 1,
    "content": "卡片内容",
    "cover": "/uploads/cards/20260101_a1b2c3d4.jpg",
    "good": 5,
    "views": 101,
    "comments": 3,
    "is_top": 1,
    "author": "testuser",
    "is_anonymous": false,
    "tags": [1, 2],
    "created_at": "2026-01-01T12:00:00",
    "is_liked": false,
    "comment_list": [
      {
        "id": 1,
        "content": "评论内容",
        "author": "commenter",
        "created_at": "2026-01-01T13:00:00"
      }
    ],
    "image_list": [
      {
        "id": 1,
        "url": "/uploads/cards/20260101_e5f6g7h8.jpg"
      }
    ]
  }
}
```

> 每次访问详情页，浏览数 `views` 自动 +1。
> `is_liked` 仅在登录状态下返回有效值，未登录时始终为 `false`。

**失败响应：**

| code | message | 场景 |
|------|---------|------|
| 404 | 卡片不存在 | 卡片不存在/未通过/已删除 |

---

### 3.3 发布卡片

| 属性 | 值 |
|------|-----|
| **URL** | `/api/v1/cards` |
| **方法** | `POST` |
| **认证** | 需要登录 |

**请求头：**

```
Content-Type: multipart/form-data
```

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `content` | string | 是 | 卡片内容（最多2000字） |
| `is_anonymous` | string | 否 | 匿名发布，传 `"1"` 为匿名 |
| `tags` | int (可多选) | 否 | 标签 ID，可传多个 |
| `cover_file` | file | 否 | 封面图文件 |
| `images` | file (可多选) | 否 | 附加图片文件，可传多个 |

**请求示例（curl）：**

```bash
curl -X POST http://localhost:8000/api/v1/cards \
  -H "Cookie: session=your_session" \
  -F "content=这是一张卡片" \
  -F "is_anonymous=0" \
  -F "tags=1" \
  -F "tags=2" \
  -F "cover_file=@cover.jpg" \
  -F "images=@img1.jpg" \
  -F "images=@img2.jpg"
```

**成功响应 (200)：**

```json
{
  "code": 200,
  "message": "发布成功，等待审核",
  "data": {
    "id": 10
  }
}
```

> 新发布的卡片 `status=0`（待审核），需管理员审核通过后才会在列表中展示。
> 发布成功后管理员会收到通知。

**失败响应：**

| code | message | 场景 |
|------|---------|------|
| 400 | 内容不能为空 | 未填写内容 |
| 400 | 内容不能超过 2000 个字符 | 内容过长 |
| 403 | 站点已关闭发布 | 发布已关闭 |

---

### 3.4 点赞/取消点赞

| 属性 | 值 |
|------|-----|
| **URL** | `/api/v1/cards/<card_id>/like` |
| **方法** | `POST` |
| **认证** | 需要登录 |

**路径参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `card_id` | int | 是 | 卡片 ID |

> 该接口为切换操作：已点赞则取消，未点赞则添加。

**成功响应 (200)：**

```json
{
  "code": 200,
  "data": {
    "liked": true,
    "count": 6
  }
}
```

**失败响应：**

| code | message | 场景 |
|------|---------|------|
| 404 | 卡片不存在 | 卡片不存在或已删除 |

---

### 3.5 发表评论

| 属性 | 值 |
|------|-----|
| **URL** | `/api/v1/cards/<card_id>/comments` |
| **方法** | `POST` |
| **认证** | 需要登录 |

**路径参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `card_id` | int | 是 | 卡片 ID |

**请求头：**

```
Content-Type: application/json
```

**请求参数：**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `content` | string | 是 | 评论内容（最多500字） |

**请求示例：**

```json
{
  "content": "很棒的卡片！"
}
```

**成功响应 (200)：**

```json
{
  "code": 200,
  "message": "评论成功",
  "data": {
    "id": 5,
    "content": "很棒的卡片！",
    "author": "testuser",
    "created_at": "2026-01-01T14:00:00"
  }
}
```

> 站点开启评论审核时，`message` 返回 "评论成功，等待审核"，评论需管理员审核后才展示。
> 评论成功后卡片作者会收到通知；待审核时管理员会收到通知。

**失败响应：**

| code | message | 场景 |
|------|---------|------|
| 400 | 评论内容不能为空 | 评论为空 |
| 400 | 评论内容不能超过 500 个字符 | 评论过长 |
| 404 | 卡片不存在 | 卡片不存在或已删除 |

---

## 4. 标签模块

### 4.1 获取标签列表

| 属性 | 值 |
|------|-----|
| **URL** | `/api/v1/tags` |
| **方法** | `GET` |
| **认证** | 无 |

**成功响应 (200)：**

```json
{
  "code": 200,
  "data": [
    { "id": 1, "name": "技术" },
    { "id": 2, "name": "生活" },
    { "id": 3, "name": "情感" }
  ]
}
```

> 仅返回启用状态（status=0）且未删除的标签。

---

## 5. 通用模块

### 5.1 通用文件上传

| 属性 | 值 |
|------|-----|
| **URL** | `/api/v1/upload` |
| **方法** | `POST` |
| **认证** | 需要登录 |

**请求头：**

```
Content-Type: multipart/form-data
```

**请求参数：**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `file` | file | 是 | — | 文件（png/jpg/jpeg/gif/webp/svg） |
| `sub_dir` | string | 否 | `cards` | 存储子目录 |

**成功响应 (200)：**

```json
{
  "code": 200,
  "message": "上传成功",
  "data": {
    "url": "/uploads/cards/20260101_a1b2c3d4.jpg"
  }
}
```

**失败响应：**

| code | message | 场景 |
|------|---------|------|
| 400 | 不支持的文件类型 | 文件格式不支持 |

---

## 6. 前台页面路由

> 以下路由返回 HTML 页面，POST 请求需携带 `csrf_token`。

### 公共页面

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 首页（卡片列表，支持 `page`、`tag`、`search` 查询参数） |
| GET | `/card/<id>` | 卡片详情页 |
| GET | `/about` | 关于页面 |
| GET | `/terms` | 服务条款 |
| GET | `/privacy` | 隐私政策 |
| GET | `/ban_records` | 封禁记录公示 |
| GET | `/api_docs` | API 文档 |

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/login` | 登录 |
| GET/POST | `/register` | 注册 |
| GET | `/logout` | 登出 |
| GET/POST | `/forgot_password` | 忘记密码 |
| GET/POST | `/reset_password/<token>` | 重置密码（1小时有效） |

### 卡片交互

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/publish` | 发布卡片（需登录） |
| POST | `/comment` | 发表评论（支持 AJAX） |
| POST | `/good/<card_id>` | 卡片点赞切换 |
| POST | `/comment/<comment_id>/good` | 评论点赞切换 |

### 个人中心

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/profile` | 个人中心首页 |
| GET/POST | `/profile/edit` | 编辑个人资料 |
| GET | `/profile/security` | 安全设置 |
| POST | `/profile/security/password` | 修改密码 |
| POST | `/profile/security/email` | 修改邮箱 |
| POST | `/profile/security/phone` | 修改手机号 |
| POST | `/profile/security/delete` | 注销账号（3天冷静期） |
| GET | `/profile/cards` | 我的卡片 |
| GET | `/profile/comments` | 我的评论 |
| POST | `/profile/cards/<id>/delete` | 删除我的卡片 |
| POST | `/profile/comments/<id>/delete` | 删除我的评论 |

### 通知

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/notifications` | 通知列表（需登录） |
| POST | `/notifications/read/<id>` | 标记已读 |
| POST | `/notifications/read_all` | 全部标记已读 |
| GET | `/notifications/count` | 未读数量 |

---

## 7. 后台管理路由

> 前缀 `/admin`，需管理员权限。标注 **[超管]** 的需要超级管理员角色。

### 仪表盘

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/` | 仪表盘（统计+待审核） |

### 卡片管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/cards` | 卡片列表（`page`/`status`/`search` 筛选） |
| GET | `/admin/cards/<id>/detail` | 卡片详情 |
| POST | `/admin/cards/<id>/approve` | 审核通过 |
| POST | `/admin/cards/<id>/reject` | 审核拒绝 |
| POST | `/admin/cards/<id>/ban` | 封禁卡片 |
| POST | `/admin/cards/<id>/unban` | 解封卡片 |
| POST | `/admin/cards/<id>/toggle_top` | 切换置顶 |
| POST | `/admin/cards/<id>/delete` | 删除卡片（软删除） |
| POST | `/admin/cards/batch` | 批量操作（approve/reject/ban/delete） |
| POST | `/admin/cards/ban_user/<user_id>` | 封禁用户所有已通过卡片 |

### 用户管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/users` | 用户列表（`page`/`status`/`role`/`search` 筛选） |
| POST | `/admin/users/<id>/toggle_status` | 切换用户状态 |
| POST | `/admin/users/<id>/ban` | 封禁用户 |
| POST | `/admin/users/<id>/unban` | 解封用户 |
| POST | `/admin/users/<id>/delete` | 删除用户 |
| POST | `/admin/users/<id>/set_role` | 设置角色 **[超管]** |

### 注册审核

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/pending_users` | 待审核用户列表 |
| POST | `/admin/pending_users/<id>/approve` | 通过审核 |
| POST | `/admin/pending_users/<id>/reject` | 拒绝审核 |
| POST | `/admin/pending_users/batch` | 批量审核 |

### 评论管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/comments` | 评论列表（`page`/`search` 筛选） |
| POST | `/admin/comments/<id>/delete` | 删除评论 |
| POST | `/admin/comment/<id>/toggle_good` | 评论点赞切换 |

### 标签管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/admin/tags` | 标签列表 / 创建标签 |
| POST | `/admin/tags/<id>/delete` | 删除标签 |
| POST | `/admin/tags/<id>/toggle_status` | 切换标签状态 |

### 邀请码管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/admin/invite_codes` | 邀请码列表 / 生成邀请码 |
| POST | `/admin/invite_codes/<id>/toggle` | 启停邀请码 |
| POST | `/admin/invite_codes/<id>/delete` | 删除邀请码 |

### 封禁记录

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/ban_records` | 封禁记录列表 |

### 审计日志

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/audit_logs` | 审计日志列表（`page`/`action`/`target_type` 筛选） |

### 已注销用户 **[超管]**

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/deleted_users` | 已注销用户列表 |
| POST | `/admin/deleted_users/<id>/restore` | 恢复用户 |
| POST | `/admin/deleted_users/<id>/purge` | 永久删除用户数据 |

### 系统配置 **[超管]**

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/admin/settings` | 查看/修改系统配置 |

---

## 8. 通用响应格式

### API 接口（`/api/v1`）

```json
{
  "code": 200,
  "message": "操作描述",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | int | 200=成功，400=参数错误，401=未认证，403=无权限，404=不存在，409=冲突，429=频率限制 |
| `message` | string | 提示信息 |
| `data` | object/null | 响应数据 |

### 前台 AJAX 接口

```json
{
  "success": true,
  "message": "操作成功"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | bool | 操作是否成功 |
| `message` | string | 提示信息 |