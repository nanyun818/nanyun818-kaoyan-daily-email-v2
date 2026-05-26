import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from zoneinfo import ZoneInfo

from openai import OpenAI


TIMEZONE = "Asia/Shanghai"
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"

DS_TOPICS = [
    "linear lists and linked-list pointer manipulation",
    "stacks, queues, and expression or traversal applications",
    "binary trees and threaded/balanced tree reasoning",
    "graphs, traversal, connectivity, and shortest paths",
    "searching, hashing, and average search length analysis",
    "sorting algorithms and complexity/stability analysis",
    "classic algorithm design with data-structure invariants",
]


def require_env(name: str) -> str:
    value = clean_env(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def clean_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    prefix = f"{name}="
    if value.startswith(prefix):
        value = value[len(prefix):].strip()
    return value


def today_info() -> tuple[str, str]:
    now = datetime.now(ZoneInfo(TIMEZONE))
    date_text = now.strftime("%Y-%m-%d")
    topic = DS_TOPICS[(now.timetuple().tm_yday - 1) % len(DS_TOPICS)]
    return date_text, topic


def build_prompt(date_text: str, topic: str) -> str:
    return f"""
请生成一封中文每日考研积累邮件，日期：{date_text}。

内容必须紧凑、实用、适合每天阅读，面向考研英语一和考研408复习。

一、考研英语一写作例句积累
- 给出6个高分、可复用的英文句子。
- 覆盖图表描述、原因/影响、对比、问题解决、社会价值、总结升华等常见写作功能。
- 每个句子后给中文翻译和一句简短使用场景说明。
- 最后给1个仿写练习。

二、考研408数据结构大题算法每日一题
- 今天的数据结构主题倾向：{topic}。
- 题目要像408大题，不能只是概念问答。
- 包含：题目、数据结构或输入输出假设、关键思路、C/C++风格伪代码、时间复杂度、空间复杂度、样例、常见易错点。
- 题目难度中等偏上，重视算法过程和边界条件。

不要写客套话，不要使用占位符，不要编造真实考试年份。
""".strip()


def generate_body(date_text: str, topic: str) -> str:
    client = OpenAI(
        api_key=require_env("DEEPSEEK_API_KEY"),
        base_url=clean_env("DEEPSEEK_BASE_URL") or DEFAULT_DEEPSEEK_BASE_URL,
    )
    response = client.chat.completions.create(
        model=clean_env("DEEPSEEK_MODEL") or DEFAULT_DEEPSEEK_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a precise Chinese study coach for postgraduate entrance exam preparation.",
            },
            {"role": "user", "content": build_prompt(date_text, topic)},
        ],
        temperature=0.7,
        stream=False,
        extra_body={"thinking": {"type": "disabled"}},
    )
    body = (response.choices[0].message.content or "").strip()
    if not body:
        raise RuntimeError("DeepSeek returned an empty response.")
    return body


def send_email(subject: str, body: str) -> None:
    smtp_host = clean_env("SMTP_HOST") or "smtp.gmail.com"
    smtp_port = int(clean_env("SMTP_PORT") or "465")
    smtp_user = clean_env("SMTP_USER") or clean_env("GMAIL_USER")
    smtp_password = clean_env("SMTP_PASSWORD") or clean_env("GMAIL_APP_PASSWORD")
    if not smtp_user:
        raise RuntimeError("Missing required environment variable: SMTP_USER or GMAIL_USER")
    if not smtp_password:
        raise RuntimeError("Missing required environment variable: SMTP_PASSWORD or GMAIL_APP_PASSWORD")
    smtp_password = smtp_password.replace(" ", "")
    from_email = clean_env("FROM_EMAIL") or smtp_user
    to_email = require_env("TO_EMAIL")

    message = EmailMessage()
    message["From"] = from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP_SSL(smtp_host, smtp_port) as smtp:
        smtp.login(smtp_user, smtp_password)
        smtp.send_message(message)


def main() -> None:
    date_text, topic = today_info()
    subject = f"考研每日积累 | 英一写作 + 408数据结构算法 | {date_text}"
    body = generate_body(date_text, topic)
    send_email(subject, body)
    print(f"sent: {subject}")


if __name__ == "__main__":
    main()
