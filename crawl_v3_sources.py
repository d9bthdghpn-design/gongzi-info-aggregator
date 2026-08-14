"""
v4.0 新数据源采集脚本
P0: 公共资源交易/招标投标/北交所增资/规自委土地
P1: 巨潮/北交所/货币网/投资北京/朝阳局委办
"""
import os
import sys
import json
import hashlib
import logging
from datetime import datetime, date
from typing import List, Dict, Optional

os.environ.setdefault("DATABASE_URL", "postgresql://postgres.sljoxgawgfdhchyibvdx:Ljz8248282%40@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres")
os.environ.setdefault("ENVIRONMENT", "production")
os.environ.setdefault("JWT_SECRET_KEY", "gOINcX8fj49sh2rUyna6W1JuBeqtFzTVMERQvKoYZPAbC7lH")
os.environ.setdefault("CORS_ORIGINS", "https://gongzi-info-aggregator.onrender.com")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.news import NewsItem, CrawlSource
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


def _dedup_hash(title: str, content: str) -> str:
    return hashlib.md5(f"{title}{content[:500]}".encode("utf-8")).hexdigest()


def save_news(db: Session, item: Dict, source_name: str, source_type: str,
              area_tags: List[str], industry_tags: List[str],
              business_category: str = "bid_action") -> bool:
    """保存资讯到数据库，去重"""
    title = item.get("title", "").strip()
    if not title:
        return False

    content = item.get("content", "") or ""
    source_url = item.get("url", "")
    pub_date = item.get("pub_date", date.today().isoformat())

    # URL去重
    if source_url:
        existing = db.query(NewsItem).filter(NewsItem.source_url == source_url).first()
        if existing:
            return False

    # 内容哈希去重
    dh = _dedup_hash(title, content)
    existing = db.query(NewsItem).filter(NewsItem.dedup_hash == dh).first()
    if existing:
        return False

    news = NewsItem(
        title=title[:200],
        source_url=source_url[:1024] if source_url else None,
        source_channel=source_name,
        source_type=source_type,
        content_raw=content[:5000],
        content_summary=content[:300] if content else None,
        publish_date=pub_date if isinstance(pub_date, date) else date.today(),
        area_tags=area_tags,
        industry_tags=industry_tags,
        business_category=business_category,
        info_type="bidding" if business_category == "bid_action" else "enterprise",
        status="pending_review",
        quality_score=0,
        dedup_hash=dh,
        lead_count=0,
    )
    db.add(news)
    db.commit()
    return True


def crawl_ggzy_beijing() -> List[Dict]:
    """P0-1: 全国公共资源交易平台 - 北京区域"""
    logger.info("开始采集: 全国公共资源交易平台(北京)")
    results = []
    try:
        # 北京公共资源交易服务平台
        url = "https://ggzy.beijing.gov.cn/xxgk/003/003001/003001001/"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        items = soup.select("ul.ewb-list li a, .list-item a, .article-list li a")
        for a in items[:15]:
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if not title or len(title) < 5:
                continue
            if href and not href.startswith("http"):
                href = "https://ggzy.beijing.gov.cn" + href
            results.append({"title": title, "url": href, "content": "", "pub_date": date.today()})

        logger.info(f"公共资源交易平台采集到 {len(results)} 条")
    except Exception as e:
        logger.error(f"公共资源交易平台采集失败: {e}")
    return results


def crawl_cebpubservice() -> List[Dict]:
    """P0-2: 中国招标投标公共服务平台"""
    logger.info("开始采集: 中国招标投标公共服务平台")
    results = []
    try:
        url = "http://www.cebpubservice.com/ctpsp_iiss/searchbusinesstypebeforedooraction/getAllList.do"
        # 尝试公告列表页
        list_url = "http://www.cebpubservice.com/xxfb/ggxx/"
        resp = requests.get(list_url, headers=HEADERS, timeout=15)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        items = soup.select("ul li a, .list a, table a")
        for a in items[:20]:
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if not title or len(title) < 8:
                continue
            if "北京" not in title and "京" not in title:
                continue
            if href and not href.startswith("http"):
                href = "http://www.cebpubservice.com" + href
            results.append({"title": title, "url": href, "content": "", "pub_date": date.today()})

        logger.info(f"招标投标平台采集到 {len(results)} 条")
    except Exception as e:
        logger.error(f"招标投标平台采集失败: {e}")
    return results


def crawl_ghzyr_land() -> List[Dict]:
    """P0-4: 北京市规自委土地出让公告"""
    logger.info("开始采集: 北京市规自委土地出让公告")
    results = []
    try:
        url = "https://ghzrzyw.beijing.gov.cn/zhengwuxinxi/tdgy/"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        items = soup.select("ul li a, .list a, .news-list a")
        for a in items[:15]:
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if not title or len(title) < 5:
                continue
            if href and not href.startswith("http"):
                href = "https://ghzrzyw.beijing.gov.cn" + href
            results.append({"title": title, "url": href, "content": "", "pub_date": date.today()})

        logger.info(f"规自委土地出让采集到 {len(results)} 条")
    except Exception as e:
        logger.error(f"规自委土地出让采集失败: {e}")
    return results


def crawl_cninfo_beijing() -> List[Dict]:
    """P1-1: 巨潮资讯网 - 北京上市公司公告"""
    logger.info("开始采集: 巨潮资讯网(北京上市公司)")
    results = []
    try:
        # 巨潮公告搜索API
        api_url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
        payload = {
            "pageNum": 1,
            "pageSize": 30,
            "column": "szse",
            "tabName": "fulltext",
            "plate": "",
            "stock": "",
            "searchkey": "北京",
            "secid": "",
            "category": "category_ndbg_szsh;category_yjdbg_szsh;category_zf_szsh;category_dshgg_szsh",
            "trade": "",
            "seDate": "",
            "sortName": "",
            "sortType": "",
            "isHLtitle": "true",
        }
        resp = requests.post(api_url, data=payload, headers=HEADERS, timeout=15)
        data = resp.json()
        announcements = data.get("announcements", [])
        for ann in announcements[:15]:
            title = ann.get("announcementTitle", "")
            sec_name = ann.get("secName", "")
            adj_url = ann.get("adjunctUrl", "")
            if not title:
                continue
            full_title = f"{sec_name}: {title}" if sec_name else title
            source_url = f"http://static.cninfo.com.cn/{adj_url}" if adj_url else ""
            results.append({
                "title": full_title,
                "url": source_url,
                "content": f"上市公司{sec_name}发布公告：{title}",
                "pub_date": date.today(),
            })

        logger.info(f"巨潮资讯网采集到 {len(results)} 条")
    except Exception as e:
        logger.error(f"巨潮资讯网采集失败: {e}")
    return results


def crawl_bse() -> List[Dict]:
    """P1-2: 北交所官网 - 专精特新融资动态"""
    logger.info("开始采集: 北交所官网")
    results = []
    try:
        url = "https://www.bse.cn/disclosure/announcement.html"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        items = soup.select("ul li a, .list a, table a")
        for a in items[:15]:
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if not title or len(title) < 5:
                continue
            if href and not href.startswith("http"):
                href = "https://www.bse.cn" + href
            results.append({"title": title, "url": href, "content": "", "pub_date": date.today()})

        logger.info(f"北交所官网采集到 {len(results)} 条")
    except Exception as e:
        logger.error(f"北交所官网采集失败: {e}")
    return results


def crawl_invest_beijing() -> List[Dict]:
    """P1-4: 投资北京 - 招商引资项目"""
    logger.info("开始采集: 投资北京")
    results = []
    try:
        url = "https://investbeijing.gov.cn/html/zwdt/"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        items = soup.select("ul li a, .list a, .news-list a")
        for a in items[:15]:
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if not title or len(title) < 5:
                continue
            if href and not href.startswith("http"):
                href = "https://investbeijing.gov.cn" + href
            results.append({"title": title, "url": href, "content": "", "pub_date": date.today()})

        logger.info(f"投资北京采集到 {len(results)} 条")
    except Exception as e:
        logger.error(f"投资北京采集失败: {e}")
    return results


def crawl_chinamoney() -> List[Dict]:
    """P1-3: 中国货币网 - 企业债券发行"""
    logger.info("开始采集: 中国货币网")
    results = []
    try:
        url = "https://www.chinamoney.com.cn/chinese/scjcqk/"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")

        items = soup.select("ul li a, .list a, table a")
        for a in items[:15]:
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if not title or len(title) < 5:
                continue
            if href and not href.startswith("http"):
                href = "https://www.chinamoney.com.cn" + href
            results.append({"title": title, "url": href, "content": "", "pub_date": date.today()})

        logger.info(f"中国货币网采集到 {len(results)} 条")
    except Exception as e:
        logger.error(f"中国货币网采集失败: {e}")
    return results


def main():
    db = SessionLocal()
    total_saved = 0
    source_results = {}

    # P0 数据源
    sources_p0 = [
        ("全国公共资源交易平台(北京)", "bidding_trade", crawl_ggzy_beijing, ["beijing"], ["other"], "bid_action"),
        ("中国招标投标公共服务平台", "bidding_trade", crawl_cebpubservice, ["beijing"], ["other"], "bid_action"),
        ("北京市规自委土地出让", "bidding_trade", crawl_ghzyr_land, ["beijing"], ["other"], "bid_action"),
    ]

    # P1 数据源
    sources_p1 = [
        ("巨潮资讯网(北京上市公司)", "corp_finance", crawl_cninfo_beijing, ["beijing"], ["finance"], "fin_demand"),
        ("北交所官网", "corp_finance", crawl_bse, ["beijing"], ["tech"], "fin_demand"),
        ("中国货币网", "corp_finance", crawl_chinamoney, ["beijing"], ["finance"], "fin_demand"),
        ("投资北京", "park_project", crawl_invest_beijing, ["beijing"], ["business_service"], "park_project"),
    ]

    all_sources = sources_p0 + sources_p1

    for source_name, source_type, crawl_func, area_tags, industry_tags, biz_cat in all_sources:
        try:
            items = crawl_func()
            saved = 0
            for item in items:
                if save_news(db, item, source_name, source_type, area_tags, industry_tags, biz_cat):
                    saved += 1
            source_results[source_name] = {"fetched": len(items), "saved": saved}
            total_saved += saved
            logger.info(f"  {source_name}: 获取{len(items)}条, 新增{saved}条")
        except Exception as e:
            logger.error(f"  {source_name} 异常: {e}")
            source_results[source_name] = {"fetched": 0, "saved": 0, "error": str(e)}

    # 北京产权交易所 - 需要Playwright，记录跳过
    source_results["北京产权交易所(增资扩股)"] = {
        "fetched": 0, "saved": 0,
        "note": "需Playwright渲染抓取(521防护)，Render环境不支持，建议本地采集后批量入库"
    }
    # 朝阳区局委办 - 部门专栏无新闻列表
    source_results["朝阳区科信局/商务局/投促局"] = {
        "fetched": 0, "saved": 0,
        "note": "部门专栏页为部门介绍页，无新闻列表结构，已探测确认无法抓取"
    }

    db.close()

    print("\n" + "=" * 60)
    print("v4.0 新数据源采集结果汇总")
    print("=" * 60)
    for name, res in source_results.items():
        status = f"获取{res.get('fetched',0)}条/新增{res.get('saved',0)}条"
        if res.get("error"):
            status += f" [错误: {res['error'][:50]}]"
        if res.get("note"):
            status += f" [说明: {res['note']}]"
        print(f"  {name}: {status}")
    print(f"\n总计新增: {total_saved} 条")
    print("=" * 60)


if __name__ == "__main__":
    main()
