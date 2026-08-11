"""
AI服务 - 规则引擎 + 大模型处理
"""
import hashlib
import json
import time
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
import logging
logger = logging.getLogger(__name__)
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.models import NewsItem, TagDictionary, AIProcessLog
from app.core.exceptions import BusinessException


class RuleEngine:
    """规则引擎 - 前置过滤，降低AI成本"""

    def __init__(self, db: Session):
        self.db = db
        self._load_keywords()

    def _load_keywords(self):
        """加载关键词字典"""
        tags = self.db.query(TagDictionary).filter(
            TagDictionary.is_active == True
        ).all()

        self.area_keywords = {}
        self.industry_keywords = {}
        self.business_keywords = {}
        self.noise_keywords = [
            "招聘", "求职", "简历", "广告", "推广", "优惠", "促销",
            "娱乐", "八卦", "明星", "综艺", "游戏", "体育",
        ]

        for tag in tags:
            keywords = tag.keywords or []
            if tag.tag_type == "area":
                self.area_keywords[tag.tag_code] = keywords + [tag.tag_name]
            elif tag.tag_type == "industry":
                self.industry_keywords[tag.tag_code] = keywords + [tag.tag_name]
            elif tag.tag_type == "business":
                self.business_keywords[tag.tag_code] = keywords + [tag.tag_name]

    def filter_noise(self, title: str, content: str = "") -> bool:
        """噪音过滤，返回True表示应该过滤掉"""
        text = (title + content).lower()
        for keyword in self.noise_keywords:
            if keyword.lower() in text:
                return True
        return False

    def match_area(self, title: str, content: str = "") -> List[str]:
        """匹配区域标签"""
        text = title + content
        matched = []
        for area_code, keywords in self.area_keywords.items():
            for kw in keywords:
                if kw in text:
                    matched.append(area_code)
                    break
        return matched

    def match_industry(self, title: str, content: str = "") -> List[str]:
        """匹配行业标签"""
        text = title + content
        matched = []
        for industry_code, keywords in self.industry_keywords.items():
            for kw in keywords:
                if kw in text:
                    matched.append(industry_code)
                    break
        return matched

    def should_process_by_ai(self, title: str, content: str = "") -> bool:
        """判断是否需要AI处理（有匹配的关键词才处理）"""
        if self.filter_noise(title, content):
            return False

        areas = self.match_area(title, content)
        industries = self.match_industry(title, content)

        # 有区域或行业匹配才进入AI处理
        return len(areas) > 0 or len(industries) > 0


class AIService:
    """AI处理服务"""

    def __init__(self):
        self.client = None
        self._init_client()

    def _init_client(self):
        """初始化AI客户端"""
        if not settings.AI_API_KEY:
            logger.warning("AI API Key未配置，AI功能将使用模拟模式")
            return

        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=settings.AI_API_KEY,
                base_url=settings.AI_BASE_URL if settings.AI_BASE_URL else None,
            )
        except Exception as e:
            logger.warning(f"AI客户端初始化失败: {e}")
            self.client = None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _call_ai(self, system_prompt: str, user_content: str) -> tuple[str, int, int]:
        """调用AI接口"""
        start_time = time.time()

        if not self.client:
            # 模拟模式：返回预设结果
            return self._mock_response(system_prompt, user_content), 100, 200

        response = self.client.chat.completions.create(
            model=settings.AI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=settings.AI_TEMPERATURE,
            max_tokens=settings.AI_MAX_TOKENS,
        )

        content = response.choices[0].message.content
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        duration_ms = int((time.time() - start_time) * 1000)

        return content, input_tokens, output_tokens

    def _mock_response(self, system_prompt: str, user_content: str) -> str:
        """模拟AI响应（开发测试用）"""
        if "分类" in system_prompt or "classify" in system_prompt.lower():
            return json.dumps({
                "business_category": "loan",
                "info_type": "policy",
                "area_tags": ["chaoyang"],
                "industry_tags": ["tech"],
            }, ensure_ascii=False)
        elif "摘要" in system_prompt or "summary" in system_prompt.lower():
            return "这是一条重要的资讯摘要，包含了核心业务信息和关键数据。"
        elif "启示" in system_prompt or "tip" in system_prompt.lower():
            return "💡 可重点关注相关企业，提供定制化金融服务方案。"
        elif "打分" in system_prompt or "score" in system_prompt.lower():
            return "75"
        return ""

    def classify_news(self, title: str, content: str) -> dict:
        """AI分类打标"""
        system_prompt = """你是一个银行对公业务资讯分类专家。请根据资讯内容，给出以下分类结果：
1. business_category: 业务分类（deposit存款/loan贷款/investment_bank投行/treasury财资/supply_chain供应链）
2. info_type: 资讯类型（policy政策/bidding招投标/enterprise企业/park园区）
3. area_tags: 区域标签数组（如chaoyang朝阳区、haidian海淀区、fengtai丰台区等）
4. industry_tags: 行业标签数组（如tech信息技术、finance金融、manufacturing制造业等）

请严格以JSON格式返回，不要有其他文字。"""

        user_content = f"标题：{title}\n内容：{content[:1000]}"

        try:
            result, input_tokens, output_tokens = self._call_ai(system_prompt, user_content)
            return json.loads(result)
        except Exception as e:
            logger.error(f"AI分类失败: {e}")
            return {
                "business_category": None,
                "info_type": None,
                "area_tags": [],
                "industry_tags": [],
            }

    def generate_summary(self, title: str, content: str) -> str:
        """AI生成摘要"""
        system_prompt = """你是一个专业的资讯编辑。请根据给定的资讯内容，生成一段120-150字的核心摘要，要求：
1. 涵盖核心信息和关键数据
2. 语言简洁、准确
3. 适合银行客户经理快速阅读
4. 直接输出摘要内容，不要有其他说明"""

        user_content = f"标题：{title}\n内容：{content[:2000]}"

        try:
            result, _, _ = self._call_ai(system_prompt, user_content)
            return result.strip()
        except Exception as e:
            logger.error(f"AI摘要生成失败: {e}")
            return content[:150] + "..."

    def generate_business_tip(self, title: str, content: str) -> str:
        """AI生成业务启示"""
        system_prompt = """你是一个资深的银行对公业务专家。请根据给定的资讯内容，生成1-2条具体的营销建议/业务启示，要求：
1. 具体、可操作，不要空泛
2. 结合银行对公业务场景（存款、贷款、投行、财资、供应链等）
3. 每条建议不超过50字
4. 以💡开头，用分号分隔多条建议
5. 直接输出建议内容"""

        user_content = f"标题：{title}\n内容：{content[:2000]}"

        try:
            result, _, _ = self._call_ai(system_prompt, user_content)
            return result.strip()
        except Exception as e:
            logger.error(f"AI业务启示生成失败: {e}")
            return "💡 持续关注该企业动态，适时跟进营销。"

    def score_quality(self, title: str, content: str) -> int:
        """AI质量打分（0-100分）"""
        system_prompt = """你是一个银行商机价值评估专家。请根据资讯内容，评估这条资讯的对公业务商机价值，给出0-100的分数。
评分维度：
1. 涉及金额大小（30分）
2. 企业规模/重要性（25分）
3. 业务相关性（25分）
4. 时效性（20分）
只返回数字分数，不要有其他文字。"""

        user_content = f"标题：{title}\n内容：{content[:2000]}"

        try:
            result, _, _ = self._call_ai(system_prompt, user_content)
            score = int(result.strip())
            return max(0, min(100, score))
        except Exception as e:
            logger.error(f"AI质量打分失败: {e}")
            return 50

    def process_news(self, db: Session, news_id: str) -> bool:
        """完整处理一条资讯"""
        news = db.query(NewsItem).filter(NewsItem.id == news_id).first()
        if not news:
            return False

        start_time = time.time()
        input_tokens_total = 0
        output_tokens_total = 0

        try:
            # 1. 分类打标
            classification = self.classify_news(news.title, news.content_raw or "")
            input_tokens_total += 100
            output_tokens_total += 100

            news.business_category = classification.get("business_category")
            news.info_type = classification.get("info_type")
            news.area_tags = classification.get("area_tags", [])
            news.industry_tags = classification.get("industry_tags", [])

            # 2. 生成摘要
            news.content_summary = self.generate_summary(news.title, news.content_raw or "")
            input_tokens_total += 200
            output_tokens_total += 150

            # 3. 生成业务启示
            news.business_tip = self.generate_business_tip(news.title, news.content_raw or "")
            input_tokens_total += 200
            output_tokens_total += 100

            # 4. 质量打分
            news.quality_score = self.score_quality(news.title, news.content_raw or "")
            input_tokens_total += 150
            output_tokens_total += 10

            # 更新状态
            news.status = "pending_review"

            duration_ms = int((time.time() - start_time) * 1000)

            # 记录AI处理日志
            log = AIProcessLog(
                news_id=news.id,
                process_type="all",
                input_tokens=input_tokens_total,
                output_tokens=output_tokens_total,
                model_version=settings.AI_MODEL,
                raw_output=json.dumps(classification, ensure_ascii=False),
                duration_ms=duration_ms,
                success=True,
            )
            db.add(log)
            db.commit()

            return True

        except Exception as e:
            logger.error(f"AI处理资讯失败 {news_id}: {e}")
            news.status = "ai_failed"
            db.commit()
            return False

    @staticmethod
    def compute_dedup_hash(title: str, content: str) -> str:
        """计算内容去重哈希"""
        # 使用标题+正文前500字的MD5
        text = title + (content[:500] if content else "")
        return hashlib.md5(text.encode("utf-8")).hexdigest()


# 服务单例
ai_service = AIService()
