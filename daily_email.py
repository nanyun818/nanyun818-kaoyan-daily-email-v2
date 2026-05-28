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
PLAN_START_DATE = datetime(2026, 5, 26, tzinfo=ZoneInfo(TIMEZONE)).date()

ENGLISH_BASE_THEMES = [
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
    "网络文明与信息辨别",
    "人工智能与人的主动性",
    "学术诚信与独立思考",
    "就业选择与个人成长",
    "挫折教育与心理韧性",
    "家庭教育与代际沟通",
    "阅读习惯与知识积累",
    "传统节日与文化自信",
    "公共交通与城市治理",
    "节约资源与反对浪费",
    "规则意识与社会秩序",
    "团队合作与个人能力",
    "数字生活与时间管理",
    "创新精神与实践能力",
    "社会责任与职业伦理",
    "媒体素养与理性表达",
    "体育锻炼与全面发展",
    "乡村振兴与青年参与",
    "志愿服务与社区建设",
    "全球视野与本土文化",
]

ENGLISH_THEME_MODES = ["现象描述", "原因分析", "利弊对比", "措施建议", "总结升华", "图画评论", "图表描述"]
ENGLISH_THEMES = [f"{theme}｜{mode}" for theme in ENGLISH_BASE_THEMES for mode in ENGLISH_THEME_MODES]

MATH_BASE_TOPICS = [
    "高数-极限：常用等价无穷小 sinx~x, tanx~x, 1-cosx~x²/2",
    "高数-极限：ln(1+x)~x, e^x-1~x, (1+x)^α-1~αx",
    "高数-极限：x→0时 arcsin x~x, arctan x~x, a^x-1~x ln a",
    "高数-极限：夹逼准则与重要极限 lim(sinx/x)=1",
    "高数-极限：第二重要极限 lim(1+1/x)^x=e",
    "高数-极限：数列极限、单调有界准则与递推数列",
    "高数-连续：间断点分类，可去、跳跃、无穷、振荡",
    "高数-连续：闭区间连续函数性质，最值、介值、零点",
    "高数-导数：复合函数链式法则 dy/dx=(dy/du)(du/dx)",
    "高数-导数：反函数求导 (f^{-1})'(y)=1/f'(x)",
    "高数-导数：隐函数求导 F(x,y)=0 时 dy/dx=-F_x/F_y",
    "高数-导数：参数方程求导 dy/dx=(dy/dt)/(dx/dt)",
    "高数-导数：对数求导，适合 y=u(x)^v(x)",
    "高数-导数：常用导数 (arcsin x)'=1/√(1-x²)",
    "高数-导数：常用导数 (arctan x)'=1/(1+x²)",
    "高数-导数：常用导数 (a^x)'=a^x ln a, (ln|x|)'=1/x",
    "高数-泰勒：e^x=1+x+x²/2!+x³/3!+o(x³)",
    "高数-泰勒：sinx=x-x³/3!+x⁵/5!+o(x⁵)",
    "高数-泰勒：cosx=1-x²/2!+x⁴/4!+o(x⁴)",
    "高数-泰勒：ln(1+x)=x-x²/2+x³/3+o(x³)",
    "高数-泰勒：(1+x)^α=1+αx+α(α-1)x²/2+o(x²)",
    "高数-泰勒：arctanx=x-x³/3+x⁵/5+o(x⁵)",
    "高数-中值定理：Rolle定理条件 f(a)=f(b)",
    "高数-中值定理：Lagrange公式 f(b)-f(a)=f'(ξ)(b-a)",
    "高数-中值定理：Cauchy中值定理与比值型证明",
    "高数-中值定理：Taylor公式余项与近似计算",
    "高数-微分应用：单调性由 f'(x) 符号判断",
    "高数-微分应用：极值点必要条件 f'(x0)=0 或不可导",
    "高数-微分应用：凹凸性由 f''(x) 符号判断",
    "高数-微分应用：拐点需函数凹凸性改变",
    "高数-微分应用：渐近线，水平、垂直、斜渐近线",
    "高数-不定积分：基本公式 ∫1/(1+x²)dx=arctanx+C",
    "高数-不定积分：基本公式 ∫1/√(1-x²)dx=arcsinx+C",
    "高数-不定积分：基本公式 ∫sec²x dx=tanx+C",
    "高数-不定积分：换元积分，凑微分与三角换元",
    "高数-不定积分：分部积分 ∫u dv=uv-∫v du",
    "高数-不定积分：有理函数积分，拆分与待定系数",
    "高数-定积分：牛顿莱布尼茨公式 ∫_a^b f(x)dx=F(b)-F(a)",
    "高数-定积分：奇偶对称 ∫_{-a}^a 奇函数=0",
    "高数-定积分：区间再现公式 ∫_0^a f(x)dx=∫_0^a f(a-x)dx",
    "高数-定积分：周期函数定积分与整周期面积",
    "高数-定积分：变上限积分 F'(x)=f(x)",
    "高数-定积分：反常积分 p判别 ∫_1^∞ 1/x^p 收敛当 p>1",
    "高数-定积分：反常积分 ∫_0^1 1/x^p 收敛当 p<1",
    "高数-定积分应用：面积、体积、弧长与旋转体",
    "高数-微分方程：可分离变量 y'=g(x)h(y)",
    "高数-微分方程：一阶线性 y'+p(x)y=q(x)",
    "高数-微分方程：二阶常系数齐次特征方程",
    "高数-多元微分：偏导数、连续、可微之间关系",
    "高数-多元微分：全微分 dz=f_x dx+f_y dy",
    "高数-多元微分：复合函数求偏导的链式法则",
    "高数-多元微分：隐函数存在定理与偏导公式",
    "高数-多元微分：方向导数与梯度 grad f",
    "高数-多元微分：无条件极值判别 AC-B²",
    "高数-多元微分：条件极值与拉格朗日乘数法",
    "高数-二重积分：直角坐标换序与区域画图",
    "高数-二重积分：极坐标 dσ=r dr dθ",
    "高数-二重积分：对称性简化奇偶函数积分",
    "高数-三重积分：柱坐标、球坐标与雅可比",
    "高数-曲线积分：第一类曲线积分 ds",
    "高数-曲线积分：第二类曲线积分 Pdx+Qdy",
    "高数-曲线积分：Green公式与区域正向边界",
    "高数-曲面积分：第一类曲面积分 dS",
    "高数-曲面积分：第二类曲面积分与方向余弦",
    "高数-无穷级数：正项级数比较判别法",
    "高数-无穷级数：比值判别法 ρ=lim|u_{n+1}/u_n|",
    "高数-无穷级数：交错级数莱布尼茨判别",
    "高数-无穷级数：绝对收敛与条件收敛",
    "高数-幂级数：收敛半径 R=1/lim|a_{n+1}/a_n|",
    "高数-幂级数：逐项求导与逐项积分",
    "线代-行列式：交换两行变号、倍加不变、提倍数",
    "线代-行列式：上三角行列式等于主对角线乘积",
    "线代-行列式：按行列展开与代数余子式",
    "线代-行列式：范德蒙德行列式 ∏(x_j-x_i)",
    "线代-矩阵：矩阵乘法不可交换 AB≠BA",
    "线代-矩阵：逆矩阵 A^{-1}=A*/|A| 条件 |A|≠0",
    "线代-矩阵：伴随矩阵 AA*=|A|E",
    "线代-矩阵：初等变换与初等矩阵",
    "线代-矩阵：分块矩阵乘法与分块对角矩阵",
    "线代-矩阵：矩阵秩 r(A) 与初等变换不变量",
    "线代-向量：线性相关与齐次方程非零解",
    "线代-向量：极大无关组、秩、维数",
    "线代-方程组：齐次方程 Ax=0 基础解系个数 n-r",
    "线代-方程组：非齐次 Ax=b 有解条件 r(A)=r(A,b)",
    "线代-方程组：通解=特解+对应齐次通解",
    "线代-特征值：|λE-A|=0 求特征值",
    "线代-特征值：不同特征值对应特征向量线性无关",
    "线代-相似：A可对角化条件 n个线性无关特征向量",
    "线代-相似：实对称矩阵必可正交对角化",
    "线代-二次型：合同变换与标准形",
    "线代-二次型：正定判别，特征值全正或顺序主子式全正",
    "概率-事件：加法公式 P(A∪B)=P(A)+P(B)-P(AB)",
    "概率-条件概率：P(A|B)=P(AB)/P(B)",
    "概率-全概率公式：P(A)=ΣP(B_i)P(A|B_i)",
    "概率-Bayes公式：P(B_i|A)=P(B_i)P(A|B_i)/ΣP(B_j)P(A|B_j)",
    "概率-独立性：P(AB)=P(A)P(B)",
    "概率-离散分布：二项分布 B(n,p), E=np, D=npq",
    "概率-离散分布：泊松分布 P(X=k)=λ^k e^{-λ}/k!",
    "概率-连续分布：均匀分布 U(a,b), E=(a+b)/2",
    "概率-连续分布：指数分布 f(x)=λe^{-λx}, E=1/λ",
    "概率-连续分布：正态分布标准化 Z=(X-μ)/σ",
    "概率-二维分布：联合、边缘、条件分布",
    "概率-数字特征：E(aX+b)=aEX+b",
    "概率-数字特征：D(aX+b)=a²DX",
    "概率-协方差：Cov(X,Y)=E(XY)-EXEY",
    "概率-相关系数：ρ=Cov/(σ_X σ_Y)",
    "概率-大数定律：样本均值依概率收敛",
    "概率-中心极限定理：标准化和趋近 N(0,1)",
    "概率-统计量：样本均值、样本方差与χ²分布",
    "概率-参数估计：矩估计与最大似然估计",
    "概率-区间估计：正态总体均值置信区间",
]

MATH_REVIEW_MODES = ["公式记忆", "适用条件", "典型题入口", "易错辨析"]
MATH_TOPICS = [f"{topic}｜{mode}" for topic in MATH_BASE_TOPICS for mode in MATH_REVIEW_MODES]

DS_ALGORITHM_BASE_TOPICS = [
    "顺序表删除所有值为x的元素",
    "顺序表删除区间[s,t]内元素",
    "顺序表两个有序表归并",
    "顺序表逆置指定区间",
    "单链表头插法逆置",
    "单链表删除最小值结点",
    "单链表稳定划分小于x与不小于x",
    "两个单链表求公共后缀起点",
    "判断单链表是否存在环并求入口",
    "双链表插入删除指针调整",
    "静态链表模拟内存分配",
    "共享栈入栈出栈与栈满判断",
    "栈实现括号匹配",
    "栈实现中缀转后缀表达式",
    "栈实现后缀表达式求值",
    "递归转非递归的显式栈模拟",
    "循环队列队空队满与元素个数",
    "队列实现二叉树层序遍历",
    "队列实现树的最大宽度统计",
    "链队列入队出队边界",
    "串的KMP next数组求解",
    "KMP模式匹配过程模拟",
    "稀疏矩阵三元组转置",
    "广义表深度递归计算",
    "二叉树先中序还原后序",
    "二叉树中后序还原层序",
    "二叉树递归求高度",
    "二叉树统计度为0/1/2的结点",
    "二叉树判断是否为完全二叉树",
    "二叉树非递归先序遍历",
    "二叉树非递归中序遍历",
    "二叉树非递归后序遍历",
    "线索二叉树找前驱后继",
    "哈夫曼树构造与WPL计算",
    "二叉排序树插入查找删除",
    "平衡二叉树插入与旋转判断",
    "堆的插入删除与调整",
    "图的DFS遍历与连通分量统计",
    "图的BFS遍历与最短边数路径",
    "邻接表求顶点入度出度",
    "有向图判断是否存在环",
    "拓扑排序输出合法序列",
    "关键路径求最早最迟发生时间",
    "Prim算法构造最小生成树",
    "Kruskal算法构造最小生成树",
    "Dijkstra最短路径与路径恢复",
    "Floyd多源最短路径过程",
    "折半查找判定树与比较次数",
    "分块查找索引表设计",
    "散列表线性探测插入查找删除",
    "散列表链地址法平均查找长度",
    "直接插入排序过程与比较移动次数",
    "希尔排序一趟过程",
    "冒泡排序提前结束标志",
    "快速排序一次划分与递归边界",
    "简单选择排序过程与稳定性",
    "堆排序建堆与筛选",
    "归并排序合并过程",
    "基数排序分配收集过程",
    "并查集路径压缩统计连通块",
]

DS_ALGORITHM_MODES = ["完整伪代码", "边界条件", "复杂度分析", "样例演算"]
DS_ALGORITHM_TOPICS = [
    f"{topic}｜{mode}" for topic in DS_ALGORITHM_BASE_TOPICS for mode in DS_ALGORITHM_MODES
]

CS408_BASE_TOPIC_BANKS = {
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
        "逻辑结构与存储结构的对应关系",
        "抽象数据类型ADT的定义方式",
        "线性表顺序存储与链式存储优缺点",
        "双链表和循环链表的边界处理",
        "栈和队列的受限线性表本质",
        "递归调用栈与非递归算法转换",
        "串的朴素匹配与KMP复杂度差异",
        "数组压缩存储与特殊矩阵地址计算",
        "树、森林与二叉树的转换",
        "完全二叉树编号性质",
        "哈夫曼编码前缀码性质",
        "AVL树旋转类型LL/RR/LR/RL",
        "B树和B+树查找插入删除基本规则",
        "图的有向/无向、连通/强连通概念",
        "图遍历生成树与生成森林",
        "AOV网和AOE网的区别",
        "查找表静态与动态查找",
        "B树查找磁盘I/O意义",
        "排序稳定性的定义和判定",
        "内部排序与外部排序区别",
        "排序算法比较次数下界",
        "各排序算法最好/平均/最坏复杂度",
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
        "机器数与真值、原码反码补码移码",
        "定点数加减法与标志位OF/CF",
        "IEEE754浮点数格式与隐藏位",
        "浮点加减对阶、尾数运算、规格化",
        "奇偶校验、海明码与CRC差错控制",
        "存储器层次结构局部性原理",
        "SRAM与DRAM刷新差异",
        "主存地址译码与芯片扩展",
        "Cache写策略：写直达与写回",
        "Cache替换算法LRU/FIFO/随机",
        "指令流水线吞吐率、加速比与冒险",
        "数据冒险、控制冒险与结构冒险",
        "中断响应过程与中断隐指令",
        "程序查询、中断、DMA三种I/O方式",
        "DMA传送周期挪用与总线控制权",
        "总线同步通信与异步通信",
        "多级时序系统与控制信号",
        "CPU性能指标 CPI、MIPS、时钟频率",
        "指令周期数据流分析",
        "机器字长、存储字长与指令字长",
        "大端小端存储方式",
        "流水线相关与转发技术",
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
        "操作系统特征：并发、共享、虚拟、异步",
        "用户态核心态与系统调用过程",
        "进程控制块PCB包含的信息",
        "上下文切换与调度开销",
        "优先级调度与多级反馈队列",
        "临界区、互斥、同步、忙等",
        "管程机制与条件变量",
        "读者写者问题同步关系",
        "哲学家进餐问题死锁预防",
        "资源分配图与死锁检测",
        "内存连续分配首次/最佳/最坏适应",
        "基本分页地址转换与页内偏移",
        "多级页表减少页表占用",
        "分段管理的共享和保护",
        "段页式管理地址结构",
        "请求分页缺页中断处理流程",
        "Belady异常与FIFO页面置换",
        "文件打开表与文件描述符",
        "位示图和空闲链表管理外存空闲块",
        "磁盘RAID基本思想",
        "I/O软件层次结构",
        "设备分配与安全性检查",
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
        "奈奎斯特定理与香农公式",
        "数字调制ASK/FSK/PSK/QAM",
        "多路复用FDM/TDM/WDM/CDM",
        "PPP协议帧格式与透明传输",
        "滑动窗口协议GBN与SR",
        "MAC地址与以太网帧格式",
        "VLAN基本思想与广播域划分",
        "生成树协议STP作用",
        "IPv4首部字段与分片",
        "NAT地址转换过程",
        "DHCP获取IP地址流程",
        "RIP距离向量与跳数限制",
        "OSPF链路状态与Dijkstra",
        "BGP路径向量协议定位",
        "子网掩码、网络号、广播地址计算",
        "运输层端口号与套接字",
        "TCP超时重传时间估计RTT",
        "HTTP请求响应报文结构",
        "DNS递归查询与迭代查询",
        "SMTP、POP3、IMAP邮件协议区别",
        "HTTPS中TLS握手基本作用",
        "网络安全：对称加密、公钥加密、数字签名",
    ],
}

CS408_REVIEW_MODES = ["核心概念", "计算题入口", "大题步骤", "易错边界", "真题问法", "综合判断"]
CS408_TOPIC_BANKS = {
    course: [f"{topic}｜{mode}" for topic in topics for mode in CS408_REVIEW_MODES]
    for course, topics in CS408_BASE_TOPIC_BANKS.items()
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


def pick_topic(bank: list[str], study_day: int, step: int = 1, offset: int = 0) -> str:
    return bank[(study_day * step + offset) % len(bank)]


def today_info() -> tuple[str, dict[str, Any]]:
    now = datetime.now(ZoneInfo(TIMEZONE))
    study_day = max((now.date() - PLAN_START_DATE).days, 0)
    date_text = now.strftime("%Y-%m-%d")
    plan = {
        "study_day": study_day + 1,
        "english_theme": pick_topic(ENGLISH_THEMES, study_day, step=11),
        "math_topics": [
            pick_topic(MATH_TOPICS, study_day, step=31),
            pick_topic(
                MATH_TOPICS,
                study_day,
                step=31,
                offset=5,
            ),
        ],
        "cs408_topics": {
            course: pick_topic(
                topics,
                study_day,
                step=7,
                offset=offset * 37,
            )
            for offset, (course, topics) in enumerate(CS408_TOPIC_BANKS.items())
        },
        "ds_algorithm_topic": pick_topic(
            DS_ALGORITHM_TOPICS,
            study_day,
            step=7,
        ),
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
今日计划序号：第{plan["study_day"]}天
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
