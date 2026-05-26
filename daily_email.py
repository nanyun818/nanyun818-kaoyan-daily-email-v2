import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from zoneinfo import ZoneInfo

from openai import OpenAI


TIMEZONE = "Asia/Shanghai"
DEFAULT_MODEL = "gpt-4.1-mini"

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
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
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
    client = OpenAI(api_key=require_env("OPENAI_API_KEY"))
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL") or DEFAULT_MODEL,
        input=build_prompt(date_text, topic),
    )
    body = response.output_text.strip()
    if not body:
        raise RuntimeError("OpenAI returned an empty response.")
    return body


def send_email(subject: str, body: str) -> None:
    gmail_user = require_env("GMAIL_USER")
    gmail_password = require_env("GMAIL_APP_PASSWORD").replace(" ", "")
    to_email = require_env("TO_EMAIL")

    message = EmailMessage()
    message["From"] = gmail_user
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(gmail_user, gmail_password)
        smtp.send_message(message)


def main() -> None:
    date_text, topic = today_info()
    subject = f"考研每日积累 | 英一写作 + 408数据结构算法 | {date_text}"
    body = generate_body(date_text, topic)
    send_email(subject, body)
    print(f"sent: {subject}")


if __name__ == "__main__":
    main()
