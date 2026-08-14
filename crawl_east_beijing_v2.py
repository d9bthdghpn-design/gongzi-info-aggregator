"""
第二批数据源采集脚本
- 亦庄经开区（通知公告+政策文件+工作动态）
- 北京市国资委（激活现有源并采集）
- 中关村朝阳园（探测+采集）
- 朝阳区各局委办（尝试采集）
"""
import os
import sys
import hashlib
import re
from datetime import datetime
from urllib.parse import urljoin

os.environ['DATABASE_URL'] = 'postgresql://postgres.sljoxgawgfdhchyibvdx:Ljz8248282%40@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres'
os.environ['ENVIRONMENT'] = 'production'
os.environ['JWT_SECRET_KEY'] = 'gOINcX8fj49sh2rUyna6W1JuBeqtFzTVMERQvKoYZPAbC7lH'
os.environ['CORS_ORIGINS'] = 'https://gongzi-info-aggregator.onrender.com'

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.news import NewsItem, CrawlSource
from app.services.ai_service import ai_service

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# ============ 数据源配置 ============
SOURCES = [
    {
        'name': '北京经开区-通知公告',
        'source_type': 'gov',
        'crawl_type': 'web',
        'entry_url': 'https://kfqgw.beijing.gov.cn/zwgkkfq/tzgg/',
        'area_scope': 'yizhuang',
        'industry_scope': 'all',
        'priority': 8,
        'list_selector': 'ul.list li',
        'content_selectors': ['div.TRS_Editor', 'div.content', 'div.article-content', 'div#zoom'],
        'encoding': 'utf-8',
        'source_channel': '北京经开区管委会',
    },
    {
        'name': '北京经开区-政策文件',
        'source_type': 'gov',
        'crawl_type': 'web',
        'entry_url': 'https://kfqgw.beijing.gov.cn/zwgkkfq/2024zcwj/',
        'area_scope': 'yizhuang',
        'industry_scope': 'all',
        'priority': 9,
        'list_selector': 'ul.list li',
        'content_selectors': ['div.TRS_Editor', 'div.content', 'div.article-content', 'div#zoom'],
        'encoding': 'utf-8',
        'source_channel': '北京经开区管委会',
    },
    {
        'name': '北京经开区-工作动态',
        'source_type': 'gov',
        'crawl_type': 'web',
        'entry_url': 'https://kfqgw.beijing.gov.cn/ywdt/gzdt/index.html',
        'area_scope': 'yizhuang',
        'industry_scope': 'all',
        'priority': 7,
        'list_selector': 'ul.list li',
        'content_selectors': ['div.TRS_Editor', 'div.content', 'div.article-content', 'div#zoom'],
        'encoding': 'utf-8',
        'source_channel': '北京经开区管委会',
    },
]


def ensure_sources(db: Session):
    """确保数据源记录存在"""
    for cfg in SOURCES:
        existing = db.query(CrawlSource).filter(CrawlSource.name == cfg['name']).first()
        if existing:
            existing.entry_url = cfg['entry_url']
            existing.is_active = True
            existing.selector_config = {
                'list_selector': cfg['list_selector'],
                'content_selectors': cfg['content_selectors'],
                'encoding': cfg['encoding'],
            }
            print(f"  更新源: {cfg['name']}")
        else:
            source = CrawlSource(
                name=cfg['name'],
                source_type=cfg['source_type'],
                crawl_type=cfg['crawl_type'],
                entry_url=cfg['entry_url'],
                area_scope=cfg['area_scope'],
                industry_scope=cfg['industry_scope'],
                priority=cfg['priority'],
                is_active=True,
                selector_config={
                    'list_selector': cfg['list_selector'],
                    'content_selectors': cfg['content_selectors'],
                    'encoding': cfg['encoding'],
                },
            )
            db.add(source)
            print(f"  新增源: {cfg['name']}")
    db.commit()


def activate_gzw(db: Session):
    """激活国资委现有源"""
    gzw = db.query(CrawlSource).filter(CrawlSource.name.contains('国资委')).first()
    if gzw:
        gzw.is_active = True
        db.commit()
        print(f"  已激活国资委源: {gzw.name} (URL: {gzw.entry_url})")
        return gzw
    else:
        print("  未找到国资委现有源，尝试新建...")
        source = CrawlSource(
            name='北京市国资委',
            source_type='gov',
            crawl_type='web',
            entry_url='https://gzw.beijing.gov.cn/zwgk/tzgg/',
            area_scope='beijing',
            industry_scope='all',
            priority=8,
            is_active=True,
            selector_config={'encoding': 'utf-8'},
        )
        db.add(source)
        db.commit()
        print(f"  新建国资委源")
        return source


def fetch_page(url, encoding=None):
    """获取页面"""
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        if encoding:
            resp.encoding = encoding
        else:
            resp.encoding = resp.apparent_encoding
        return resp.text
    except Exception as e:
        print(f"    获取页面失败 {url}: {e}")
        return None


def extract_list_items(html, base_url, list_selector):
    """提取列表项"""
    soup = BeautifulSoup(html, 'html.parser')
    items = []
    for li in soup.select(list_selector):
        a = li.find('a')
        if not a:
            continue
        title = a.get_text(strip=True)
        href = a.get('href', '')
        if not href or not title:
            continue
        full_url = urljoin(base_url, href)
        # 提取日期
        date_text = li.get_text()
        date_match = re.search(r'(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})', date_text)
        publish_date = None
        if date_match:
            try:
                publish_date = datetime(int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))).date()
            except:
                pass
        items.append({'title': title, 'url': full_url, 'publish_date': publish_date})
    return items


def extract_content(html, content_selectors):
    """提取正文"""
    soup = BeautifulSoup(html, 'html.parser')
    for sel in content_selectors:
        elem = soup.select_one(sel)
        if elem:
            text = elem.get_text(separator='\n', strip=True)
            if len(text) > 50:
                return text[:5000]
    # fallback: 最大文本块
    paragraphs = soup.find_all(['p', 'div'])
    best = ''
    for p in paragraphs:
        t = p.get_text(strip=True)
        if len(t) > len(best):
            best = t
    return best[:3000] if best else ''


def crawl_source(db: Session, cfg, max_items=12):
    """采集单个源"""
    print(f"\n  采集: {cfg['name']}")
    html = fetch_page(cfg['entry_url'], cfg.get('encoding'))
    if not html:
        return 0

    items = extract_list_items(html, cfg['entry_url'], cfg['list_selector'])
    print(f"    列表找到 {len(items)} 条")

    count = 0
    for item in items[:max_items]:
        # 去重
        existing = db.query(NewsItem).filter(NewsItem.source_url == item['url']).first()
        if existing:
            continue

        # 抓取正文
        content_html = fetch_page(item['url'], cfg.get('encoding'))
        content = extract_content(content_html, cfg['content_selectors']) if content_html else ''

        # 计算去重哈希
        dedup_hash = hashlib.md5((item['title'] + (content[:500] if content else '')).encode('utf-8')).hexdigest()
        existing_hash = db.query(NewsItem).filter(NewsItem.dedup_hash == dedup_hash).first()
        if existing_hash:
            continue

        news = NewsItem(
            title=item['title'][:200],
            content_raw=content,
            source_url=item['url'],
            source_channel=cfg['source_channel'],
            source_type=cfg['source_type'],
            publish_date=item['publish_date'] or datetime.now().date(),
            area_tags=[cfg['area_scope']] if cfg['area_scope'] != 'all' else [],
            status='pending_review',
            quality_score=0,
            dedup_hash=dedup_hash,
        )
        db.add(news)
        db.commit()
        count += 1

        # AI处理
        try:
            ai_service.process_news(db, news.id)
            db.commit()
        except Exception as e:
            print(f"    AI处理失败: {e}")

    print(f"    新增 {count} 条")
    return count


def crawl_gzw(db: Session, source, max_items=10):
    """采集国资委"""
    print(f"\n  采集: {source.name}")
    html = fetch_page(source.entry_url, 'utf-8')
    if not html:
        print("    页面获取失败")
        return 0

    soup = BeautifulSoup(html, 'html.parser')
    items = []
    # 通用匹配
    for a in soup.find_all('a', href=True):
        title = a.get_text(strip=True)
        href = a.get('href', '')
        parent_text = a.parent.get_text() if a.parent else ''
        if re.search(r'20\d{2}', parent_text + title) and len(title) > 10:
            full_url = urljoin(source.entry_url, href)
            date_match = re.search(r'(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})', parent_text)
            publish_date = None
            if date_match:
                try:
                    publish_date = datetime(int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))).date()
                except:
                    pass
            items.append({'title': title, 'url': full_url, 'publish_date': publish_date})

    print(f"    找到 {len(items)} 条")
    count = 0
    for item in items[:max_items]:
        existing = db.query(NewsItem).filter(NewsItem.source_url == item['url']).first()
        if existing:
            continue
        content_html = fetch_page(item['url'], 'utf-8')
        content = extract_content(content_html, ['div.TRS_Editor', 'div.content', 'div.article-content', 'div#zoom']) if content_html else ''
        dedup_hash = hashlib.md5((item['title'] + (content[:500] if content else '')).encode('utf-8')).hexdigest()
        if db.query(NewsItem).filter(NewsItem.dedup_hash == dedup_hash).first():
            continue
        news = NewsItem(
            title=item['title'][:200],
            content_raw=content,
            source_url=item['url'],
            source_channel='北京市国资委',
            source_type='gov',
            publish_date=item['publish_date'] or datetime.now().date(),
            area_tags=['beijing'],
            status='pending_review',
            quality_score=0,
            dedup_hash=dedup_hash,
        )
        db.add(news)
        db.commit()
        count += 1
        try:
            ai_service.process_news(db, news.id)
            db.commit()
        except Exception as e:
            print(f"    AI处理失败: {e}")
    print(f"    新增 {count} 条")
    return count


def main():
    print('=' * 60)
    print('第二批数据源采集')
    print('=' * 60)

    db = SessionLocal()
    try:
        # 1. 确保亦庄数据源
        print('\n[1/4] 确保亦庄数据源...')
        ensure_sources(db)

        # 2. 激活国资委
        print('\n[2/4] 激活国资委数据源...')
        gzw_source = activate_gzw(db)

        # 3. 采集亦庄
        print('\n[3/4] 采集亦庄经开区...')
        total_yizhuang = 0
        for cfg in SOURCES:
            total_yizhuang += crawl_source(db, cfg)

        # 4. 采集国资委
        print('\n[4/4] 采集国资委...')
        total_gzw = crawl_gzw(db, gzw_source)

        # 统计
        print('\n' + '=' * 60)
        print('采集完成统计:')
        print(f'  亦庄经开区: {total_yizhuang} 条')
        print(f'  北京市国资委: {total_gzw} 条')
        print(f'  合计新增: {total_yizhuang + total_gzw} 条')

        total = db.query(NewsItem).filter(NewsItem.is_deleted == False).count()
        pending = db.query(NewsItem).filter(NewsItem.status == 'pending_review').count()
        published = db.query(NewsItem).filter(NewsItem.status == 'published').count()
        active_sources = db.query(CrawlSource).filter(CrawlSource.is_active == True).count()
        print(f'\n数据库状态: 总计{total}条, 待审核{pending}条, 已发布{published}条, 活跃源{active_sources}个')

    finally:
        db.close()


if __name__ == '__main__':
    main()
