"""
区域标签规范化脚本
将已有资讯的area_tags统一为标准7类：
chaoyang(朝阳)、dongcheng(东城)、tongzhou(通州)、yizhuang(亦庄)、beijing(北京市级)、national(全国性)、other(其他)
"""
import os
import sys
import json

os.environ['DATABASE_URL'] = 'postgresql://postgres.sljoxgawgfdhchyibvdx:Ljz8248282%40@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres'
os.environ['ENVIRONMENT'] = 'production'
os.environ['JWT_SECRET_KEY'] = 'gOINcX8fj49sh2rUyna6W1JuBeqtFzTVMERQvKoYZPAbC7lH'
os.environ['CORS_ORIGINS'] = 'https://gongzi-info-aggregator.onrender.com'

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.database import SessionLocal
from app.models.news import NewsItem
from sqlalchemy import func

# 标准区域标签
STANDARD_AREAS = {'chaoyang', 'dongcheng', 'tongzhou', 'yizhuang', 'beijing', 'national', 'other'}

# 旧标签→新标签映射
AREA_MAP = {
    # 朝阳
    'chaoyang': 'chaoyang',
    '朝阳': 'chaoyang',
    '朝阳区': 'chaoyang',
    # 东城
    'dongcheng': 'dongcheng',
    '东城': 'dongcheng',
    '东城区': 'dongcheng',
    # 通州
    'tongzhou': 'tongzhou',
    '通州': 'tongzhou',
    '通州区': 'tongzhou',
    # 亦庄
    'yizhuang': 'yizhuang',
    '亦庄': 'yizhuang',
    '经开区': 'yizhuang',
    '北京经开区': 'yizhuang',
    '亦庄经开区': 'yizhuang',
    '北京经济技术开发区': 'yizhuang',
    # 北京市级
    'beijing': 'beijing',
    '北京': 'beijing',
    '北京市': 'beijing',
    '市级': 'beijing',
    '北京市级': 'beijing',
    # 全国
    'national': 'national',
    '全国': 'national',
    '国家': 'national',
    '中央': 'national',
    '全国性': 'national',
    # 其他区归为other
    'haidian': 'other', '海淀': 'other', '海淀区': 'other',
    'fengtai': 'other', '丰台': 'other', '丰台区': 'other',
    'xicheng': 'other', '西城': 'other', '西城区': 'other',
    'shijingshan': 'other', '石景山': 'other', '石景山区': 'other',
    'changping': 'other', '昌平': 'other', '昌平区': 'other',
    'daxing': 'other', '大兴': 'other', '大兴区': 'other',
    'shunyi': 'other', '顺义': 'other', '顺义区': 'other',
    'fangshan': 'other', '房山': 'other', '房山区': 'other',
    'mentougou': 'other', '门头沟': 'other',
    'pinggu': 'other', '平谷': 'other',
    'huairou': 'other', '怀柔': 'other',
    'miyun': 'other', '密云': 'other',
    'yanqing': 'other', '延庆': 'other',
}


def normalize_area_tags(tags):
    """规范化区域标签"""
    if not tags:
        return []
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except:
            tags = [tags]
    result = []
    for tag in tags:
        if not tag:
            continue
        normalized = AREA_MAP.get(tag, tag if tag in STANDARD_AREAS else 'other')
        if normalized not in result:
            result.append(normalized)
    return result


def main():
    db = SessionLocal()
    try:
        print('=' * 60)
        print('区域标签规范化')
        print('=' * 60)

        # 迁移前统计
        print('\n迁移前 area_tags 分布:')
        all_news = db.query(NewsItem).filter(NewsItem.is_deleted == False).all()
        tag_counts = {}
        for news in all_news:
            tags = news.area_tags or []
            for t in tags:
                tag_counts[t] = tag_counts.get(t, 0) + 1
        for tag, cnt in sorted(tag_counts.items(), key=lambda x: -x[1]):
            print(f'  {tag}: {cnt}条')

        # 执行规范化
        updated = 0
        new_counts = {tag: 0 for tag in STANDARD_AREAS}
        new_counts['(空)'] = 0

        for news in all_news:
            old_tags = news.area_tags or []
            new_tags = normalize_area_tags(old_tags)
            if old_tags != new_tags:
                news.area_tags = new_tags
                updated += 1
            if not new_tags:
                new_counts['(空)'] += 1
            else:
                for t in new_tags:
                    new_counts[t] = new_counts.get(t, 0) + 1

        db.commit()

        print(f'\n规范化完成: 更新 {updated} 条')
        print('\n规范化后 area_tags 分布:')
        for tag, cnt in sorted(new_counts.items(), key=lambda x: -x[1]):
            if cnt > 0:
                print(f'  {tag}: {cnt}条')

    finally:
        db.close()


if __name__ == '__main__':
    main()
