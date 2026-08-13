"""
事件聚类服务 - 同一政策/事件多源发布自动去重聚合
算法：标题相似度 + 发布时间窗口 + 关键词重叠
"""
import re
import uuid
import logging
from datetime import timedelta
from difflib import SequenceMatcher
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from app.models import NewsItem, EventCluster

logger = logging.getLogger(__name__)


# 中文停用词（用于关键词提取）
STOP_WORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个",
    "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好",
    "自己", "这", "那", "关于", "通知", "公告", "公示", "发布", "印发", "开展",
    "组织", "进行", "工作", "项目", "企业", "单位", "部门", "北京市", "北京",
    "年", "月", "日", "第", "批", "号", "文", "办", "局", "委", "部",
    "（", "）", "(", ")", "《", "》", "，", "。", "、", "：", "；",
}

# 聚类参数
TITLE_SIMILARITY_THRESHOLD = 0.55  # 标题相似度阈值
TIME_WINDOW_DAYS = 7  # 时间窗口（天）
KEYWORD_OVERLAP_MIN = 2  # 最小关键词重叠数
MIN_CLUSTER_SIZE = 2  # 最小聚类规模（单条不创建聚类）


def extract_keywords(text: str) -> set:
    """从标题中提取关键词（简单分词：2-4字的中文词组）"""
    if not text:
        return set()

    # 移除标点和停用词
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', ' ', text)
    words = set()

    # 提取2-4字的中文词组
    for length in [2, 3, 4]:
        for i in range(len(text) - length + 1):
            word = text[i:i + length]
            if word not in STOP_WORDS and len(word.strip()) >= 2:
                words.add(word)

    # 也提取英文/数字词
    for word in re.findall(r'[a-zA-Z0-9]+', text):
        if len(word) >= 2 and word.lower() not in STOP_WORDS:
            words.add(word)

    return words


def title_similarity(title1: str, title2: str) -> float:
    """计算两个标题的相似度（SequenceMatcher）"""
    if not title1 or not title2:
        return 0.0
    return SequenceMatcher(None, title1, title2).ratio()


def keyword_overlap(title1: str, title2: str) -> int:
    """计算两个标题的关键词重叠数"""
    kw1 = extract_keywords(title1)
    kw2 = extract_keywords(title2)
    return len(kw1 & kw2)


def is_same_event(news1: NewsItem, news2: NewsItem) -> bool:
    """判断两条资讯是否属于同一事件"""
    # 1. 标题相似度
    sim = title_similarity(news1.title, news2.title)
    if sim < TITLE_SIMILARITY_THRESHOLD:
        return False

    # 2. 发布时间窗口
    if news1.publish_date and news2.publish_date:
        delta = abs((news1.publish_date - news2.publish_date).days)
        if delta > TIME_WINDOW_DAYS:
            return False
    elif news1.publish_date is None or news2.publish_date is None:
        # 没有日期的资讯不参与聚类
        return False

    # 3. 关键词重叠（相似度较高时可放宽关键词要求）
    overlap = keyword_overlap(news1.title, news2.title)
    if sim >= 0.7:
        # 高相似度时只要有1个关键词重叠即可
        if overlap < 1:
            return False
    else:
        if overlap < KEYWORD_OVERLAP_MIN:
            return False

    return True


class EventClusterService:
    """事件聚类服务"""

    def __init__(self, db: Session):
        self.db = db

    def cluster_all_news(self, status_filter: List[str] = None) -> Tuple[int, int]:
        """对全量资讯运行聚类
        返回: (聚类数量, 涉及资讯数量)
        """
        if status_filter is None:
            status_filter = ["published", "pending_review"]

        # 1. 清除旧的聚类关联
        old_clusters = self.db.query(EventCluster).all()
        for cluster in old_clusters:
            self.db.delete(cluster)
        self.db.query(NewsItem).update({NewsItem.event_cluster_id: None})
        self.db.commit()
        logger.info(f"已清除 {len(old_clusters)} 个旧聚类")

        # 2. 获取待聚类资讯
        news_list = self.db.query(NewsItem).filter(
            NewsItem.status.in_(status_filter),
            NewsItem.publish_date.isnot(None),
            NewsItem.is_deleted == False
        ).order_by(NewsItem.publish_date.asc()).all()

        logger.info(f"待聚类资讯: {len(news_list)} 条")

        if len(news_list) < MIN_CLUSTER_SIZE:
            return 0, 0

        # 3. 贪心聚类
        clusters: List[List[NewsItem]] = []
        assigned = set()

        for i, news in enumerate(news_list):
            if news.id in assigned:
                continue

            # 新建一个聚类
            current_cluster = [news]
            assigned.add(news.id)

            # 寻找同事件的其他资讯
            for j in range(i + 1, len(news_list)):
                other = news_list[j]
                if other.id in assigned:
                    continue

                # 与聚类中任意一条比较（取最大相似度）
                max_sim = 0
                for member in current_cluster:
                    sim = title_similarity(member.title, other.title)
                    if sim > max_sim:
                        max_sim = sim

                if max_sim >= TITLE_SIMILARITY_THRESHOLD:
                    # 详细判断
                    if any(is_same_event(member, other) for member in current_cluster):
                        current_cluster.append(other)
                        assigned.add(other.id)

            if len(current_cluster) >= MIN_CLUSTER_SIZE:
                clusters.append(current_cluster)

        # 4. 保存聚类结果
        total_news_in_clusters = 0
        for cluster_news in clusters:
            self._save_cluster(cluster_news)
            total_news_in_clusters += len(cluster_news)

        self.db.commit()
        logger.info(f"聚类完成: {len(clusters)} 个事件, 涉及 {total_news_in_clusters} 条资讯")

        return len(clusters), total_news_in_clusters

    def _save_cluster(self, news_list: List[NewsItem]):
        """保存一个聚类"""
        if len(news_list) < MIN_CLUSTER_SIZE:
            return

        # 选择代表资讯（最早发布或最高质量分）
        representative = min(news_list, key=lambda n: (n.publish_date, -n.quality_score))

        # 收集来源渠道
        sources = list(set(n.source_channel for n in news_list if n.source_channel))

        # 计算日期范围
        dates = [n.publish_date for n in news_list if n.publish_date]
        first_date = min(dates) if dates else None
        last_date = max(dates) if dates else None

        # 最高质量分
        max_score = max(n.quality_score or 0 for n in news_list)

        # 判断事件类型
        event_type = self._infer_event_type(news_list)

        # 创建聚类
        cluster = EventCluster(
            id=str(uuid.uuid4()),
            title=representative.title,
            description=f"该事件由 {len(news_list)} 条资讯聚合，涉及 {len(sources)} 个来源渠道",
            event_type=event_type,
            news_count=len(news_list),
            news_ids=[str(n.id) for n in news_list],
            source_channels=sources,
            first_publish_date=first_date,
            last_publish_date=last_date,
            max_quality_score=max_score,
        )
        self.db.add(cluster)
        self.db.flush()

        # 更新资讯的聚类关联
        for news in news_list:
            news.event_cluster_id = cluster.id

    def _infer_event_type(self, news_list: List[NewsItem]) -> str:
        """推断事件类型"""
        info_types = [n.info_type for n in news_list if n.info_type]
        if not info_types:
            return "other"

        # 取出现最多的类型
        type_count = {}
        for t in info_types:
            type_count[t] = type_count.get(t, 0) + 1
        return max(type_count, key=type_count.get)

    def get_clusters(self, page: int = 1, page_size: int = 20,
                     event_type: str = None) -> Tuple[List[EventCluster], int]:
        """获取聚类列表"""
        query = self.db.query(EventCluster)

        if event_type:
            query = query.filter(EventCluster.event_type == event_type)

        total = query.count()
        clusters = query.order_by(EventCluster.first_publish_date.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return clusters, total

    def get_cluster_detail(self, cluster_id: str) -> Optional[EventCluster]:
        """获取聚类详情（含关联资讯）"""
        cluster = self.db.query(EventCluster).filter(EventCluster.id == cluster_id).first()
        if not cluster:
            return None

        # 加载关联资讯
        news_list = self.db.query(NewsItem).filter(
            NewsItem.id.in_(cluster.news_ids)
        ).order_by(NewsItem.publish_date.asc()).all()

        cluster.news_items = news_list  # 动态附加
        return cluster

    def cluster_single_news(self, news_id: str) -> Optional[str]:
        """对单条新资讯进行聚类（增量聚类）
        返回: 聚类ID（如果被归入某个聚类）
        """
        news = self.db.query(NewsItem).filter(NewsItem.id == news_id).first()
        if not news or not news.publish_date:
            return None

        # 查找最近的聚类（时间窗口内）
        recent_clusters = self.db.query(EventCluster).filter(
            EventCluster.first_publish_date <= news.publish_date + timedelta(days=TIME_WINDOW_DAYS),
            EventCluster.last_publish_date >= news.publish_date - timedelta(days=TIME_WINDOW_DAYS),
        ).all()

        best_cluster = None
        best_sim = 0

        for cluster in recent_clusters:
            # 获取聚类中的代表资讯
            cluster_news = self.db.query(NewsItem).filter(
                NewsItem.id.in_(cluster.news_ids)
            ).all()

            for member in cluster_news:
                if is_same_event(member, news):
                    sim = title_similarity(member.title, news.title)
                    if sim > best_sim:
                        best_sim = sim
                        best_cluster = cluster
                    break

        if best_cluster:
            # 加入现有聚类
            news_id_str = str(news.id)
            if news_id_str not in best_cluster.news_ids:
                best_cluster.news_ids.append(news_id_str)
                best_cluster.news_count = len(best_cluster.news_ids)

                if news.source_channel and news.source_channel not in best_cluster.source_channels:
                    best_cluster.source_channels.append(news.source_channel)

                if news.publish_date:
                    if best_cluster.first_publish_date is None or news.publish_date < best_cluster.first_publish_date:
                        best_cluster.first_publish_date = news.publish_date
                    if best_cluster.last_publish_date is None or news.publish_date > best_cluster.last_publish_date:
                        best_cluster.last_publish_date = news.publish_date

                if (news.quality_score or 0) > best_cluster.max_quality_score:
                    best_cluster.max_quality_score = news.quality_score

            news.event_cluster_id = best_cluster.id
            self.db.commit()
            return best_cluster.id

        return None


# 服务单例（需要db session，不做全局单例）
def get_cluster_service(db: Session) -> EventClusterService:
    return EventClusterService(db)
