# Kaoyan Daily Email

每天通过 GitHub Actions 自动生成并发送一封考研积累邮件，内容包括：

- 考研英语一写作例句积累，控制在2到3句
- 考研数学基础阶段知识点
- 考研408四门专业课知识点
- 考研408数据结构算法每日一题

邮件会以 HTML 卡片样式发送，同时保留纯文本版本作为兼容回退。

默认发送时间是北京时间每天 08:07。GitHub Actions 的定时任务使用 UTC，所以工作流里配置的是 `7 0 * * *`。

## 配置 GitHub Secrets

进入仓库：

`Settings -> Secrets and variables -> Actions -> New repository secret`

添加这些 secrets：

| Name | Value |
| --- | --- |
| `DEEPSEEK_API_KEY` | 你的 DeepSeek API Key |
| `DEEPSEEK_MODEL` | 可选，默认使用 `deepseek-v4-flash` |
| `DEEPSEEK_BASE_URL` | 可选，默认使用 `https://api.deepseek.com` |
| `TO_EMAIL` | 收件邮箱，例如 `zrf051231@gmail.com` |

发件方式二选一：

| Name | Value |
| --- | --- |
| `GMAIL_USER` | 发件 Gmail，例如 `zrf051231@gmail.com` |
| `GMAIL_APP_PASSWORD` | Gmail App Password，不是网页登录密码 |

或使用通用 SMTP：

| Name | Value |
| --- | --- |
| `SMTP_HOST` | SMTP 服务器，例如 `smtp.qq.com`、`smtp.163.com` |
| `SMTP_PORT` | SMTP SSL 端口，默认 `465` |
| `SMTP_USER` | SMTP 登录账号 |
| `SMTP_PASSWORD` | SMTP 授权码或应用专用密码 |
| `FROM_EMAIL` | 可选，发件人邮箱；不填则使用 `SMTP_USER` |

`TO_EMAIL` 可以继续填 `zrf051231@gmail.com`，也就是发到你的 Gmail。

填写 GitHub Secret 时，`Name` 和 `Secret` 要分开填；`Secret` 里只填值本身。比如 `Name` 填 `SMTP_HOST`，`Secret` 只填 `smtp.qq.com`，不要填成 `SMTP_HOST=smtp.qq.com`。

## Gmail App Password

Gmail SMTP 需要使用 App Password：

1. 开启 Google 账号两步验证。
2. 打开 <https://myaccount.google.com/apppasswords>。
3. 创建一个用于邮件发送的 App Password。
4. 把生成的 16 位密码填入 `GMAIL_APP_PASSWORD`。

如果密码中显示有空格，可以原样复制；脚本会自动去掉空格。

如果 App Password 页面提示“您的账号不支持您正在尝试的设置”，通常说明当前 Google 账号不能创建应用专用密码。常见原因包括：没有开启两步验证、账号只使用安全密钥作为两步验证方式、账号属于工作/学校/组织管理，或开启了高级保护计划。

这种情况下可以改用其他发件方式，例如：

- 换一个可以创建 App Password 的 Gmail 账号作为发件邮箱。
- 使用 QQ 邮箱、163 邮箱等支持 SMTP 授权码的邮箱。
- 使用 Resend、SendGrid 等邮件发送服务。

## 手动测试

在仓库页面进入：

`Actions -> Daily Kaoyan Email -> Run workflow`

第一次建议手动运行一次，确认邮件能收到。之后会每天自动运行。

## 注意

- 定时任务只会在默认分支上的 workflow 生效。
- GitHub Actions 的 scheduled workflow 可能会有几分钟延迟。
- 如果仓库长时间没有活动，公开仓库的定时任务可能被 GitHub 暂停；私有仓库通常更适合这种个人自动化。
