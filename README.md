# 电子秤计量检定服务

## 原始需求

> 请开发电子秤计量检定服务，使用 FastAPI 和 PostgreSQL 管理商户、秤具编号、检定预约、标准砝码、读数记录、误差判定、合格标签、整改复检和监管抽查。市场监管人员导入商户与秤具档案，商户预约上门或集中检定，检定员记录砝码读数、环境条件、现场照片和封签信息，系统签发合格证或整改通知。服务要处理同一秤重复预约、读数超差、标签作废、离线补录、抽查追溯和检定员误操作，合格结论不能只靠一个简单通过字段。

## 项目简介

本项目是一个完整的电子秤计量检定服务系统，基于 FastAPI 和 PostgreSQL 开发，支持商户管理、秤具档案管理、检定预约、标准砝码管理、读数记录、误差自动判定、合格标签签发、整改复检、监管抽查和操作追溯等功能。

## 技术栈

- **后端框架**: FastAPI 0.115.0
- **数据库**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0.35
- **认证**: JWT (python-jose)
- **密码加密**: passlib + bcrypt
- **容器化**: Docker + Docker Compose

## 主要功能

### 1. 用户与权限管理
- 四种角色：系统管理员、市场监管员、检定员、商户
- JWT 令牌认证
- 基于角色的权限控制

### 2. 商户管理
- 商户信息 CRUD
- CSV 批量导入商户档案
- 商户状态管理

### 3. 秤具管理
- 秤具档案管理（编号、型号、精度等级等）
- CSV 批量导入秤具档案
- 秤具状态管理
- 检定周期自动计算

### 4. 检定预约
- 商户预约上门或集中检定
- 预约确认与取消
- 同一秤重复预约检测与标记
- 检定员分配

### 5. 检定流程
- 标准砝码管理
- 多载荷点读数记录
- 自动误差计算与合格判定
- 环境条件记录（温度、湿度等）
- 封签信息记录
- 现场照片记录
- 离线补录支持
- 检定结论签发（最终结论与原因）

### 6. 合格标签
- 自动生成标签编号
- 标签签发与作废
- 标签有效期管理
- 每秤仅能有一张有效标签

### 7. 整改复检
- 不合格项整改通知
- 整改进度跟踪
- 复检预约安排
- 复检结果判定

### 8. 监管抽查
- 抽查计划与记录
- 多类型抽查（例行、投诉、随机、专项）
- 秤具全生命周期追溯
- 历史检定记录查询

### 9. 操作日志
- 全操作审计追踪
- 支持离线补录标记
- 支持标签作废记录

## 启动方式

### 前置要求

- Docker 20.10+
- Docker Compose v2+

或者：

- Python 3.11+
- PostgreSQL 13+

### 方式一：Docker 一键启动（推荐）

#### 1. 克隆项目到本地

```bash
cd 项目目录
```

#### 2. 启动服务

```bash
docker compose up --build
```

如需后台运行：

```bash
docker compose up --build -d
```

#### 3. 访问服务

API 服务地址：http://localhost:8000

API 文档地址：http://localhost:8000/docs

#### 4. 停止服务

```bash
docker compose down
```

### 方式二：本地开发启动

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 配置环境变量

复制 `.env.example` 为 `.env`，根据实际情况修改数据库连接等配置：

```bash
cp .env.example .env
```

#### 3. 初始化数据库

确保 PostgreSQL 服务已启动并创建好数据库，然后执行：

```bash
python scripts/init_db.py
```

#### 4. 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 5. 访问服务

API 服务地址：http://localhost:8000

API 文档地址：http://localhost:8000/docs

## 默认账号

系统初始化后会创建以下测试账号：

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 系统管理员 | admin | admin123 |
| 市场监管员 | regulator | regulator123 |
| 检定员 | verifier | verifier123 |
| 商户 | merchant | merchant123 |

## 核心业务流程

### 检定流程

1. **市场监管员** 导入商户和秤具档案
2. **商户** 发起检定预约（上门或集中）
3. **市场监管员/检定员** 确认预约并分配检定员
4. **检定员** 现场检定：
   - 记录环境条件（温度、湿度）
   - 检查封签完整性
   - 使用标准砝码进行多载荷点测试
   - 记录每次读数
   - 系统自动计算误差并判定是否合格
5. 系统根据读数和封签综合判定检定结果
6. **检定员** 签发最终检定结论和原因
7. 合格的签发合格标签，不合格的发出整改通知

### 误差判定规则

- 根据秤具精度等级自动计算允差
- 每次读数自动计算绝对误差和相对误差
- 所有载荷点均合格且封签完好才算检定通过
- 不合格的需要整改并安排复检

## API 模块列表

| 模块 | 路径前缀 | 说明 |
|------|----------|------|
| 认证 | /auth | 登录、获取当前用户信息 |
| 用户管理 | /users | 用户 CRUD（管理员） |
| 商户管理 | /merchants | 商户 CRUD、批量导入 |
| 秤具管理 | /scales | 秤具 CRUD、批量导入 |
| 标准砝码 | /standard-weights | 标准砝码管理 |
| 检定预约 | /appointments | 预约 CRUD、确认、取消 |
| 检定管理 | /verifications | 检定记录、读数、结果判定 |
| 合格标签 | /labels | 标签签发、作废、查询 |
| 整改复检 | /rectifications | 整改通知、复检、完成 |
| 监管抽查 | /inspections | 抽查记录、追溯查询 |
| 操作日志 | /operation-logs | 操作审计日志 |

## 目录结构

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # 应用入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   ├── models.py            # 数据模型
│   ├── schemas.py           # Pydantic 模式
│   ├── auth.py              # 认证与权限
│   ├── utils.py             # 工具函数
│   ├── crud.py              # 基础 CRUD 操作
│   ├── crud_verification.py # 检定相关 CRUD
│   └── routers/             # API 路由
│       ├── __init__.py
│       ├── auth.py
│       ├── users.py
│       ├── merchants.py
│       ├── scales.py
│       ├── standard_weights.py
│       ├── appointments.py
│       ├── verifications.py
│       ├── labels.py
│       ├── rectifications.py
│       ├── inspections.py
│       └── operation_logs.py
├── scripts/
│   ├── __init__.py
│   └── init_db.py           # 数据库初始化脚本
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env.example
├── requirements.txt
└── README.md
```

## 注意事项

1. 生产环境请务必修改默认密钥和密码
2. 数据库数据默认通过 Docker volume 持久化
3. 合格结论由多维度综合判定（读数误差、封签状态、检定员结论），不仅是一个简单的通过字段
4. 系统支持离线补录标记，便于现场无网络时的后续同步
5. 所有关键操作都有审计日志，支持操作追溯
6. 同一秤具只能有一张有效的合格标签
