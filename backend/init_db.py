"""
数据库初始化脚本 - 创建表并插入初始数据（幂等，可安全重复执行）
"""
import sys
import os
import uuid
from datetime import datetime, date, timedelta, timezone


def _now():
    return datetime.now(timezone.utc)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, engine, SessionLocal
from app.models import User, TagDictionary, CrawlSource, NewsItem, Topic
from app.core.security import get_password_hash


def init_db():
    """初始化数据库（幂等，可安全重复执行）"""
    print("正在创建数据表...")

    # 导入所有模型确保注册
    from app.models import user, news, lead, log

    # 创建所有表（如果不存在的话，不会修改已有表结构）
    Base.metadata.create_all(bind=engine)

    print("数据表创建完成！")

    db = SessionLocal()
    try:
        # 1. 创建管理员用户（如果不存在）
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            print("正在创建管理员用户...")
            admin = User(
                id=str(uuid.uuid4()),
                username="admin",
                email="admin@example.com",
                full_name="系统管理员",
                password_hash=get_password_hash("admin123"),
                role="admin",
                department="信息技术部",
                position="系统管理员",
                is_active=True,
                created_at=_now(),
                updated_at=_now(),
            )
            db.add(admin)
            db.commit()
            print("  管理员用户创建成功")
        else:
            print("  管理员用户已存在，跳过")

        # 2. 创建普通用户（如果不存在）
        viewer = db.query(User).filter(User.username == "user").first()
        if not viewer:
            print("正在创建普通用户...")
            viewer = User(
                id=str(uuid.uuid4()),
                username="user",
                email="user@example.com",
                full_name="张经理",
                password_hash=get_password_hash("user123"),
                role="viewer",
                department="公司业务部",
                position="客户经理",
                is_active=True,
                created_at=_now(),
                updated_at=_now(),
            )
            db.add(viewer)
            db.commit()
            print("  普通用户创建成功")
        else:
            print("  普通用户已存在，跳过")

        # 3. 插入标签（如果不存在）
        if db.query(TagDictionary).count() == 0:
            print("正在插入标签数据...")
            all_tags = [
                # 业务分类
                ("business", "deposit", "存款业务", "#27ae60", 0),
                ("business", "loan", "贷款业务", "#e74c3c", 1),
                ("business", "investment_bank", "投行业务", "#9b59b6", 2),
                ("business", "treasury", "财资业务", "#f39c12", 3),
                ("business", "supply_chain", "供应链金融", "#1abc9c", 4),
                # 区域
                ("area", "chaoyang", "朝阳区", "#3498db", 0),
                ("area", "haidian", "海淀区", "#2ecc71", 1),
                ("area", "fengtai", "丰台区", "#e67e22", 2),
                # 行业
                ("industry", "tech", "信息技术", "#3498db", 0),
                ("industry", "finance", "金融服务", "#9b59b6", 1),
                ("industry", "manufacturing", "制造业", "#e67e22", 2),
                ("industry", "real_estate", "房地产", "#e74c3c", 3),
                ("industry", "medical", "医药健康", "#2ecc71", 4),
                ("industry", "education", "教育培训", "#1abc9c", 5),
                ("industry", "retail", "零售消费", "#f39c12", 6),
                ("industry", "logistics", "物流运输", "#34495e", 7),
                ("industry", "energy", "能源环保", "#27ae60", 8),
                ("industry", "culture", "文化传媒", "#9b59b6", 9),
                ("industry", "government", "政府机构", "#2c3e50", 10),
                # 资讯类型
                ("info_type", "policy", "政策动态", "#3498db", 0),
                ("info_type", "bidding", "招投标", "#e67e22", 1),
                ("info_type", "enterprise", "企业动态", "#2ecc71", 2),
                ("info_type", "park", "园区动态", "#9b59b6", 3),
            ]
            for tag_type, code, name, color, order in all_tags:
                tag = TagDictionary(
                    id=str(uuid.uuid4()),
                    tag_type=tag_type,
                    tag_code=code,
                    tag_name=name,
                    tag_color=color,
                    sort_order=order,
                    is_active=True,
                    created_at=_now(),
                    updated_at=_now(),
                )
                db.add(tag)
            db.commit()
            print(f"  插入 {len(all_tags)} 个标签")
        else:
            print("  标签数据已存在，跳过")

        # 4. 插入采集源（如果不存在）—— P0 五个权威源
        if db.query(CrawlSource).count() == 0:
            print("正在插入采集源...")
            sources = [
                {
                    "name": "中国政府采购网",
                    "source_type": "bidding",
                    "crawl_type": "web",
                    "entry_url": "http://www.ccgp.gov.cn/cggg/dfgg/",
                    "area_scope": [],
                    "industry_scope": ["government"],
                    "priority": 10,
                    "selector_config": {
                        "list_selector": "ul.c_list_bid li",
                        "title_selector": "a",
                        "link_selector": "a@href",
                        "date_selector": "",
                        "date_regex": True,
                        "content_selector": ".vF_detail_content",
                        "next_page_selector": ".next a, a.next",
                    },
                },
                {
                    "name": "北京市政府采购网",
                    "source_type": "bidding",
                    "crawl_type": "web",
                    "entry_url": "http://www.ccgp-beijing.gov.cn/xxgg/qjxxgg/",
                    "area_scope": ["chaoyang", "haidian"],
                    "industry_scope": ["government"],
                    "priority": 9,
                    "selector_config": {
                        "list_selector": ".list li, ul.list li, .news-list li, ul.news-list li",
                        "title_selector": "a",
                        "link_selector": "a@href",
                        "date_selector": ".date, span.time, span.date",
                        "date_regex": True,
                        "content_selector": ".article-content, .TRS_Editor, .content, .vF_detail_content",
                        "next_page_selector": ".next a, a.next",
                    },
                },
                {
                    "name": "北京市公共资源交易服务平台",
                    "source_type": "bidding",
                    "crawl_type": "web",
                    "entry_url": "https://ggzyfw.beijing.gov.cn/",
                    "area_scope": ["chaoyang", "haidian", "fengtai"],
                    "industry_scope": ["government"],
                    "priority": 9,
                    "selector_config": {
                        "list_selector": ".news-list li, .list li, .jyxx-list li, ul li",
                        "title_selector": "a",
                        "link_selector": "a@href",
                        "date_selector": ".date, .time, span.date, span",
                        "date_regex": True,
                        "content_selector": ".article-content, .content, .detail-content, .TRS_Editor, .con",
                        "next_page_selector": ".next a, a.next",
                    },
                },
                {
                    "name": "朝阳区政府",
                    "source_type": "gov",
                    "crawl_type": "web",
                    "entry_url": "http://www.bjchy.gov.cn/",
                    "area_scope": ["chaoyang"],
                    "industry_scope": ["government"],
                    "priority": 8,
                    "selector_config": {
                        "list_selector": "div.news_text li",
                        "title_selector": "a",
                        "link_selector": "a@href",
                        "date_selector": "span",
                        "date_regex": True,
                        "content_selector": ".con, .content_article, .TRS_Editor, .article-content",
                        "next_page_selector": ".next-page a, .next a",
                    },
                },
                {
                    "name": "北京市财政局",
                    "source_type": "gov",
                    "crawl_type": "web",
                    "entry_url": "https://czj.beijing.gov.cn/zwxx/tztg/",
                    "area_scope": ["chaoyang", "haidian", "fengtai"],
                    "industry_scope": ["government", "finance"],
                    "priority": 8,
                    "selector_config": {
                        "list_selector": "div.ul-back li",
                        "title_selector": "a",
                        "link_selector": "a@href",
                        "date_selector": "span.docRelTime",
                        "date_regex": True,
                        "content_selector": ".view.TRS_UEDITOR, .TRS_Editor, .article-content, .content",
                        "next_page_selector": ".next a, a.next",
                    },
                },
                # ===== P1 源：央国企官网（默认未启用，验证选择器后开启）=====
                {
                    "name": "国家电网",
                    "source_type": "enterprise",
                    "crawl_type": "web",
                    "entry_url": "https://www.sgcc.com.cn/html/sgcc_main/col2016010004/column_2016010004_1.shtml",
                    "area_scope": [],
                    "industry_scope": ["energy"],
                    "priority": 6,
                    "is_active": False,
                    "selector_config": {
                        "list_selector": ".news-list li, .list li, ul li",
                        "title_selector": "a",
                        "link_selector": "a@href",
                        "date_selector": ".date, span.time, span",
                        "date_regex": True,
                        "content_selector": ".article-content, .TRS_Editor, .content, .detail",
                        "next_page_selector": ".next a, a.next",
                    },
                },
                {
                    "name": "中国建筑集团",
                    "source_type": "enterprise",
                    "crawl_type": "web",
                    "entry_url": "https://www.cscec.com/zgjzww/300419/300420/index.html",
                    "area_scope": [],
                    "industry_scope": ["construction"],
                    "priority": 6,
                    "is_active": False,
                    "selector_config": {
                        "list_selector": ".news-list li, .list li, ul li",
                        "title_selector": "a",
                        "link_selector": "a@href",
                        "date_selector": ".date, span.time, span",
                        "date_regex": True,
                        "content_selector": ".article-content, .TRS_Editor, .content, .detail",
                        "next_page_selector": ".next a, a.next",
                    },
                },
                {
                    "name": "北京市国资委",
                    "source_type": "gov",
                    "crawl_type": "web",
                    "entry_url": "https://gzw.beijing.gov.cn/",
                    "area_scope": ["chaoyang", "haidian", "fengtai"],
                    "industry_scope": ["government", "finance"],
                    "priority": 7,
                    "is_active": False,
                    "selector_config": {
                        "list_selector": ".news-list li, .list li, ul li",
                        "title_selector": "a",
                        "link_selector": "a@href",
                        "date_selector": ".date, span.time, span",
                        "date_regex": True,
                        "content_selector": ".article-content, .TRS_Editor, .content, .detail",
                        "next_page_selector": ".next a, a.next",
                    },
                },
                # ===== P1 源：微信公众号（默认未启用，需手动提交文章URL）=====
                {
                    "name": "北京发布（微信公众号）",
                    "source_type": "gov",
                    "crawl_type": "wechat",
                    "entry_url": "",
                    "area_scope": ["chaoyang", "haidian", "fengtai"],
                    "industry_scope": ["government"],
                    "priority": 7,
                    "is_active": False,
                    "selector_config": {
                        "article_urls": "",
                        "note": "微信公众号需手动填写文章URL（逗号分隔），或通过RSSHub获取RSS后走rss类型",
                    },
                },
                {
                    "name": "朝阳发改（微信公众号）",
                    "source_type": "gov",
                    "crawl_type": "wechat",
                    "entry_url": "",
                    "area_scope": ["chaoyang"],
                    "industry_scope": ["government"],
                    "priority": 6,
                    "is_active": False,
                    "selector_config": {
                        "article_urls": "",
                        "note": "微信公众号需手动填写文章URL（逗号分隔）",
                    },
                },
            ]
            for s in sources:
                source = CrawlSource(
                    id=str(uuid.uuid4()),
                    name=s["name"],
                    source_type=s["source_type"],
                    crawl_type=s["crawl_type"],
                    entry_url=s["entry_url"],
                    area_scope=s.get("area_scope", []),
                    industry_scope=s.get("industry_scope", []),
                    crawl_interval_hours=24,
                    priority=s["priority"],
                    selector_config=s.get("selector_config", {}),
                    is_active=s.get("is_active", True),
                    created_at=_now(),
                    updated_at=_now(),
                )
                db.add(source)
            db.commit()
            print(f"  插入 {len(sources)} 个采集源")
        else:
            print("  采集源已存在，跳过")

        # 5. 插入示例资讯（如果不存在）
        if db.query(NewsItem).count() == 0:
            print("正在插入示例资讯...")
            sample_news = [
                {
                    "title": "朝阳区发布2024年数字经济发展行动计划，将投入50亿元支持企业数字化转型",
                    "content_summary": "朝阳区政府近日发布《2024年数字经济发展行动计划》，计划投入50亿元专项资金，支持辖区内企业数字化转型。重点支持人工智能、大数据、云计算等领域的创新应用，预计将带动超过200家企业参与。",
                    "business_category": "loan",
                    "area_tags": ["chaoyang"],
                    "industry_tags": ["tech", "government"],
                    "info_type": "policy",
                    "source_type": "gov",
                    "source_channel": "朝阳区政府官网",
                    "business_tip": "数字经济转型企业有大量融资需求，可重点对接科技型中小企业贷款、知识产权质押贷款等产品。建议客户经理梳理辖区内科技企业名单，主动上门营销。",
                    "quality_score": 92,
                    "status": "published",
                },
                {
                    "title": "海淀区某AI企业完成C轮融资10亿元，计划扩大研发团队",
                    "content_summary": "海淀区某人工智能企业近日宣布完成C轮融资，融资金额达10亿元。该企业专注于大模型技术研发，本轮融资将主要用于扩大研发团队和产品商业化落地。公司目前员工规模约500人，计划年底前扩招至800人。",
                    "business_category": "investment_bank",
                    "area_tags": ["haidian"],
                    "industry_tags": ["tech", "finance"],
                    "info_type": "enterprise",
                    "source_type": "enterprise",
                    "source_channel": "企业动态",
                    "business_tip": "融资完成后企业现金流充裕，可重点营销存款理财、财资管理、员工代发工资等业务。同时可跟进后续IPO相关投行业务机会。",
                    "quality_score": 88,
                    "status": "published",
                },
                {
                    "title": "北京市政府采购中心发布2024年信息化建设项目招标公告，预算2.5亿元",
                    "content_summary": "北京市政府采购中心发布2024年度信息化建设项目招标公告，项目总预算2.5亿元。采购内容包括云平台建设、数据中心升级、安全防护体系等多个子项目，投标截止时间为下月15日。",
                    "business_category": "supply_chain",
                    "area_tags": ["chaoyang", "haidian"],
                    "industry_tags": ["government", "tech"],
                    "info_type": "bidding",
                    "source_type": "bidding",
                    "source_channel": "中国政府采购网",
                    "business_tip": "招投标项目涉及大量供应链金融需求，可向投标企业推介投标保函、履约保函、应收账款融资等产品。建议重点关注中标企业名单，及时跟进。",
                    "quality_score": 85,
                    "status": "published",
                },
                {
                    "title": "丰台园区新增30家高新技术企业入驻，年产值预计超百亿",
                    "content_summary": "丰台科技园今年以来新增30家高新技术企业入驻，涵盖生物医药、新能源、智能制造等领域。园区管委会表示，预计新增企业全部达产后，年产值将超过100亿元，带动就业超5000人。",
                    "business_category": "deposit",
                    "area_tags": ["fengtai"],
                    "industry_tags": ["manufacturing", "medical"],
                    "info_type": "park",
                    "source_type": "park",
                    "source_channel": "丰台科技园官网",
                    "business_tip": "新入驻企业有开户、结算、代发工资等基础金融需求。建议联合园区管委会开展批量获客，提供一站式金融服务方案。",
                    "quality_score": 78,
                    "status": "published",
                },
                {
                    "title": "央行发布结构性货币政策工具新指引，支持科技创新和绿色发展",
                    "content_summary": "央行近日发布结构性货币政策工具新指引，进一步加大对科技创新、绿色发展等重点领域的支持力度。新政策将扩大再贷款再贴现规模，引导金融机构增加相关领域信贷投放。",
                    "business_category": "loan",
                    "area_tags": ["chaoyang", "haidian", "fengtai"],
                    "industry_tags": ["finance", "government"],
                    "info_type": "policy",
                    "source_type": "gov",
                    "source_channel": "央行官网",
                    "business_tip": "政策利好科创贷、绿色信贷等产品。建议抓住政策窗口期，加大相关领域贷款投放力度，优化信贷结构。",
                    "quality_score": 90,
                    "status": "published",
                },
            ]
            for i, news in enumerate(sample_news):
                item = NewsItem(
                    id=str(uuid.uuid4()),
                    title=news["title"],
                    content_summary=news["content_summary"],
                    content_raw=news["content_summary"] + "\n\n详细内容正在完善中...",
                    business_category=news["business_category"],
                    area_tags=news["area_tags"],
                    industry_tags=news["industry_tags"],
                    info_type=news["info_type"],
                    source_type=news["source_type"],
                    source_channel=news["source_channel"],
                    source_url=f"https://example.com/news/{i+1}",
                    publish_date=date.today() - timedelta(days=i),
                    business_tip=news["business_tip"],
                    quality_score=news["quality_score"],
                    dedup_hash=f"sample_{i}",
                    status=news["status"],
                    view_count=i * 10 + 5,
                    lead_count=i,
                    created_at=_now(),
                    updated_at=_now(),
                )
                db.add(item)
            db.commit()
            print(f"  插入 {len(sample_news)} 条示例资讯")
        else:
            print("  资讯数据已存在，跳过")

        # 6. 插入示例专题（如果不存在）
        if db.query(Topic).count() == 0:
            print("正在插入专题数据...")
            topics = [
                {"title": "数字经济专题", "description": "聚焦数字经济发展政策、企业动态、投资机会", "filter_config": {"info_type": ["policy", "enterprise"], "industry_tags": ["tech"]}, "sort_order": 1},
                {"title": "基建投资专题", "description": "跟踪基础设施建设项目、招投标信息、投资机会", "filter_config": {"info_type": ["bidding"], "business_category": ["loan", "supply_chain"]}, "sort_order": 2},
                {"title": "专精特新专题", "description": "关注专精特新企业发展、融资需求、上市动态", "filter_config": {"industry_tags": ["tech", "manufacturing"], "info_type": ["enterprise"]}, "sort_order": 3},
            ]
            for t in topics:
                topic = Topic(
                    id=str(uuid.uuid4()),
                    title=t["title"],
                    description=t["description"],
                    filter_config=t["filter_config"],
                    sort_order=t["sort_order"],
                    is_active=True,
                    created_by=admin.id,
                    created_at=_now(),
                    updated_at=_now(),
                )
                db.add(topic)
            db.commit()
            print(f"  插入 {len(topics)} 个专题")
        else:
            print("  专题数据已存在，跳过")

        print("\n数据库初始化完成！")
        print(f"  - 用户: {db.query(User).count()} 个")
        print(f"  - 标签: {db.query(TagDictionary).count()} 个")
        print(f"  - 采集渠道: {db.query(CrawlSource).count()} 个")
        print(f"  - 资讯: {db.query(NewsItem).count()} 条")
        print(f"  - 专题: {db.query(Topic).count()} 个")

    except Exception as e:
        db.rollback()
        print(f"初始化失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    print("\n默认账号：admin / admin123")
