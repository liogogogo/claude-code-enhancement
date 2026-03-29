---
name: security-check
description: 部署前安全检查，扫描代码漏洞、依赖风险、配置问题。用户请求安全检查或部署前检查时自动触发。
---

# Security Check Skill

部署前安全检查，防止漏洞上线。

## 检查维度

### 1. 代码漏洞扫描

| 类型 | 检查项 | 工具 |
|------|--------|------|
| SQL 注入 | 字符串拼接 SQL | grep/semgrep |
| XSS | 未转义用户输入 | grep/semgrep |
| 命令注入 | exec 用户输入 | grep/semgrep |
| 硬编码密钥 | API key、密码明文 | grep |

**检查命令**:
```bash
# 查找硬编码密钥
grep -rE "(password|api_key|secret|token)\s*=\s*['\"][^'\"]+['\"]" src/

# 查找 SQL 拼接
grep -rE "execute.*\+|query.*\+" src/

# 查找命令注入
grep -rE "exec|system|shell.*\+" src/
```

### 2. 依赖安全检查

```bash
# Python
pip-audit || safety check

# JavaScript
npm audit || pnpm audit

# Go
govulncheck ./...

# Rust
cargo audit
```

### 3. 配置安全检查

| 检查项 | 风险 | 建议 |
|--------|------|------|
| `.env` 文件 | 泄露敏感配置 | 使用 `.env.example`，真实 `.env` 不提交 |
| CORS 配置 | 过宽允许 | 限制特定域名 |
| 调试模式 | 生产开启 | 确保 `DEBUG=false` |
| HTTPS | 未强制 | 重定向 HTTP 到 HTTPS |

### 4. Docker 安全

```bash
# 检查 Dockerfile
grep -E "USER root|RUN apt" Dockerfile

# 建议
# - 不使用 root 用户
# - 最小化镜像
# - 不安装不必要的包
```

### 5. API 安全检查

| 检查项 | 说明 |
|--------|------|
| 认证机制 | JWT/OAuth 是否正确实现 |
| 权限校验 | 每个接口是否验证权限 |
| 输入验证 | 是否有 schema 验证 |
| 速率限制 | 是否防止 DDoS |

## 输出格式

```markdown
## 🔒 安全检查报告

### 🔴 高风险 (必须修复)
- [文件:行号] 问题描述
  - 影响: ...
  - 建议: ...

### 🟡 中风险 (建议修复)
- [文件:行号] 问题描述

### 🟢 低风险 (可选优化)
- [文件:行号] 问题描述

### ✅ 已检查项
- 依赖扫描: 无已知漏洞
- 配置检查: 通过

### 总结
是否可以安全部署: [是/否]
优先修复项: ...
```

## 注意事项

- 检查后给出具体修复代码示例
- 标记问题严重程度
- 依赖工具需提前安装（pip-audit、npm audit 等）
- 检查结果仅供参考，需人工确认