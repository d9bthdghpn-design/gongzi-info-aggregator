"""
标签体系 v5 升级脚本
========================
1. ALTER TABLE 增加 news_items.topic_tags 列（幂等）
2. 重建 TagDictionary 标签字典：
   - 新增 topic 类型（31 个主题标签）
   - 重建 industry 类型（15 类，清洗脏 code）
   - 清理 v2 遗留 business 类型（deposit/loan/investment_bank/treasury/supply_chain）
   - action/area/info_type/opportunity 保留并完善 keywords
3. 规则引擎重打标所有资讯（business_category / topic_tags / industry_tags / area_tags / info_type）
4. 输出打标前后对比报告

用法：
  python upgrade_tags_v5.py          # 正常执行
  python upgrade_tags_v5.py --dry-run  # 只预览不打标
"""
import os
import sys
import json
import argparse
import re
from collections import Counter

# ============ 环境变量 ============
os.environ.setdefault("DATABASE_URL", "postgresql://postgres.sljoxgawgfdhchyibvdx:Ljz8248282%40@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres")
os.environ.setdefault("ENVIRONMENT", "production")
os.environ.setdefault("JWT_SECRET_KEY", "gOINcX8fj49sh2rUyna6W1JuBeqtFzTVMERQvKoYZPAbC7lH")
os.environ.setdefault("CORS_ORIGINS", "https://gongzi-info-aggregator.onrender.com")

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "backend"))

from sqlalchemy import text
from app.database import SessionLocal
from app.models import NewsItem, TagDictionary
from sqlalchemy.orm.attributes import flag_modified

# ============ v5 标签定义 ============

ACTION_TAGS = [
    ("bid_action", "招投标机会", "#1a56db", 0, ["招标", "投标", "采购", "中标", "磋商", "比选", "竞价"]),
    ("fin_demand", "融资需求", "#f59e0b", 1, ["融资", "发行", "定增", "发债", "并购", "重组", "募集资金"]),
    ("account_chance", "开户结算机会", "#10b981", 2, ["新设", "注册成立", "落户", "迁址", "登记设立"]),
    ("park_project", "区域产业动态", "#8b5cf6", 3, ["园区", "招商", "入驻", "产业基地", "落地", "开工", "综保区"]),
    ("policy_ref", "监管与政策", "#6b7280", 4, ["政策", "通知", "办法", "意见", "规划", "指南", "监管"]),
]

AREA_TAGS = [
    ("chaoyang", "朝阳区", "#06b6d4", 0, ["朝阳区", "朝阳", "CBD", "望京", "金盏"]),
    ("dongcheng", "东城区", "#0ea5e9", 1, ["东城区", "东城"]),
    ("tongzhou", "通州区", "#14b8a6", 2, ["通州区", "通州", "城市副中心"]),
    ("yizhuang", "亦庄经开区", "#6366f1", 3, ["北京经济技术开发区", "亦庄", "经开区", "经济开发区"]),
    ("haidian", "海淀区", "#3b82f6", 4, ["海淀区", "海淀", "上地", "中关村科技园"]),
    ("fengtai", "丰台区", "#8b5cf6", 5, ["丰台区", "丰台", "丽泽"]),
    ("beijing", "北京市级", "#2563eb", 6, ["北京市", "市级"]),
    ("national", "全国性", "#7c3aed", 7, ["全国", "国家", "中央", "央行", "部委"]),
    ("other", "其他地区", "#9ca3af", 8, []),
]

# 31 个主题标签（topic）
TOPIC_TAGS = [
    # A. 招投标场景（6）
    ("gov_procurement", "政府采购招标", "#1a56db", 0, ["政府采购", "公开招标", "招标公告", "招标文件", "招标编号"]),
    ("project_tender", "工程建设项目", "#0e7490", 1, ["工程施工", "工程建设", "施工项目", "改造工程", "装修工程", "维修工程", "市政工程"]),
    ("service_bid", "服务类采购", "#0284c7", 2, ["咨询服务", "服务项目", "维护服务", "监理服务", "物业服务", "保洁服务", "培训服务"]),
    ("it_bid", "IT与信息化采购", "#4f46e5", 3, ["信息化", "软件开发", "系统集成", "平台建设", "智慧城市", "政务系统", "智能设备"]),
    ("medical_bid", "医疗设备采购", "#0d9488", 4, ["医疗设备", "医疗器械", "医疗耗材", "试剂", "药品采购"]),
    ("single_source", "单一来源采购", "#64748b", 5, ["单一来源", "竞争性磋商", "竞争性谈判", "比选", "询价"]),
    # B. 融资资本场景（6）
    ("ipo_listing", "上市与IPO", "#d97706", 10, ["上市", "IPO", "首次公开发行", "北交所"]),
    ("private_placement", "定增再融资", "#b45309", 11, ["定向增发", "发行股票", "募集资金", "配股", "非公开发行"]),
    ("bond_financing", "债券融资", "#a16207", 12, ["发行债券", "公司债", "中期票据", "资产证券化", "ABS"]),
    ("m_a", "并购重组", "#7c2d12", 13, ["并购", "重组", "收购", "股权转让", "资产置换", "吸收合并"]),
    ("loan_demand", "信贷融资需求", "#ea580c", 14, ["贷款", "授信", "融资需求", "项目融资", "银团"]),
    ("fund_investment", "基金与股权投资", "#ca8a04", 15, ["产业基金", "投资基金", "股权投资", "战略投资", "投资意向"]),
    # C. 政策监管场景（8）
    ("monetary_policy", "货币政策", "#1d4ed8", 20, ["央行", "货币政策", "降准", "降息", "LPR", "利率调整", "存款准备金"]),
    ("financial_regulation", "金融监管", "#3730a3", 21, ["金融监管总局", "证监会", "监管要求", "合规", "处罚", "风险提示", "金融稳定"]),
    ("tax_finance_policy", "财税政策", "#166534", 22, ["税收政策", "减税", "退税", "专项资金", "预算管理", "财政政策", "政府采购政策"]),
    ("subsidy_program", "补贴申报", "#15803d", 23, ["补贴", "补助", "奖励", "申报指南", "申报通知", "资金申报", "支持资金"]),
    ("industry_planning", "产业规划", "#0f766e", 24, ["规划", "发展纲要", "实施方案", "行动计划", "十五五", "实施意见"]),
    ("innovation_policy", "科技创新政策", "#4338ca", 25, ["科技创新", "专精特新", "高新技术", "研发投入", "知识产权", "技术攻关"]),
    ("foreign_trade", "外贸跨境政策", "#0369a1", 26, ["跨境贸易", "外贸", "进出口", "外汇便利化", "自贸区", "保税"]),
    ("green_development", "绿色低碳政策", "#047857", 27, ["绿色低碳", "双碳", "节能", "环保", "绿色发展", "碳排放"]),
    # D. 园区与区域场景（4）
    ("park_settlement", "园区入驻招商", "#6d28d9", 30, ["招商引资", "入驻", "落户", "签约", "挂牌"]),
    ("platform_landing", "平台基地落地", "#7e22ce", 31, ["产业基地", "实验室", "创新中心", "产业园", "平台落地", "建成投用"]),
    ("project_launch", "重点项目开工", "#9333ea", 32, ["开工", "奠基", "启动建设", "竣工", "开工仪式"]),
    ("land_transfer", "土地出让", "#be185d", 33, ["土地出让", "地块", "国有建设用地", "招拍挂"]),
    # E. 市场与企业场景（5）
    ("enterprise_dynamics", "企业工商动态", "#0891b2", 40, ["新设", "注册成立", "增资", "迁址", "决议", "董事会"]),
    ("economic_data", "经济运行数据", "#2563eb", 41, ["增加值", "GDP", "增速", "同比", "经济运行", "统计公报"]),
    ("price_market", "价格与市场", "#dc2626", 42, ["价格调整", "市场行情", "成品油", "价格上涨", "价格下调"]),
    ("rate_forex", "利率汇率", "#c2410c", 43, ["汇率", "结售汇", "外汇市场", "人民币汇率"]),
    ("conference_expo", "会议展会活动", "#db2777", 44, ["大会", "论坛", "展会", "博览会", "研讨会", "峰会"]),
    # F. 社会民生（2）
    ("sports_event", "文体赛事", "#ea580c", 50, ["赛事", "运动会", "艺术节", "演出", "比赛"]),
    ("social_service", "社会民生服务", "#65a30d", 51, ["社保", "就业", "养老", "社区服务", "供暖", "民生"]),
]

# 每个 action 允许的主题组
ACTION_TOPIC_GROUPS = {
    "bid_action": {"gov_procurement", "project_tender", "service_bid", "it_bid", "medical_bid", "single_source"},
    "fin_demand": {"ipo_listing", "private_placement", "bond_financing", "m_a", "loan_demand", "fund_investment", "enterprise_dynamics"},
    "account_chance": {"enterprise_dynamics", "park_settlement"},
    "park_project": {"park_settlement", "platform_landing", "project_launch", "land_transfer"},
    "policy_ref": {"monetary_policy", "financial_regulation", "tax_finance_policy", "subsidy_program",
                   "industry_planning", "innovation_policy", "foreign_trade", "green_development",
                   "economic_data", "price_market", "rate_forex", "conference_expo",
                   "sports_event", "social_service"},
}

# 16 类行业标签（含 government，收紧泛词）
INDUSTRY_TAGS = [
    ("finance", "金融", "#0ea5e9", 0, ["金融", "银行", "保险", "证券", "基金", "信托", "金融监管", "货币"]),
    ("digital_economy", "数字经济", "#6366f1", 1, ["人工智能", "大数据", "云计算", "软件", "数字经济", "信息技术", "互联网", "大模型", "算力"]),
    ("integrated_circuit", "集成电路", "#4f46e5", 2, ["芯片", "半导体", "集成电路", "晶圆", "封测"]),
    ("biomedicine", "生物医药", "#10b981", 3, ["生物医药", "疫苗", "创新药", "医药研发", "临床"]),
    ("new_energy", "新能源与节能环保", "#059669", 4, ["新能源", "光伏", "储能", "氢能", "双碳", "节能环保"]),
    ("intelligent_mfg", "智能制造与高端装备", "#ef4444", 5, ["智能制造", "机器人", "高端装备", "数控", "仪器仪表", "传感器", "工业母机"]),
    ("automobile", "智能网联汽车", "#dc2626", 6, ["新能源汽车", "智能网联汽车", "自动驾驶", "汽车产业"]),
    ("aerospace", "航空航天", "#7c3aed", 7, ["航天", "航空", "卫星", "火箭", "低空经济", "无人机"]),
    ("commercial_service", "商务服务", "#f59e0b", 8, ["法律顾问", "会计", "审计", "人力资源服务", "知识产权代理", "咨询公司", "会展服务"]),
    ("culture_tourism", "文化旅游", "#a855f7", 9, ["文化", "旅游", "演艺", "博物馆", "文创", "书店"]),
    ("medical_health", "医疗健康", "#0d9488", 10, ["医院", "医疗", "健康", "养老", "口腔", "药品", "卫生"]),
    ("logistics_trade", "物流与跨境贸易", "#0891b2", 11, ["物流", "仓储", "跨境电商", "口岸", "综保区", "货运"]),
    ("construction", "城市建设与房地产", "#b45309", 12, ["工程建设", "建筑施工", "房地产", "城市更新", "基础设施", "轨道交通", "市政工程", "老旧小区"]),
    ("education", "教育", "#16a34a", 13, ["教育", "学校", "学院", "培训", "大学", "中学", "小学"]),
    ("government", "政府机构", "#64748b", 14, ["财政局", "税务局", "发改委", "经信局", "国资委", "科委", "街道办事处", "人民政府"]),
    ("other", "其他", "#9ca3af", 15, []),
]

# 旧脏 code → 新 code
INDUSTRY_ALIAS = {
    "tech": "digital_economy",
    "manufacturing": "intelligent_mfg",
    "advanced_manufacturing": "intelligent_mfg",
    "medical": "medical_health",
    "medical_health": "medical_health",
    "digital": "digital_economy",
    "energy": "new_energy",
    "investment": "finance",
    "retail": "other",
    "real_estate": "construction",
    "government": "government",
    "logistics": "logistics_trade",
    "education": "education",
    "culture": "culture_tourism",
    "finance": "finance",
}

INFO_TYPE_TAGS = [
    ("policy", "政策动态", "#3498db", 0, []),
    ("bidding", "招投标", "#e67e22", 1, []),
    ("enterprise", "企业动态", "#2ecc71", 2, []),
    ("park", "园区动态", "#9b59b6", 3, []),
]

OPPORTUNITY_TAGS = [
    ("bidding", "招投标", "#1a56db", 0, []),
    ("financing", "融资", "#f59e0b", 1, []),
    ("merger", "并购", "#8b5cf6", 2, []),
    ("account", "开户", "#10b981", 3, []),
    ("subsidy", "补贴申报", "#06b6d4", 4, []),
    ("land", "土地出让", "#ef4444", 5, []),
]

# ============ 规则引擎 ============

def make_matcher(tag_defs):
    """把标签定义转成 [(code, keywords)] 并按关键词长度降序（长词优先匹配）"""
    rules = [(code, [k for k in kws if k]) for code, _name, _c, _o, kws in tag_defs]
    for r in rules:
        r[1].sort(key=len, reverse=True)
    return rules

ACTION_RULES = make_matcher(ACTION_TAGS)
TOPIC_RULES = make_matcher(TOPIC_TAGS)
INDUSTRY_RULES = make_matcher(INDUSTRY_TAGS)
AREA_RULES = make_matcher(AREA_TAGS)

# action 与 topic 组的兜底映射（未命中任何主题时）
ACTION_DEFAULT_TOPIC = {
    "bid_action": "gov_procurement",
    "fin_demand": "loan_demand",
    "account_chance": "enterprise_dynamics",
    "park_project": "park_settlement",
    "policy_ref": "industry_planning",
}

# 强信号词（分级判断，避免泛词误判）
ACCOUNT_STRONG_WORDS = ["新设", "注册成立", "登记设立", "迁址", "工商注册", "完成注册"]
BID_STRONG_WORDS = [
    "招标公告", "公开招标", "竞争性磋商", "竞争性谈判", "单一来源", "比选公告",
    "中标公告", "成交公告", "中标结果", "成交结果", "询价公告", "采购意向",
    "采购项目", "招标项目", "资格预审", "公开比选", "招投标",
]
FIN_STRONG_WORDS = [
    "募集资金", "定向增发", "发行股票", "发行股份", "发行债券", "并购重组",
    "吸收合并", "股权转让", "资产重组", "IPO", "定增", "挂牌上市", "董事会", "股东大会",
]
PARK_STRONG_WORDS = [
    "招商引资", "产业基地", "项目开工", "开工建设", "奠基", "综保区",
    "产业园", "建成投用", "创新中心",
]
# 政策强词（招投标/融资类未命中时兜底）
POLICY_STRONG_WORDS = ["政策", "通知", "办法", "意见", "规划", "指南", "监管", "申报", "批复", "会议", "揭榜挂帅"]

# 其他北京区县（非重点区，命中则归 other；海淀/丰台已有专标签不在此列）
OTHER_BEIJING_DISTRICTS = [
    "西城区", "西城", "石景山区", "石景山", "昌平区", "昌平",
    "大兴区", "大兴", "顺义区", "顺义", "房山区", "房山", "门头沟区", "门头沟",
    "平谷区", "平谷", "怀柔区", "怀柔", "密云区", "密云", "延庆区", "延庆",
]


def match_tags(text: str, rules, max_n=3, allowed=None):
    """匹配关键词，返回 [(code, hit_count)] 按命中数降序；allowed 限定候选 code 集合"""
    if not text:
        return []
    hits = []
    for code, kws in rules:
        if allowed is not None and code not in allowed:
            continue
        cnt = 0
        for kw in kws:
            if kw in text:
                cnt += 1
        if cnt > 0:
            hits.append((code, cnt))
    hits.sort(key=lambda x: (-x[1], x[0]))
    return [c for c, _ in hits[:max_n]]


def decide_action(title_text: str, full_text: str) -> str:
    """按强词分级判断一级行动分类：标题强词优先，正文补充，开户词仅看标题"""
    # ===== 标题强词 =====
    if any(w in title_text for w in ACCOUNT_STRONG_WORDS):
        return "account_chance"
    if any(w in title_text for w in BID_STRONG_WORDS):
        return "bid_action"
    if any(w in title_text for w in FIN_STRONG_WORDS):
        return "fin_demand"
    if any(w in title_text for w in PARK_STRONG_WORDS):
        return "park_project"
    if any(w in title_text for w in POLICY_STRONG_WORDS):
        return "policy_ref"
    # ===== 正文补充（开户词不参与，避免正文误命中） =====
    if any(w in full_text for w in BID_STRONG_WORDS):
        return "bid_action"
    if any(w in full_text for w in FIN_STRONG_WORDS):
        return "fin_demand"
    if any(w in full_text for w in PARK_STRONG_WORDS):
        return "park_project"
    if any(w in full_text for w in POLICY_STRONG_WORDS):
        return "policy_ref"
    # 兜底：关键词直接匹配 action
    hits = match_tags(full_text, ACTION_RULES, 1)
    return hits[0] if hits else "policy_ref"


def decide_area(title_text: str, full_text: str, channel: str) -> list:
    """区域匹配：标题优先 > 全文补充；重点区 > 其他区县(other) > 全国 > 北京市级"""
    key_areas = {c for c, _n, _col, _o, _k in AREA_TAGS if c in ("chaoyang", "dongcheng", "tongzhou", "yizhuang", "haidian", "fengtai")}

    # 1. 标题重点区
    areas = match_tags(title_text, AREA_RULES, 2, allowed=key_areas)
    if areas:
        return areas[:2]
    # 2. 标题其他区县 → other
    if any(d in title_text for d in OTHER_BEIJING_DISTRICTS):
        return ["other"]
    # 3. 全文重点区（补充）
    areas = match_tags(full_text, AREA_RULES, 2, allowed=key_areas)
    if areas:
        return areas[:2]
    # 4. 全文其他区县 → other
    if any(d in full_text for d in OTHER_BEIJING_DISTRICTS):
        return ["other"]
    # 5. 全国性
    if any(k in full_text for k in ["国家", "全国", "中央", "央行", "金融监管总局", "证监会", "财政部", "商务部", "工信部"]):
        return ["national"]
    # 6. 北京市级（严格匹配"北京市"，避免"北京时间"等误判）
    if "北京市" in full_text:
        return ["beijing"]
    # 7. 上市公司/资本市场来源渠道默认北京市级
    if channel and any(k in channel for k in ["巨潮", "北交所", "货币网", "投资北京"]):
        return ["beijing"]
    return ["other"]


def decide_industry(text: str, channel: str) -> list:
    """行业匹配：命中取前2，无命中 other（不再默认 finance）"""
    inds = match_tags(text, INDUSTRY_RULES, 2)
    inds = [i for i in inds if i != "other"]
    if inds:
        return inds[:2]
    return ["other"]


# 模拟模式 AI 废话 tip（清理用）
MOCK_TIPS = [
    "💡 可重点关注相关企业，提供定制化金融服务方案。",
    "这是一条重要的资讯摘要，包含了核心业务信息和关键数据。",
]


def tag_item(title: str, summary: str, content: str, channel: str) -> dict:
    """对单条资讯打标：action 强词分级 → topic 按 action 组别过滤 → industry/area"""
    raw_title = re.sub(r"<[^>]+>", "", title or "")
    full = f"{raw_title}。{(summary or '')[:300]}。{(content or '')[:1200]}"
    full = re.sub(r"<[^>]+>", "", full)  # 去掉 HTML 标签（<em>等）

    action = decide_action(raw_title, full)

    # 主题按 action 组别过滤（保证 topic 与 action 语义一致）
    allowed_topics = ACTION_TOPIC_GROUPS[action]
    topic_hits = match_tags(full, TOPIC_RULES, 3, allowed=allowed_topics)

    # 主题兜底
    if not topic_hits:
        topic_hits = [ACTION_DEFAULT_TOPIC[action]]

    industry = decide_industry(full, channel)
    area = decide_area(raw_title, full, channel)

    # info_type
    info_type_map = {
        "bid_action": "bidding", "fin_demand": "enterprise",
        "account_chance": "enterprise", "park_project": "park",
        "policy_ref": "policy",
    }
    return {
        "business_category": action,
        "topic_tags": topic_hits,
        "industry_tags": industry,
        "area_tags": area,
        "info_type": info_type_map[action],
    }


# ============ 字典重建 ============

def rebuild_dictionary(db):
    """重建 TagDictionary（清空后整体重建，避免唯一约束冲突）"""
    print("\n== 重建 TagDictionary ==")
    # 清空旧字典（action/area/topic/industry/info_type/opportunity 全部重定义，
    # 并清理 v2 遗留 business 类型）
    deleted = db.query(TagDictionary).delete()
    db.commit()
    print(f"  清空旧标签 {deleted} 个")

    groups = [
        ("action", ACTION_TAGS), ("area", AREA_TAGS), ("topic", TOPIC_TAGS),
        ("industry", INDUSTRY_TAGS), ("info_type", INFO_TYPE_TAGS),
        ("opportunity", OPPORTUNITY_TAGS),
    ]
    total = 0
    for tag_type, defs in groups:
        for code, name, color, order, kws in defs:
            db.add(TagDictionary(
                tag_type=tag_type, tag_code=code, tag_name=name,
                tag_color=color, sort_order=order,
                keywords=kws or [], is_active=True,
            ))
            total += 1
    db.commit()
    print(f"  标签字典重建完成: 共 {total} 个标签")


def ensure_topic_tags_column(db):
    """确保 news_items.topic_tags 列存在"""
    r = db.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='news_items' AND column_name='topic_tags'"
    )).fetchone()
    if not r:
        print("== 新增 news_items.topic_tags 列 ==")
        db.execute(text("ALTER TABLE news_items ADD COLUMN topic_tags jsonb DEFAULT '[]'::jsonb"))
        db.commit()
        print("  已新增 topic_tags 列")
    else:
        print("== topic_tags 列已存在 ==")


# ============ 主流程 ============

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="只预览不打标")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.dry_run:
            print("== dry-run 模式：不执行 DDL/字典变更/数据写入 ==")
        else:
            ensure_topic_tags_column(db)
            rebuild_dictionary(db)

        items = db.query(NewsItem).filter(NewsItem.is_deleted == False).all()
        print(f"\n== 重打标 {len(items)} 条资讯 {'(dry-run)' if args.dry_run else ''} ==")

        before = Counter()
        for i in items:
            before[i.business_category] += 1

        updated = 0
        after = Counter()
        after_topic = Counter()
        after_industry = Counter()
        after_area = Counter()
        tip_cleaned = 0

        for it in items:
            old_tags = {
                "business_category": it.business_category,
                "industry_tags": list(it.industry_tags or []),
                "area_tags": list(it.area_tags or []),
            }
            new = tag_item(it.title or "", it.content_summary or "", it.content_raw or "", it.source_channel or "")

            it.business_category = new["business_category"]
            it.topic_tags = new["topic_tags"]
            it.industry_tags = new["industry_tags"]
            it.area_tags = new["area_tags"]
            it.info_type = new["info_type"]
            # 清理模拟模式废话 tip
            if it.business_tip and it.business_tip.strip() in MOCK_TIPS:
                it.business_tip = None
                tip_cleaned += 1

            flag_modified(it, "industry_tags")
            flag_modified(it, "area_tags")
            flag_modified(it, "topic_tags")
            updated += 1
            after[it.business_category] += 1
            for t in new["topic_tags"]:
                after_topic[t] += 1
            for ind in new["industry_tags"]:
                after_industry[ind] += 1
            for a in new["area_tags"]:
                after_area[a] += 1

        if not args.dry_run:
            db.commit()

        # ===== 对比报告 =====
        print("\n" + "=" * 56)
        print("打标前后对比报告")
        print("=" * 56)

        print("\n① action 行动分类变化:")
        print(f"  {'code':<20}{'before':>8}{'after':>8}")
        all_actions = sorted(set(list(before.keys()) + list(after.keys())), key=lambda x: str(x))
        for k in all_actions:
            name = k or "(未分类)"
            print(f"  {name:<20}{before.get(k, 0):>8}{after.get(k, 0):>8}")

        print("\n② topic 主题标签 TOP15（新维度）:")
        for k, v in after_topic.most_common(15):
            print(f"  {k}: {v}")

        print("\n③ industry 行业标签变化（重打标后）:")
        for k, v in after_industry.most_common():
            print(f"  {k}: {v}")

        print("\n④ area 区域标签分布:")
        for k, v in after_area.most_common():
            print(f"  {k}: {v}")

        print(f"\n更新: {updated} 条 | 清理模拟废话 tip: {tip_cleaned} 条")
        if args.dry_run:
            print("（dry-run，未写入数据库）")
        print("=" * 56)

    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        print(f"失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
