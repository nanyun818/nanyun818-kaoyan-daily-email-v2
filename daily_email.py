import html
import json
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from typing import Any
from zoneinfo import ZoneInfo

from openai import OpenAI


TIMEZONE = "Asia/Shanghai"
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"

MATH_TOPICS = [
    "高等数学：极限、连续、等价无穷小与洛必达法则",
    "高等数学：一元函数微分学、单调性、极值与凹凸性",
    "高等数学：一元函数积分学、变限积分与反常积分",
    "高等数学：多元函数微分学、偏导、全微分与条件极值",
    "高等数学：二重积分、三重积分、曲线曲面积分的基本思想",
    "线性代数：行列式、矩阵初等变换与矩阵秩",
    "线性代数：向量组线性相关、方程组与基础解系",
    "线性代数：特征值、特征向量、相似对角化与二次型",
    "概率论：随机事件、条件概率、独立性与全概率公式",
    "概率论：随机变量分布、数字特征与常见分布",
]

DS_TOPICS = [
    "线性表与链表指针调整",
    "栈、队列与递归/表达式/遍历应用",
    "二叉树、线索树、堆与平衡思想",
    "图的遍历、连通性、最短路径与最小生成树",
    "查找、散列表与平均查找长度",
    "排序算法、稳定性、复杂度与过程分析",
    "综合算法设计与数据结构不变量",
]

CS408_TOPICS = [
    "数据结构：逻辑结构、存储结构与算法复杂度",
    "计算机组成原理：数据表示、运算器、存储层次与指令系统",
    "操作系统：进程线程、调度、同步互斥、内存管理与文件系统",
    "计算机网络：分层模型、可靠传输、路由、拥塞控制与应用层协议",
]


def clean_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    prefix = f"{name}="
    if value.startswith(prefix):
        value = value[len(prefix):].strip()
    return value


def require_env(name: str) -> str:
    value = clean_env(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def today_info() -> tuple[str, str, str]:
    now = datetime.now(ZoneInfo(TIMEZONE))
    day_index = now.timetuple().tm_yday - 1
    date_text = now.strftime("%Y-%m-%d")
    math_topic = MATH_TOPICS[day_index % len(MATH_TOPICS)]
    ds_topic = DS_TOPICS[day_index % len(DS_TOPICS)]
    return date_text, math_topic, ds_topic


def build_prompt(date_text: str, math_topic: str, ds_topic: str) -> str:
    return f"""
请生成一封中文每日考研积累邮件的数据内容，日期：{date_text}。

请只输出合法 JSON，不要 Markdown 代码块，不要额外解释。内容要紧凑、实用、适合每天阅读。

内容结构要求：
1. 英语一写作例句只给2到3句，必须少而精。
2. 增加考研数学知识点，围绕基础阶段常见框架，可参考“张宇基础三十讲”覆盖的典型知识范围，但不要引用、复刻或改写教材原文和原题。
3. 增加408专业课四门知识点：数据结构、计算机组成原理、操作系统、计算机网络，每门各给1个小知识点。
4. 保留408数据结构算法每日一题，但篇幅适中。
5. 不要编造真实考试年份、页码或教材原句。

今日数学主题倾向：{math_topic}
今日数据结构算法主题倾向：{ds_topic}
408四门覆盖范围参考：{"；".join(CS408_TOPICS)}

JSON 格式必须完全匹配：
{{
  "lead": "今天适合先看什么、抓住什么，1句话",
  "english": [
    {{
      "sentence": "英文例句",
      "translation": "中文翻译",
      "usage": "使用场景，1句话"
    }}
  ],
  "imitation": "1个英语仿写练习",
  "math": [
    {{
      "topic": "数学知识点标题",
      "point": "核心结论或理解，2到3句话",
      "formula": "必要公式，没有则写空字符串",
      "mistake": "常见误区，1句话"
    }}
  ],
  "cs408": [
    {{
      "course": "数据结构",
      "point": "知识点标题",
      "explanation": "核心理解，2到3句话",
      "exam_hint": "做题提醒，1句话"
    }},
    {{
      "course": "计算机组成原理",
      "point": "知识点标题",
      "explanation": "核心理解，2到3句话",
      "exam_hint": "做题提醒，1句话"
    }},
    {{
      "course": "操作系统",
      "point": "知识点标题",
      "explanation": "核心理解，2到3句话",
      "exam_hint": "做题提醒，1句话"
    }},
    {{
      "course": "计算机网络",
      "point": "知识点标题",
      "explanation": "核心理解，2到3句话",
      "exam_hint": "做题提醒，1句话"
    }}
  ],
  "algorithm": {{
    "title": "408数据结构算法题标题",
    "problem": "题目描述",
    "idea": "关键思路",
    "pseudocode": "C/C++风格伪代码",
    "complexity": "时间复杂度和空间复杂度",
    "example": "小样例",
    "pitfalls": ["易错点1", "易错点2"]
  }},
  "daily_task": "今天收尾练习，1句话"
}}

数量要求：
- english 数组必须是2到3项。
- math 数组必须是2项。
- cs408 数组必须是4项，且四门课各1项。
- pitfalls 数组必须是2到3项。
""".strip()


def parse_json_response(content: str) -> dict[str, Any]:
    content = content.strip()
    if content.startswith("```"):
        lines = content.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise RuntimeError(f"DeepSeek did not return JSON: {content[:300]}")

    return json.loads(content[start : end + 1])


def generate_payload(date_text: str, math_topic: str, ds_topic: str) -> dict[str, Any]:
    client = OpenAI(
        api_key=require_env("DEEPSEEK_API_KEY"),
        base_url=clean_env("DEEPSEEK_BASE_URL") or DEFAULT_DEEPSEEK_BASE_URL,
    )
    response = client.chat.completions.create(
        model=clean_env("DEEPSEEK_MODEL") or DEFAULT_DEEPSEEK_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a precise Chinese study coach for postgraduate entrance exam preparation. Return valid JSON only.",
            },
            {"role": "user", "content": build_prompt(date_text, math_topic, ds_topic)},
        ],
        temperature=0.7,
        stream=False,
        extra_body={"thinking": {"type": "disabled"}},
    )
    content = (response.choices[0].message.content or "").strip()
    if not content:
        raise RuntimeError("DeepSeek returned an empty response.")
    return parse_json_response(content)


def as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def render_text(payload: dict[str, Any], date_text: str) -> str:
    lines = [
        f"考研每日积累 | {date_text}",
        "",
        as_text(payload.get("lead")),
        "",
        "一、英语一写作例句",
    ]
    for item in payload.get("english", []):
        lines.extend(
            [
                f"- {as_text(item.get('sentence'))}",
                f"  译：{as_text(item.get('translation'))}",
                f"  用法：{as_text(item.get('usage'))}",
            ]
        )
    lines.extend(["", f"仿写：{as_text(payload.get('imitation'))}", "", "二、数学知识点"])
    for item in payload.get("math", []):
        lines.extend(
            [
                f"- {as_text(item.get('topic'))}",
                f"  {as_text(item.get('point'))}",
                f"  公式：{as_text(item.get('formula'))}",
                f"  易错：{as_text(item.get('mistake'))}",
            ]
        )

    lines.extend(["", "三、408四门知识点"])
    for item in payload.get("cs408", []):
        lines.extend(
            [
                f"- {as_text(item.get('course'))}：{as_text(item.get('point'))}",
                f"  {as_text(item.get('explanation'))}",
                f"  提醒：{as_text(item.get('exam_hint'))}",
            ]
        )

    algo = payload.get("algorithm", {})
    lines.extend(
        [
            "",
            "四、408数据结构算法每日一题",
            as_text(algo.get("title")),
            as_text(algo.get("problem")),
            f"思路：{as_text(algo.get('idea'))}",
            f"伪代码：\n{as_text(algo.get('pseudocode'))}",
            f"复杂度：{as_text(algo.get('complexity'))}",
            f"样例：{as_text(algo.get('example'))}",
            "易错点：",
        ]
    )
    for pitfall in algo.get("pitfalls", []):
        lines.append(f"- {as_text(pitfall)}")
    lines.extend(["", f"今日收尾：{as_text(payload.get('daily_task'))}"])
    return "\n".join(lines)


def h(value: Any) -> str:
    return html.escape(as_text(value))


def render_html(payload: dict[str, Any], date_text: str) -> str:
    english_cards = "\n".join(
        f"""
        <div class="item">
          <p class="en">{h(item.get("sentence"))}</p>
          <p><span>译</span>{h(item.get("translation"))}</p>
          <p><span>用法</span>{h(item.get("usage"))}</p>
        </div>
        """
        for item in payload.get("english", [])
    )

    math_cards = "\n".join(
        f"""
        <div class="item">
          <h3>{h(item.get("topic"))}</h3>
          <p>{h(item.get("point"))}</p>
          {f'<p><span>公式</span><code>{h(item.get("formula"))}</code></p>' if as_text(item.get("formula")) else ""}
          <p><span>易错</span>{h(item.get("mistake"))}</p>
        </div>
        """
        for item in payload.get("math", [])
    )

    cs_cards = "\n".join(
        f"""
        <div class="item compact">
          <p class="course">{h(item.get("course"))}</p>
          <h3>{h(item.get("point"))}</h3>
          <p>{h(item.get("explanation"))}</p>
          <p><span>提醒</span>{h(item.get("exam_hint"))}</p>
        </div>
        """
        for item in payload.get("cs408", [])
    )

    algo = payload.get("algorithm", {})
    pitfalls = "\n".join(f"<li>{h(pitfall)}</li>" for pitfall in algo.get("pitfalls", []))

    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ margin: 0; background: #f4f6f8; color: #17202a; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, "Microsoft YaHei", sans-serif; }}
    .wrap {{ max-width: 760px; margin: 0 auto; padding: 24px 14px; }}
    .hero {{ background: #1f6f5b; color: #fff; border-radius: 14px; padding: 22px 24px; }}
    .hero h1 {{ margin: 0 0 8px; font-size: 24px; line-height: 1.3; }}
    .hero p {{ margin: 0; line-height: 1.7; color: #eaf6f1; }}
    .section {{ margin-top: 16px; background: #fff; border: 1px solid #e4e8ee; border-radius: 12px; padding: 18px 20px; }}
    .section h2 {{ margin: 0 0 12px; font-size: 18px; color: #143d35; }}
    .item {{ border-top: 1px solid #edf0f3; padding: 13px 0; }}
    .item:first-of-type {{ border-top: 0; padding-top: 0; }}
    .item h3 {{ margin: 0 0 8px; font-size: 16px; color: #1f2937; }}
    .item p {{ margin: 6px 0; line-height: 1.75; }}
    .en {{ font-size: 16px; font-weight: 650; color: #0f513f; }}
    .course {{ display: inline-block; margin: 0 0 6px; padding: 3px 8px; border-radius: 999px; background: #eaf6f1; color: #1f6f5b; font-size: 12px; font-weight: 700; }}
    span {{ display: inline-block; margin-right: 8px; padding: 2px 7px; border-radius: 6px; background: #f0f3f5; color: #46505a; font-size: 12px; font-weight: 700; }}
    code, pre {{ font-family: "Cascadia Mono", Consolas, monospace; }}
    code {{ background: #f6f8fa; padding: 2px 5px; border-radius: 5px; }}
    pre {{ white-space: pre-wrap; background: #101828; color: #e6edf3; border-radius: 10px; padding: 14px; line-height: 1.55; overflow-x: auto; }}
    ul {{ margin: 8px 0 0 20px; padding: 0; line-height: 1.75; }}
    .task {{ background: #fff7e6; border-color: #f5d7a1; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <h1>考研每日积累</h1>
      <p>{h(date_text)} · 英一写作 + 数学 + 408</p>
      <p>{h(payload.get("lead"))}</p>
    </div>

    <div class="section">
      <h2>一、英语一写作例句</h2>
      {english_cards}
      <div class="item"><p><span>仿写</span>{h(payload.get("imitation"))}</p></div>
    </div>

    <div class="section">
      <h2>二、数学知识点</h2>
      {math_cards}
    </div>

    <div class="section">
      <h2>三、408四门知识点</h2>
      {cs_cards}
    </div>

    <div class="section">
      <h2>四、408数据结构算法每日一题</h2>
      <div class="item">
        <h3>{h(algo.get("title"))}</h3>
        <p>{h(algo.get("problem"))}</p>
        <p><span>思路</span>{h(algo.get("idea"))}</p>
        <pre>{h(algo.get("pseudocode"))}</pre>
        <p><span>复杂度</span>{h(algo.get("complexity"))}</p>
        <p><span>样例</span>{h(algo.get("example"))}</p>
        <p><span>易错点</span></p>
        <ul>{pitfalls}</ul>
      </div>
    </div>

    <div class="section task">
      <h2>今日收尾</h2>
      <p>{h(payload.get("daily_task"))}</p>
    </div>
  </div>
</body>
</html>"""


def send_email(subject: str, text_body: str, html_body: str) -> None:
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
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP_SSL(smtp_host, smtp_port) as smtp:
        smtp.login(smtp_user, smtp_password)
        smtp.send_message(message)


def main() -> None:
    date_text, math_topic, ds_topic = today_info()
    subject = f"考研每日积累 | 英一 + 数学 + 408 | {date_text}"
    payload = generate_payload(date_text, math_topic, ds_topic)
    send_email(subject, render_text(payload, date_text), render_html(payload, date_text))
    print(f"sent: {subject}")


if __name__ == "__main__":
    main()
