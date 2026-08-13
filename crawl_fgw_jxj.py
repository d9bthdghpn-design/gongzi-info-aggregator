"""采集北京市发改委、经信局通知公告 - 加入数据源并采集入库"""
import os
import sys
import re
import hashlib
import uuid
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

os.environ['DATABASE_URL'] = 'postgresql://postgres.sljoxgawgfdhchyibvdx:Ljz8248282%40@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres'
os.environ['ENVIRONMENT'] = 'production'
os.environ['JWT_SECRET_KEY'] = 'gOINcX8fj49sh2rUyna6W1JuBeqtFzTVMERQvKoYZPAbC7lH'
os.environ['CORS_ORIGINS'] = 'https://gongzi-info-aggregator.onrender.com'

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.database import SessionLocal
from app.models.news import CrawlSource, NewsItem

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
DATE_PATTERN = re.compile(r'20\d{2}[-年./]\d{1,2}[-月./]\d{1,2}')

# 两个数据源配置
SOURCES_CONFIG = [
    {
        'name': '北京市发展和改革委员会-通知通告',
        'source_type': 'gov',
        'crawl_type': 'web',
        'entry_url': 'https://fgw.beijing.gov.cn/gzdt/tztg/',
        'area_scope': ['beijing'],
        'industry_scope': ['finance', 'energy', 'investment'],
        'priority': 7,
        'selector_config': {
            'list_selector': 'ul.list li',
            'title_selector': 'a',
            'link_selector': 'a',
            'content_selector': '.content',
            'encoding': 'utf-8',
        },
    },
    {
        'name': '北京市经济和信息化局-通知公告',
        'source_type': 'gov',
        'crawl_type': 'web',
        'entry_url': 'https://jxj.beijing.gov.cn/jxdt/tzgg/',
        'area_scope': ['beijing'],
        'industry_scope': ['tech', 'manufacturing', 'digital'],
        'priority': 7,
        'selector_config': {
            'list_selector': 'ul.list li',
            'title_selector': 'a',
            'link_selector': 'a',
            'content_selector': '.content',
            'encoding': 'utf-8',
        },
    },
]


def ensure_sources(db):
    """确保数据源存在，不存在则创建"""
    created = []
    for cfg in SOURCES_CONFIG:
        existing = db.query(CrawlSource).filter(CrawlSource.name == cfg['name']).first()
        if existing:
            print(f'  数据源已存在: {cfg["name"]}')
            # 更新配置
            existing.entry_url = cfg['entry_url']
            existing.selector_config = cfg['selector_config']
            existing.is_active = True
            existing.priority = cfg['priority']
            existing.area_scope = cfg['area_scope']
            existing.industry_scope = cfg['industry_scope']
        else:
            source = CrawlSource(
                id=str(uuid.uuid4()),
                name=cfg['name'],
                source_type=cfg['source_type'],
                crawl_type=cfg['crawl_type'],
                entry_url=cfg['entry_url'],
                area_scope=cfg['area_scope'],
                industry_scope=cfg['industry_scope'],
                priority=cfg['priority'],
                is_active=True,
                selector_config=cfg['selector_config'],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(source)
            created.append(source)
            print(f'  创建数据源: {cfg["name"]}')
    db.commit()
    return created


def compute_dedup_hash(title, content):
    text = (title or '') + (content or '')[:500]
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def parse_date(date_str):
    """解析日期字符串"""
    if not date_str:
        return None
    date_str = date_str.replace('年', '-').replace('月', '-').replace('日', '').replace('/', '-').replace('.', '-')
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        return None


def crawl_source(db, source, max_items=15):
    """采集单个数据源"""
    config = source.selector_config or {}
    list_selector = config.get('list_selector', 'ul.list li')
    content_selector = config.get('content_selector', '.content')
    encoding = config.get('encoding', 'utf-8')

    print(f'\n  采集列表页: {source.entry_url}')
    try:
        r = requests.get(source.entry_url, headers=HEADERS, timeout=20)
        for enc in [encoding, 'utf-8', 'gbk', 'gb2312']:
            r.encoding = enc
            if '通知' in r.text or '公告' in r.text:
                break
        soup = BeautifulSoup(r.text, 'html.parser')
    except Exception as e:
        print(f'  列表页抓取失败: {e}')
        source.last_crawl_status = 'failed'
        source.last_error_msg = str(e)[:500]
        db.commit()
        return 0

    items = soup.select(list_selector)
    print(f'  找到 {len(items)} 个列表项')

    count = 0
    for item in items:
        if count >= max_items:
            break
        try:
            a = item.find('a', href=True)
            if not a:
                continue
            title = a.get_text(strip=True)
            if not title or len(title) < 8:
                continue

            href = a['href']
            url = urljoin(source.entry_url, href)

            # 从列表项提取日期
            date_str = ''
            date_match = DATE_PATTERN.search(item.get_text())
            if date_match:
                date_str = date_match.group()

            # 抓详情页
            content = ''
            detail_date = ''
            try:
                r2 = requests.get(url, headers=HEADERS, timeout=15)
                for enc in ['utf-8', 'gbk', 'gb2312']:
                    r2.encoding = enc
                    if len(r2.text) > 500:
                        break
                soup2 = BeautifulSoup(r2.text, 'html.parser')
                content_elem = soup2.select_one(content_selector)
                if content_elem:
                    # 移除script和style
                    for tag in content_elem.find_all(['script', 'style']):
                        tag.decompose()
                    content = content_elem.get_text('\n', strip=True)
                # 从详情页提取日期（如果列表里没有）
                if not date_str:
                    for sel in ['.info', '.date', '.time', '.publish-date']:
                        elem = soup2.select_one(sel)
                        if elem:
                            dm = DATE_PATTERN.search(elem.get_text())
                            if dm:
                                detail_date = dm.group()
                                break
                    if not detail_date and content:
                        dm = DATE_PATTERN.search(content[:500])
                        if dm:
                            detail_date = dm.group()
            except Exception as e:
                print(f'    详情页抓取失败: {e}')

            publish_date = parse_date(date_str or detail_date)

            # 去重检查
            dedup_hash = compute_dedup_hash(title, content)
            existing = db.query(NewsItem).filter(
                (NewsItem.source_url == url) | (NewsItem.dedup_hash == dedup_hash)
            ).first()
            if existing:
                print(f'    跳过(已存在): {title[:40]}')
                continue

            news = NewsItem(
                id=str(uuid.uuid4()),
                title=title[:512],
                content_raw=content[:5000] if content else '',
                content_summary=content[:200] if content else '',
                source_type=source.source_type,
                source_channel=source.name,
                source_url=url,
                publish_date=publish_date,
                area_tags=source.area_scope,
                industry_tags=source.industry_scope,
                info_type='policy',
                dedup_hash=dedup_hash,
                status='pending_review',
                quality_score=0,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(news)
            count += 1
            print(f'    [{count}] {title[:50]} ({publish_date})')

        except Exception as e:
            print(f'    处理失败: {e}')
            continue

    db.commit()

    # 更新采集状态
    source.last_crawl_at = datetime.now(timezone.utc)
    source.last_crawl_status = 'success'
    source.last_error_msg = None
    db.commit()

    return count


def main():
    db = SessionLocal()
    try:
        print('=' * 60)
        print('步骤1: 确保数据源存在')
        print('=' * 60)
        ensure_sources(db)

        print('\n' + '=' * 60)
        print('步骤2: 采集资讯')
        print('=' * 60)

        total_new = 0
        for cfg in SOURCES_CONFIG:
            source = db.query(CrawlSource).filter(CrawlSource.name == cfg['name']).first()
            if not source:
                continue
            print(f'\n采集源: {source.name}')
            count = crawl_source(db, source, max_items=15)
            print(f'  新增: {count} 条')
            total_new += count

        print(f'\n{"=" * 60}')
        print(f'采集完成，共新增 {total_new} 条资讯')

        # 统计
        total = db.query(NewsItem).count()
        pending = db.query(NewsItem).filter(NewsItem.status == 'pending_review').count()
        published = db.query(NewsItem).filter(NewsItem.status == 'published').count()
        sources_count = db.query(CrawlSource).filter(CrawlSource.is_active == True).count()
        print(f'数据库状态: 总计={total}, 待审核={pending}, 已发布={published}, 活跃源={sources_count}')

        # 按来源统计
        print('\n各来源统计:')
        from sqlalchemy import func
        stats = db.query(
            NewsItem.source_channel,
            func.count(NewsItem.id)
        ).group_by(NewsItem.source_channel).order_by(func.count(NewsItem.id).desc()).all()
        for channel, cnt in stats:
            print(f'  {channel}: {cnt}条')

    finally:
        db.close()


if __name__ == '__main__':
    main()
