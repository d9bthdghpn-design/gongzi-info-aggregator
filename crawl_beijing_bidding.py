"""
北京市政府采购网 - 招投标公告采集脚本（P0 核心源，稳健版）
采集：主页公告链接 → 批量抓详情 → 入库 bid_action
特点：独立请求、异常容错、URL去重、可重复运行
"""
import os
import sys
import re
import time
import hashlib
import logging
from datetime import datetime, date
from urllib.parse import urljoin

os.environ.setdefault("DATABASE_URL", "postgresql://postgres.sljoxgawgfdhchyibvdx:Ljz8248282%40@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres")
os.environ.setdefault("ENVIRONMENT", "production")
os.environ.setdefault("JWT_SECRET_KEY", "gOINcX8fj49sh2rUyna6W1JuBeqtFzTVMERQvKoYZPAbC7lH")
os.environ.setdefault("CORS_ORIGINS", "https://gongzi-info-aggregator.onrender.com")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

import requests
from bs4 import BeautifulSoup
from app.database import SessionLocal
from app.models.news import NewsItem, CrawlSource

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE = "http://www.ccgp-beijing.gov.cn"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": BASE + "/",
    "Connection": "close",
}

BID_KEYWORDS = ["招标", "投标", "磋商", "询价", "竞争性", "公开招标", "采购", "中标", "单一来源"]
NOISE_KEYWORDS = ["拟聘用", "招聘", "面试", "人员公示"]


def dedup_hash(title: str, content: str) -> str:
    return hashlib.md5(f"{title}{content[:500]}".encode("utf-8")).hexdigest()


def fetch(url: str, timeout: int = 12) -> str:
    """抓取页面（独立连接，短超时）"""
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    for enc in ["utf-8", "gbk", "gb2312", "gb18030"]:
        r.encoding = enc
        text = r.text
        if len(text) > 1000:
            return text
    return r.text


def extract_announcements(html: str) -> list:
    """从主页提取公告链接和标题"""
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        title = re.sub(r"\s+", " ", a.get_text(strip=True))
        if len(title) < 8 or title in seen:
            continue
        if "/xxgg/" not in href:
            continue
        if any(k in title for k in NOISE_KEYWORDS):
            continue
        url = href if href.startswith("http") else ("http:" + href if href.startswith("//") else urljoin(BASE, href))
        seen.add(title)
        results.append({"title": title, "url": url})
    return results


def extract_detail(html: str) -> str:
    """提取详情页正文"""
    try:
        soup = BeautifulSoup(html, "html.parser")
        for sel in [".detail-content", ".article-content", ".content", ".TRS_Editor", "#zoom", ".vF_detail_content", ".detail"]:
            el = soup.select_one(sel)
            if el:
                text = el.get_text("\n", strip=True)
                if len(text) > 50:
                    return text[:5000]
        for tag in soup.find_all(["p", "div"]):
            text = tag.get_text("\n", strip=True)
            if len(text) > 200 and any(k in text for k in ["招标", "采购", "磋商"]):
                return text[:5000]
    except Exception:
        pass
    return ""


def parse_date(text: str) -> date:
    m = re.search(r"20\d{2}[-年/.]\d{1,2}[-月/.]\d{1,2}", text)
    if m:
        ds = m.group().replace("年", "-").replace("月", "-").replace("日", "").replace("/", "-").replace(".", "-")
        try:
            return datetime.strptime(ds, "%Y-%m-%d").date()
        except Exception:
            pass
    return date.today()


def is_bid_item(title: str) -> bool:
    return any(k in title for k in BID_KEYWORDS)


def save_item(db, item: dict) -> bool:
    """入库（URL+内容双去重）"""
    title = item["title"].strip()
    if not title:
        return False
    url = item["url"]
    if url:
        if db.query(NewsItem).filter(NewsItem.source_url == url).first():
            return False
    content = item.get("content", "") or ""
    dh = dedup_hash(title, content)
    if db.query(NewsItem).filter(NewsItem.dedup_hash == dh).first():
        return False
    db.add(NewsItem(
        title=title[:200],
        source_url=url[:1024] if url else None,
        source_channel="北京市政府采购网",
        source_type="bidding_trade",
        content_raw=content[:5000],
        content_summary=content[:300] if content else None,
        publish_date=item.get("pub_date", date.today()),
        area_tags=["beijing"],
        industry_tags=["other"],
        business_category="bid_action",
        info_type="bidding",
        status="pending_review",
        quality_score=0,
        dedup_hash=dh,
        lead_count=0,
    ))
    db.commit()
    return True


def process_item(db, item: dict):
    """处理单条：抓详情 + 入库（独立容错）"""
    try:
        detail_html = fetch(item["url"])
        item["content"] = extract_detail(detail_html)
        item["pub_date"] = parse_date(detail_html[:3000] + item["title"])
    except Exception as e:
        logger.warning(f"  详情抓取失败: {item['title'][:30]} - {str(e)[:40]}")
        item["content"] = ""
        item["pub_date"] = date.today()
    return save_item(db, item)


def main():
    db = SessionLocal()
    try:
        logger.info("抓取北京市政府采购网主页...")
        try:
            html = fetch(BASE + "/")
        except Exception as e:
            logger.error(f"主页抓取失败: {e}")
            return
        items = extract_announcements(html)
        bid_items = [it for it in items if is_bid_item(it["title"])]
        logger.info(f"主页提取 {len(items)} 条公告, 招投标类 {len(bid_items)} 条")

        saved = 0
        for item in bid_items:
            if saved >= 40:
                break
            if process_item(db, item):
                saved += 1
                logger.info(f"  [{saved}] 新增: {item['title'][:40]}")
            time.sleep(0.8)

        logger.info(f"北京市政府采购网采集完成: 新增 {saved} 条")

        # 更新采集源状态
        src = db.query(CrawlSource).filter(CrawlSource.name.contains("政府采购网")).order_by(CrawlSource.id).first()
        if src:
            src.last_crawl_at = datetime.utcnow()
            src.last_crawl_status = "success"
            db.commit()
    except Exception as e:
        logger.error(f"采集异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
