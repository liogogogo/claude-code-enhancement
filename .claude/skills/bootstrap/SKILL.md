---
name: bootstrap
description: 新项目脚手架工具，快速创建标准项目结构。用户请求创建项目或初始化项目时自动触发。
---

# Project Bootstrap Skill

快速创建标准化项目结构，节省 30-60 分钟初始化时间。

## 支持的项目类型

| 类型 | 框架 | 结构 |
|------|------|------|
| Python | FastAPI/Flask/Django | src/, tests/, pyproject.toml |
| TypeScript | Next.js/Express/React | src/, tests/, package.json |
| Go | Gin/Echo | cmd/, internal/, go.mod |
| Rust | Actix/Axum | src/, Cargo.toml |

## 执行流程

1. **询问项目信息**
   - 项目名称
   - 项目类型（Python/TS/Go/Rust）
   - 框架选择
   - 是否需要 Docker

2. **创建目录结构**

   **Python (FastAPI)**:
   ```
   project/
   ├── src/
   │   ├── __init__.py
   │   ├── main.py
   │   ├── api/
   │   │   └── routes.py
   │   └── models/
   │       └── __init__.py
   ├── tests/
   │   └── test_main.py
   ├── pyproject.toml
   ├── .gitignore
   ├── README.md
   └── Dockerfile (可选)
   ```

   **TypeScript (Express)**:
   ```
   project/
   ├── src/
   │   ├── index.ts
   │   ├── routes/
   │   │   └── index.ts
   │   └── controllers/
   │       └── index.ts
   ├── tests/
   │   └ index.test.ts
   ├── package.json
   ├── tsconfig.json
   ├── .gitignore
   └── README.md
   ```

   **Go (Gin)**:
   ```
   project/
   ├── cmd/
   │   └── main.go
   ├── internal/
   │   ├── handlers/
   │   ├── models/
   │   └── services/
   ├── pkg/
   ├── go.mod
   ├── .gitignore
   └ README.md
   ```

3. **生成配置文件**

   - `pyproject.toml` / `package.json` / `go.mod`
   - `.gitignore`（适配语言）
   - `README.md`（项目说明模板）
   - `Dockerfile`（可选）

4. **初始化 Git**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: project bootstrap"
   ```

## 注意事项

- 使用用户指定的项目名称
- 文件内容包含基本模板代码
- README 包含快速启动指南
- 不创建远程仓库，需用户手动关联