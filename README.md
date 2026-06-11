# 教师评教系统

基于 Python 3.11 + Flask 的轻量级学生评教系统，使用内存 + JSON 文件存储，无需数据库。

## 项目结构

```
.
├── app/
│   ├── __init__.py
│   ├── config.py              # 配置文件
│   ├── app.py                 # 主入口
│   ├── models/
│   │   └── dataclasses.py     # 数据模型
│   ├── services/
│   │   ├── auth_service.py    # 认证与权限
│   │   └── review_service.py  # 业务逻辑
│   ├── storage/
│   │   └── json_store.py      # JSON 存储
│   ├── censor/
│   │   └── censor.py          # 敏感词过滤
│   ├── routes/
│   │   ├── students.py        # 学生接口
│   │   ├── teachers.py        # 教师接口
│   │   ├── courses.py         # 课程接口
│   │   ├── reviews.py         # 评价接口
│   │   ├── admin.py           # 管理员接口
│   │   └── base.py            # 基础数据接口
│   └── utils/
│       └── response.py        # 统一响应格式
├── data/                      # JSON 数据目录
│   ├── courses.json
│   ├── enrollments.json
│   ├── reviews.json
│   ├── semesters.json
│   ├── students.json
│   └── teachers.json
├── censor_words.txt           # 敏感词库
├── requirements.txt
├── .env.example
├── .env
└── README.md
```

## 快速启动

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并根据需要修改：

```
PORT=8080
ADMIN_USER=admin
ADMIN_PASS=admin123
JWT_SECRET=your-secret-key-here
```

### 3. 启动服务

```bash
python app.py
```

服务将在 `http://localhost:8080` 启动。

## 初始化数据说明

系统启动时会自动从 `data/` 目录加载 JSON 数据。默认包含以下测试数据：

- **4 名学生**: s001-s004 (小明、小红、小华、小丽)
- **4 名教师**: t001-t004 (张教授、李老师、王教授、陈老师)
- **6 门课程**: 数据结构、高等数学、大学物理、计算机网络、大学英语、操作系统
- **3 个学期**: 2023-fall(已结课)、2024-spring(已结课)、2024-fall(进行中)
- **12 条选课记录**

## 获取 Token

### 管理员登录

```bash
curl -X POST http://localhost:8080/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

响应示例：
```json
{
  "code": 0,
  "msg": "登录成功",
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
}
```

### 学生/教师 Token 生成

为了方便测试，你可以使用 Python 生成任意角色的 Token：

```python
from app.services.auth_service import generate_student_token, generate_teacher_token

# 学生 token (id: s001)
student_token = generate_student_token("s001")

# 教师 token (id: t001)
teacher_token = generate_teacher_token("t001")
```

## 核心接口示例

所有需要认证的接口都需要在请求头中携带：

```
Authorization: Bearer <your-token>
```

### 学生接口

#### 1. 查看可评价的课程

```bash
curl http://localhost:8080/students/s001/available-courses \
  -H "Authorization: Bearer <student-token>"
```

#### 2. 提交评价

```bash
curl -X POST http://localhost:8080/reviews \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <student-token>" \
  -d '{
    "student_id": "s001",
    "course_id": "c001",
    "semester": "2023-fall",
    "content_score": 5,
    "difficulty_score": 3,
    "gain_score": 4,
    "comment": "老师讲得很好，内容充实，收获很大。"
  }'
```

#### 3. 查看自己的评价记录

```bash
curl http://localhost:8080/students/s001/reviews \
  -H "Authorization: Bearer <student-token>"
```

### 教师接口

#### 1. 查看自己教的课程

```bash
curl http://localhost:8080/teachers/t001/courses \
  -H "Authorization: Bearer <teacher-token>"
```

#### 2. 查看课程汇总分

```bash
curl http://localhost:8080/teachers/t001/courses/c001/summary \
  -H "Authorization: Bearer <teacher-token>"
```

响应示例：
```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "courseId": "c001",
    "courseName": "数据结构",
    "semester": "2023-fall",
    "totalReviews": 2,
    "contentAvg": 4.50,
    "difficultyAvg": 3.00,
    "gainAvg": 4.00,
    "scoreDistribution": {
      "1": 0,
      "2": 0,
      "3": 0,
      "4": 1,
      "5": 1
    }
  }
}
```

### 管理员接口

#### 1. 查看所有评价（含敏感词筛选）

```bash
# 所有评价
curl http://localhost:8080/admin/reviews \
  -H "Authorization: Bearer <admin-token>"

# 仅看命中敏感词的评价
curl "http://localhost:8080/admin/reviews?sensitive=true" \
  -H "Authorization: Bearer <admin-token>"
```

#### 2. 查看整体统计

```bash
curl http://localhost:8080/admin/stats \
  -H "Authorization: Bearer <admin-token>"
```

#### 3. 学期结课操作

```bash
curl -X POST http://localhost:8080/admin/semesters/2024-fall/close \
  -H "Authorization: Bearer <admin-token>"
```

#### 4. 热更新敏感词库

```bash
curl -X POST http://localhost:8080/admin/censor-words \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin-token>" \
  -d '{"words": ["脏话1", "脏话2", "敏感词3"]}'
```

#### 5. 查看当前敏感词库

```bash
curl http://localhost:8080/admin/censor-words \
  -H "Authorization: Bearer <admin-token>"
```

### 基础数据接口

```bash
# 课程列表
curl http://localhost:8080/courses \
  -H "Authorization: Bearer <token>"

# 教师列表
curl http://localhost:8080/teachers \
  -H "Authorization: Bearer <token>"

# 学生列表
curl http://localhost:8080/students \
  -H "Authorization: Bearer <token>"
```

### 健康检查

```bash
curl http://localhost:8080/healthz
```

## 业务规则

1. **评价权限**: 学生只能评价自己选修过且已结课的课程
2. **防重复**: 一个学生一门课一学期只能评一次
3. **时效性**: 结课超过 2 学期（1 年）的课程不能再评
4. **评分范围**: 三个维度（内容质量、难度感受、收获程度）均为 1-5 整数
5. **评语文本**: 1-500 字，自动过滤敏感词
6. **教师权限**: 只能看汇总分，不能看单条评价内容
7. **数据持久化**: 内存优先，每 5 秒或累积 100 次写入自动落盘

## 统一响应格式

```json
{
  "code": 0,
  "msg": "ok",
  "data": {...}
}
```

- `code`: 0 表示成功，非 0 表示错误
- `msg`: 错误信息或成功提示
- `data`: 响应数据

## 错误码说明

| 状态码 | 说明 |
|--------|------|
| 400 | 参数错误 |
| 401 | 未认证或 Token 无效 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 409 | 资源冲突（如重复评价） |
| 422 | 业务规则校验失败 |
| 500 | 服务器内部错误 |
