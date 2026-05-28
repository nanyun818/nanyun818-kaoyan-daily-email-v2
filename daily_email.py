import html
import hashlib
import json
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from openai import OpenAI


TIMEZONE = "Asia/Shanghai"
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"
HISTORY_PATH = Path(__file__).with_name("sent_history.json")
HISTORY_LIMIT = 14

ENGLISH_THEMES = [
    "教育公平与终身学习",
    "科技便利与责任边界",
    "环境保护与绿色生活",
    "文化传承与开放交流",
    "青年责任与社会参与",
    "公共道德与规则意识",
    "理性消费与价值选择",
    "健康生活与自我管理",
    "城乡发展与社会进步",
    "志愿服务与互助精神",
]

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

DS_ALGORITHM_TOPICS = [
    "单链表稳定划分：小于x与不小于x的结点分区",
    "顺序表原地删除：删除所有值在区间[s,t]内的元素",
    "双栈共享空间：判断栈满、入栈和出栈边界",
    "循环队列应用：用队列实现层序遍历并统计树宽度",
    "二叉树递归算法：求树中度为2的结点个数",
    "二叉树非递归遍历：中序遍历判断二叉排序树",
    "图的遍历：基于DFS判断无向图是否连通",
    "图的最短路径：Dijkstra过程与路径恢复",
    "拓扑排序：判断有向图是否存在环",
    "散列表：线性探测插入与查找成功/失败长度分析",
    "堆排序：建堆过程、筛选调整与第k大元素",
    "快速排序：一次划分过程与递归边界",
    "归并排序：有序子表合并与稳定性分析",
    "并查集：统计无向图连通分量个数",
]

CS408_TOPIC_BANKS = {
    "数据结构": [
        "算法时间复杂度与空间复杂度的数量级判断",
        "顺序表插入删除的移动次数分析",
        "单链表头插、尾插与指针断链风险",
        "栈在括号匹配和表达式求值中的应用",
        "循环队列队空、队满与元素个数计算",
        "二叉树三种遍历序列的还原条件",
        "二叉排序树查找路径与平均查找长度",
        "图的邻接矩阵与邻接表空间复杂度比较",
        "最小生成树Kruskal与Prim适用场景",
        "折半查找判定树与查找失败结点",
        "散列冲突处理与装填因子影响",
        "直接插入排序与希尔排序的过程差异",
        "快速排序最坏情况与划分策略",
        "归并排序稳定性与辅助空间",
    ],
    "计算机组成原理": [
        "补码表示范围与溢出判断",
        "浮点数规格化、阶码和尾数含义",
        "定点乘除法的符号位处理",
        "ALU、通用寄存器与数据通路",
        "指令格式中的操作码和地址码",
        "寻址方式：立即、直接、间接、寄存器间接",
        "CISC与RISC指令系统差异",
        "CPU周期、机器周期与时钟周期",
        "微程序控制器与硬布线控制器",
        "Cache映射方式：直接、全相联、组相联",
        "主存与Cache一致性、命中率和平均访问时间",
        "虚拟存储器地址转换与TLB作用",
        "I/O中断方式与DMA方式区别",
        "总线仲裁、总线周期与带宽计算",
    ],
    "操作系统": [
        "进程与线程的资源拥有关系",
        "进程状态转换和调度时机",
        "先来先服务、短作业优先和时间片轮转",
        "信号量P/V操作解决同步互斥",
        "生产者消费者问题中的空缓冲区和满缓冲区",
        "死锁四个必要条件与银行家算法",
        "连续分配、分页、分段与段页式管理",
        "页表、快表TLB与有效访问时间",
        "页面置换算法FIFO、LRU、Clock",
        "工作集与抖动现象",
        "文件逻辑结构与物理结构",
        "目录结构、FCB与索引结点",
        "磁盘调度FCFS、SSTF、SCAN和CSCAN",
        "设备独立性、缓冲区和SPOOLing技术",
    ],
    "计算机网络": [
        "OSI与TCP/IP分层模型对应关系",
        "物理层编码、带宽、波特率与比特率",
        "数据链路层成帧、差错控制与CRC",
        "CSMA/CD与以太网最小帧长",
        "交换机自学习和转发表建立",
        "IP地址分类、子网划分与CIDR",
        "ARP协议地址解析过程",
        "路由选择：距离向量与链路状态",
        "ICMP报文和ping/traceroute应用",
        "UDP无连接特性与应用场景",
        "TCP三次握手和四次挥手",
        "TCP可靠传输：序号、确认、重传",
        "TCP流量控制与滑动窗口",
        "拥塞控制：慢开始、拥塞避免、快重传、快恢复",
    ],
}

ENGLISH_BANNED_TERMS = [
    "determinant",
    "matrix",
    "linear algebra",
    "calculus",
    "integral",
    "derivative",
    "eigen",
    "vector",
    "rank",
    "algorithm",
    "data structure",
    "stack",
    "queue",
    "binary tree",
    "operating system",
    "computer organization",
    "computer network",
    "cpu",
    "cache",
    "408",
    "行列式",
    "矩阵",
    "线性代数",
    "微积分",
    "积分",
    "导数",
    "特征值",
    "向量",
    "秩",
    "算法",
    "数据结构",
    "栈",
    "队列",
    "二叉树",
    "操作系统",
    "计算机组成",
    "计算机网络",
    "powerful weapon",
    "change the world",
    "as the saying goes",
    "proverb",
    "famous quote",
    "名言",
    "谚语",
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


def today_info() -> tuple[str, dict[str, Any]]:
    now = datetime.now(ZoneInfo(TIMEZONE))
    day_index = now.timetuple().tm_yday - 1
    date_text = now.strftime("%Y-%m-%d")
    plan = {
        "english_theme": ENGLISH_THEMES[day_index % len(ENGLISH_THEMES)],
        "math_topics": [
            MATH_TOPICS[day_index % len(MATH_TOPICS)],
            MATH_TOPICS[(day_index + 4) % len(MATH_TOPICS)],
        ],
        "cs408_topics": {
            course: topics[(day_index + offset * 3) % len(topics)]
            for offset, (course, topics) in enumerate(CS408_TOPIC_BANKS.items())
        },
        "ds_algorithm_topic": DS_ALGORITHM_TOPICS[day_index % len(DS_ALGORITHM_TOPICS)],
    }
    return date_text, plan


def build_prompt(
    date_text: str,
    plan: dict[str, Any],
    history_context: str,
    retry_reason: str = "",
) -> str:
    retry_note = f"\n上一次输出需要修正的问题：{retry_reason}\n请严格修正后重新输出合法 JSON。" if retry_reason else ""
    date_seed = date_text.replace("-", "")
    return f"""
请生成一封中文每日考研积累邮件的数据内容，日期：{date_text}。

请只输出合法 JSON，不要 Markdown 代码块，不要额外解释。内容要紧凑、实用、适合每天阅读。

内容结构要求：
1. 英语一写作例句只给2到3句，必须少而精。
2. 英语例句必须是考研英语一作文可复用句，围绕教育、科技影响、环境保护、文化传承、青年责任、公共道德、消费观、健康、社会发展等常见作文主题；禁止写数学、408、算法、计算机专业课、矩阵、行列式、代码等内容。
   英语例句必须是原创的论证功能句，适合考研英语一大作文，不要名人名言、谚语、鸡汤句、过度文学化句子或具体学科知识句。
3. 增加考研数学知识点，围绕基础阶段常见框架，可参考“张宇基础三十讲”覆盖的典型知识范围，但不要引用、复刻或改写教材原文和原题。
4. 增加408专业课四门知识点：数据结构、计算机组成原理、操作系统、计算机网络，每门各给1个小知识点。
5. 保留408数据结构算法每日一题，但篇幅适中。
6. 不要编造真实考试年份、页码或教材原句。
7. 每天内容必须不同。不要复用历史中的英语句子、数学知识点标题、408知识点标题、算法题标题或相同题型。

今日日期种子：{date_seed}
今日英语作文主题：{plan["english_theme"]}
今日数学指定主题：{"；".join(plan["math_topics"])}
今日408四门指定知识点：
{"；".join(f"{course}：{topic}" for course, topic in plan["cs408_topics"].items())}
今日数据结构算法大题指定方向：{plan["ds_algorithm_topic"]}

最近已发送内容摘要，今天必须避开：
{history_context or "暂无历史记录。"}

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
- math 数组必须是2项，且必须分别对应“今日数学指定主题”的两个主题。
- cs408 数组必须是4项，且四门课各1项；每项必须对应“今日408四门指定知识点”。
- algorithm 必须对应“今日数据结构算法大题指定方向”，不得改成其他链表/树/图/排序题型。
- pitfalls 数组必须是2到3项。
{retry_note}
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


def payload_fingerprint(payload: dict[str, Any]) -> str:
    normalized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def load_history() -> list[dict[str, Any]]:
    if not HISTORY_PATH.exists():
        return []
    try:
        data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def save_history(date_text: str, payload: dict[str, Any]) -> None:
    history = load_history()
    history.append(summarize_payload(date_text, payload))
    HISTORY_PATH.write_text(
        json.dumps(history[-HISTORY_LIMIT:], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def summarize_payload(date_text: str, payload: dict[str, Any]) -> dict[str, Any]:
    algo = payload.get("algorithm", {})
    return {
        "date": date_text,
        "fingerprint": payload_fingerprint(payload),
        "english": [as_text(item.get("sentence")) for item in payload.get("english", [])],
        "math_topics": [as_text(item.get("topic")) for item in payload.get("math", [])],
        "cs408_points": [
            f"{as_text(item.get('course'))}:{as_text(item.get('point'))}"
            for item in payload.get("cs408", [])
        ],
        "algorithm_title": as_text(algo.get("title")),
        "algorithm_problem": as_text(algo.get("problem"))[:180],
    }


def format_history_context(history: list[dict[str, Any]], max_items: int = 7) -> str:
    if not history:
        return ""
    lines: list[str] = []
    for item in history[-max_items:]:
        lines.extend(
            [
                f"- 日期：{as_text(item.get('date'))}",
                f"  英语：{' / '.join(as_text(x) for x in item.get('english', []))}",
                f"  数学：{' / '.join(as_text(x) for x in item.get('math_topics', []))}",
                f"  408：{' / '.join(as_text(x) for x in item.get('cs408_points', []))}",
                f"  算法：{as_text(item.get('algorithm_title'))}",
            ]
        )
    return "\n".join(lines)


def norm_key(value: Any) -> str:
    return "".join(ch for ch in as_text(value).lower() if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")


def validate_payload(payload: dict[str, Any], history: list[dict[str, Any]], plan: dict[str, Any]) -> None:
    english_items = payload.get("english", [])
    if not 2 <= len(english_items) <= 3:
        raise ValueError("英语例句数量必须是2到3句。")

    for item in english_items:
        combined = " ".join(
            [
                as_text(item.get("sentence")),
                as_text(item.get("translation")),
                as_text(item.get("usage")),
            ]
        ).lower()
        hits = [term for term in ENGLISH_BANNED_TERMS if term.lower() in combined]
        if hits:
            raise ValueError(f"英语例句混入了数学/408/计算机内容：{', '.join(hits[:3])}")

    fingerprint = payload_fingerprint(payload)
    for item in history[-HISTORY_LIMIT:]:
        if as_text(item.get("fingerprint")) == fingerprint:
            raise ValueError("生成结果与历史邮件完全重复。")

    previous_english = {
        as_text(sentence).lower()
        for item in history[-7:]
        for sentence in item.get("english", [])
        if as_text(sentence)
    }
    current_english = {
        as_text(item.get("sentence")).lower()
        for item in english_items
        if as_text(item.get("sentence"))
    }
    repeated_english = previous_english.intersection(current_english)
    if repeated_english:
        raise ValueError("英语例句与最近历史重复。")

    math_items = payload.get("math", [])
    if len(math_items) != 2:
        raise ValueError("数学知识点必须是2项。")
    current_math_topics = [as_text(item.get("topic")) for item in math_items]
    previous_math_topics = {
        norm_key(topic)
        for item in history[-7:]
        for topic in item.get("math_topics", [])
        if norm_key(topic)
    }
    if previous_math_topics.intersection(norm_key(topic) for topic in current_math_topics):
        raise ValueError("数学知识点标题与最近历史重复。")

    cs408_items = payload.get("cs408", [])
    if len(cs408_items) != 4:
        raise ValueError("408知识点必须是4项。")
    expected_courses = set(CS408_TOPIC_BANKS)
    current_courses = {as_text(item.get("course")) for item in cs408_items}
    if current_courses != expected_courses:
        raise ValueError("408知识点必须覆盖数据结构、计算机组成原理、操作系统、计算机网络四门。")

    current_cs408_points = [
        f"{as_text(item.get('course'))}:{as_text(item.get('point'))}"
        for item in cs408_items
    ]
    previous_cs408_points = {
        norm_key(point)
        for item in history[-7:]
        for point in item.get("cs408_points", [])
        if norm_key(point)
    }
    if previous_cs408_points.intersection(norm_key(point) for point in current_cs408_points):
        raise ValueError("408四门知识点与最近历史重复。")

    previous_algo_titles = {
        as_text(item.get("algorithm_title")).lower()
        for item in history[-7:]
        if as_text(item.get("algorithm_title"))
    }
    current_algo_title = as_text(payload.get("algorithm", {}).get("title")).lower()
    if current_algo_title and current_algo_title in previous_algo_titles:
        raise ValueError("算法题标题与最近历史重复。")

    expected_fragments = [
        plan["english_theme"],
        *plan["math_topics"],
        *plan["cs408_topics"].values(),
        plan["ds_algorithm_topic"],
    ]
    if not all(as_text(fragment) for fragment in expected_fragments):
        raise ValueError("每日题单不完整。")


def generate_payload(
    date_text: str,
    plan: dict[str, Any],
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    client = OpenAI(
        api_key=require_env("DEEPSEEK_API_KEY"),
        base_url=clean_env("DEEPSEEK_BASE_URL") or DEFAULT_DEEPSEEK_BASE_URL,
    )
    retry_reason = ""
    history_context = format_history_context(history)
    for attempt in range(3):
        response = client.chat.completions.create(
            model=clean_env("DEEPSEEK_MODEL") or DEFAULT_DEEPSEEK_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise Chinese study coach for postgraduate entrance exam preparation. Return valid JSON only. Keep English I writing examples unrelated to math, algorithms, and computer science.",
                },
                {
                    "role": "user",
                    "content": build_prompt(
                        date_text,
                        plan,
                        history_context,
                        retry_reason,
                    ),
                },
            ],
            temperature=0.7,
            stream=False,
            extra_body={"thinking": {"type": "disabled"}},
        )
        content = (response.choices[0].message.content or "").strip()
        if not content:
            raise RuntimeError("DeepSeek returned an empty response.")
        payload = parse_json_response(content)
        try:
            validate_payload(payload, history, plan)
            return payload
        except ValueError as exc:
            retry_reason = str(exc)
            if attempt == 2:
                raise

    raise RuntimeError("DeepSeek failed to produce a valid daily email payload.")


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
    date_text, plan = today_info()
    subject_suffix = clean_env("EMAIL_SUBJECT_SUFFIX") or ""
    subject = f"考研每日积累 | 英一 + 数学 + 408 | {date_text}{subject_suffix}"
    history = load_history()
    payload = generate_payload(date_text, plan, history)
    send_email(subject, render_text(payload, date_text), render_html(payload, date_text))
    save_history(date_text, payload)
    print(f"sent: {subject}")


if __name__ == "__main__":
    main()
