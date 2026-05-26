# Kaoyan Daily Email

每天通过 GitHub Actions 自动生成并发送一封考研积累邮件，内容包括：

- 考研英语一写作例句积累
- 考研408数据结构大题算法每日一题

默认发送时间是北京时间每天 08:07。GitHub Actions 的定时任务使用 UTC，所以工作流里配置的是 `7 0 * * *`。

## 配置 GitHub Secrets

进入仓库：

`Settings -> Secrets and variables -> Actions -> New repository secret`

添加这些 secrets：

| Name | Value |
| --- | --- |
| `OPENAI_API_KEY` | 你的 OpenAI API Key |
| `OPENAI_MODEL` | 可选，默认使用 `gpt-4.1-mini` |
| `GMAIL_USER` | 发件 Gmail，例如 `zrf051231@gmail.com` |
| `GMAIL_APP_PASSWORD` | Gmail App Password，不是网页登录密码 |
| `TO_EMAIL` | 收件邮箱，例如 `zrf051231@gmail.com` |

## Gmail App Password

Gmail SMTP 需要使用 App Password：

1. 开启 Google 账号两步验证。
2. 打开 <https://myaccount.google.com/apppasswords>。
3. 创建一个用于邮件发送的 App Password。
4. 把生成的 16 位密码填入 `GMAIL_APP_PASSWORD`。

如果密码中显示有空格，可以原样复制；脚本会自动去掉空格。

## 手动测试

在仓库页面进入：

`Actions -> Daily Kaoyan Email -> Run workflow`

第一次建议手动运行一次，确认邮件能收到。之后会每天自动运行。

## 注意

- 定时任务只会在默认分支上的 workflow 生效。
- GitHub Actions 的 scheduled workflow 可能会有几分钟延迟。
- 如果仓库长时间没有活动，公开仓库的定时任务可能被 GitHub 暂停；私有仓库通常更适合这种个人自动化。
