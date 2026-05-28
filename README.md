# Kaoyan Daily Email

每天自动生成并发送一封考研积累邮件，适合用来做长期复习提醒。项目不依赖 Gmail，QQ 邮箱、163 邮箱、126 邮箱、腾讯企业邮箱等中国国内邮箱都可以作为发件邮箱。

邮件内容包括：

- 考研英语一写作例句，控制在 2 到 3 句
- 考研数学基础阶段知识点、公式和易错点
- 408 四门专业课知识点：数据结构、计算机组成原理、操作系统、计算机网络
- 408 数据结构算法每日一题
- 按遗忘曲线安排复习：`D-1 / D-3 / D-7 / D-14 / D-30 / D-60 / D-120`

邮件会发送 HTML 美化版，同时保留纯文本版本作为兼容回退。英语例句会限制在考研英语一作文常见主题内，不会写成数学、算法或计算机专业课内容。

默认发送时间是北京时间每天 `08:07`。

## 推荐部署方式

推荐部署到自己的 Linux 服务器，用 `cron` 定时运行。这样 `sent_history.json` 会长期保存在服务器上，遗忘曲线复习才能稳定追踪 30 天、60 天、120 天前的内容。

GitHub Actions 也能运行，但如果账号受限、Actions 排队异常，或者不想处理 GitHub 权限问题，用服务器部署更省心。

## 准备 DeepSeek API

需要一个 DeepSeek API Key，用来生成每日内容。

环境变量：

| 变量名 | 是否必填 | 示例 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | 必填 | `sk-xxxxxxxx` |
| `DEEPSEEK_BASE_URL` | 可选 | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | 可选 | `deepseek-v4-flash` |

`DEEPSEEK_BASE_URL` 不填时默认使用 `https://api.deepseek.com`。`DEEPSEEK_MODEL` 不填时默认使用 `deepseek-v4-flash`。

## 使用国内邮箱发件

你只需要准备一个支持 SMTP 的邮箱作为发件邮箱。收件邮箱可以是 Gmail、QQ 邮箱、163 邮箱或其他邮箱。

通用环境变量：

| 变量名 | 是否必填 | 说明 |
| --- | --- | --- |
| `SMTP_HOST` | 必填 | SMTP 服务器地址 |
| `SMTP_PORT` | 必填 | SSL 端口，一般填 `465` |
| `SMTP_USER` | 必填 | 发件邮箱完整地址 |
| `SMTP_PASSWORD` | 必填 | SMTP 授权码，不是网页登录密码 |
| `FROM_EMAIL` | 可选 | 发件人邮箱，不填则使用 `SMTP_USER` |
| `TO_EMAIL` | 必填 | 收件邮箱 |

常见国内邮箱 SMTP 参数：

| 邮箱 | `SMTP_HOST` | `SMTP_PORT` | `SMTP_USER` | `SMTP_PASSWORD` |
| --- | --- | --- | --- | --- |
| QQ 邮箱 | `smtp.qq.com` | `465` | 完整 QQ 邮箱地址 | QQ 邮箱 SMTP 授权码 |
| 163 邮箱 | `smtp.163.com` | `465` | 完整 163 邮箱地址 | 163 邮箱授权码 |
| 126 邮箱 | `smtp.126.com` | `465` | 完整 126 邮箱地址 | 126 邮箱授权码 |
| Yeah 邮箱 | `smtp.yeah.net` | `465` | 完整 Yeah 邮箱地址 | Yeah 邮箱授权码 |
| 腾讯企业邮箱 | `smtp.exmail.qq.com` | `465` | 完整企业邮箱地址 | 邮箱授权码或客户端专用密码 |

QQ 邮箱获取授权码：

1. 打开 QQ 邮箱网页版。
2. 进入 `设置 -> 账号`。
3. 找到 `POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV 服务`。
4. 开启 `POP3/SMTP服务` 或 `IMAP/SMTP服务`。
5. 按页面提示短信验证，生成 SMTP 授权码。
6. 把授权码填到 `SMTP_PASSWORD`。

163/126 邮箱获取授权码：

1. 打开 163 或 126 邮箱网页版。
2. 进入 `设置 -> POP3/SMTP/IMAP`。
3. 开启 SMTP 或 IMAP/SMTP 服务。
4. 生成客户端授权码。
5. 把授权码填到 `SMTP_PASSWORD`。

注意：`SMTP_PASSWORD` 填授权码，不填网页登录密码。

## 服务器部署

下面以 Ubuntu 服务器为例。

### 1. 上传项目

在服务器上准备目录：

```bash
mkdir -p ~/kaoyan-daily-email
cd ~/kaoyan-daily-email
```

把本项目文件放到这个目录，至少需要：

```text
daily_email.py
requirements.txt
```

### 2. 安装 Python 依赖

```bash
cd ~/kaoyan-daily-email
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 3. 创建 `.env`

在 `~/kaoyan-daily-email/.env` 中填写自己的配置：

```bash
DEEPSEEK_API_KEY=你的DeepSeek_API_Key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash

SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USER=你的QQ邮箱@qq.com
SMTP_PASSWORD=你的QQ邮箱SMTP授权码
FROM_EMAIL=你的QQ邮箱@qq.com
TO_EMAIL=你的收件邮箱
```

如果用 163 邮箱发件，把 SMTP 部分改成：

```bash
SMTP_HOST=smtp.163.com
SMTP_PORT=465
SMTP_USER=你的163邮箱@163.com
SMTP_PASSWORD=你的163邮箱授权码
FROM_EMAIL=你的163邮箱@163.com
TO_EMAIL=你的收件邮箱
```

不要把 `.env` 提交到 GitHub。

### 4. 创建运行脚本

在 `~/kaoyan-daily-email/run_daily.sh` 中写入：

```bash
#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
set -a
source .env
set +a

.venv/bin/python daily_email.py
```

然后赋予执行权限：

```bash
chmod +x ~/kaoyan-daily-email/run_daily.sh
```

### 5. 手动测试

```bash
cd ~/kaoyan-daily-email
./run_daily.sh
```

看到类似输出就表示发送成功：

```text
sent: 考研每日积累 | 英一 + 数学 + 408 | 2026-05-28
```

如果没有收到邮件，先看垃圾箱，再检查 `TO_EMAIL`、SMTP 授权码和发件邮箱是否开启 SMTP 服务。

### 6. 设置每天自动发送

先创建日志目录：

```bash
mkdir -p ~/kaoyan-daily-email/logs
```

编辑定时任务：

```bash
crontab -e
```

添加：

```cron
7 8 * * * /home/ubuntu/kaoyan-daily-email/run_daily.sh >> /home/ubuntu/kaoyan-daily-email/logs/cron.log 2>&1
```

如果你的服务器用户名不是 `ubuntu`，把 `/home/ubuntu/kaoyan-daily-email` 改成自己的项目路径。

查看定时任务：

```bash
crontab -l
```

## GitHub Actions 部署

如果你的 GitHub Actions 可以正常运行，也可以直接用仓库工作流。

进入仓库：

```text
Settings -> Secrets and variables -> Actions -> New repository secret
```

添加这些 secrets：

| Name | Secret |
| --- | --- |
| `DEEPSEEK_API_KEY` | 你的 DeepSeek API Key |
| `DEEPSEEK_MODEL` | 可选，默认 `deepseek-v4-flash` |
| `DEEPSEEK_BASE_URL` | 可选，默认 `https://api.deepseek.com` |
| `SMTP_HOST` | 例如 `smtp.qq.com` |
| `SMTP_PORT` | `465` |
| `SMTP_USER` | 发件邮箱完整地址 |
| `SMTP_PASSWORD` | SMTP 授权码 |
| `FROM_EMAIL` | 发件邮箱完整地址 |
| `TO_EMAIL` | 收件邮箱 |

填写 Secret 时，`Name` 和 `Secret` 要分开填。比如：

```text
Name: SMTP_HOST
Secret: smtp.qq.com
```

不要把 Secret 写成：

```text
SMTP_HOST=smtp.qq.com
```

手动运行：

```text
Actions -> Daily Kaoyan Email v2 -> Run workflow
```

GitHub Actions 的定时任务使用 UTC，当前工作流配置是 `7 0 * * *`，对应北京时间每天 `08:07`。

## Gmail 可选

本项目不需要 Gmail。只有当你想用 Gmail 作为发件邮箱时，才需要配置：

| 变量名 | 说明 |
| --- | --- |
| `GMAIL_USER` | Gmail 地址 |
| `GMAIL_APP_PASSWORD` | Gmail App Password |

国内邮箱用户不需要填写 `GMAIL_USER` 和 `GMAIL_APP_PASSWORD`。

## 常见错误

### `socket.gaierror: [Errno -2] Name or service not known`

通常是 `SMTP_HOST` 填错了，或者在 Secret 里把值写成了 `SMTP_HOST=smtp.qq.com`。正确写法是 `Name` 填 `SMTP_HOST`，`Secret` 只填 `smtp.qq.com`。

### `SMTPAuthenticationError` 或 `535`

常见原因：

- `SMTP_PASSWORD` 填成了网页登录密码，而不是授权码。
- 邮箱没有开启 SMTP 服务。
- 授权码复制错了，或多了空格。
- `SMTP_USER` 没有填写完整邮箱地址。

### GitHub Actions checkout 报 `403`

这通常是 GitHub 账号、仓库权限或 Actions 权限问题，不是邮箱配置问题。可以先改用服务器部署。

### 邮件发送成功但收不到

检查：

- 垃圾箱或广告邮件分类
- `TO_EMAIL` 是否写错
- 发件邮箱是否被限制 SMTP 发送
- 同一天反复测试可能被邮箱服务商临时限流

## 文件说明

| 文件 | 说明 |
| --- | --- |
| `daily_email.py` | 生成内容、渲染邮件、发送邮件 |
| `requirements.txt` | Python 依赖 |
| `.github/workflows/daily-v2.yml` | GitHub Actions 定时任务 |
| `sent_history.json` | 发送历史，服务器运行后自动生成 |

`sent_history.json` 用来记录历史内容，支持后续的遗忘曲线复习。服务器部署时建议长期保留这个文件。
