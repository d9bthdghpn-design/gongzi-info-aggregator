"""
AI服务 - 规则引擎 + 大模型处理
"""
import hashlib
import json
import re
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
                "business_category": "policy_ref",
                "info_type": "policy",
                "area_tags": ["chaoyang"],
                "industry_tags": ["finance"],
                "opportunity_type": "监管政策",
                "is_bank_relevant": True,
            }, ensure_ascii=False)
        elif "摘要" in system_prompt or "summary" in system_prompt.lower():
            return "这是一条重要的资讯摘要，包含了核心业务信息和关键数据。"
        elif "启示" in system_prompt or "tip" in system_prompt.lower():
            return "💡 可重点关注相关企业，提供定制化金融服务方案。"
        elif "打分" in system_prompt or "score" in system_prompt.lower() or "评估" in system_prompt:
            return json.dumps({
                "event_severity": 75,
                "impact_scope": 70,
                "asset_sensitivity": 80,
                "credibility": 90,
                "novelty": 65,
                "timeliness": 80,
                "confidence": 70,
            }, ensure_ascii=False)
        return ""

    def classify_news(self, title: str, content: str) -> dict:
        """AI分类打标 - v4行动分类体系"""
        system_prompt = """你是一个银行对公业务商机情报分类专家。请根据资讯内容，给出以下分类结果：

1. business_category: 行动分类（仅限以下5个值）
   - bid_action（可投标项目）：政府采购、工程招标、中标公告、产权交易、PPP项目等可直接参与投标的商机
   - fin_demand（融资需求）：企业发债、增资扩股、定增、并购、贷款需求、融资担保、上市辅导等明确融资信号
   - account_chance（开户与结算机会）：新设企业、企业变更、迁移注册地、园区入驻等可能带来开户结算的机会
   - park_project（区域产业动态）：园区招商、产业政策落地、区域经济数据、重点项目开工、楼宇经济等区域动态
   - policy_ref（监管与政策）：金融监管、财政税收、产业政策、行业规范等需合规参考或客户提示的政策

2. info_type: 资讯类型（policy政策/bidding招投标/enterprise企业/park园区）

3. area_tags: 区域标签数组，仅限：chaoyang(朝阳)、dongcheng(东城)、tongzhou(通州)、yizhuang(亦庄/经开区)、beijing(北京市级)、national(全国性)、other(其他)；无明确区域则空数组

4. industry_tags: 行业标签数组（北京主导产业）：finance(金融)、tech(科技)、culture(文化)、business_service(商务服务)、advanced_manufacturing(先进制造)、medical_health(医药健康)、digital_economy(数字经济)、other(其他)

5. opportunity_type: 商机类型标签（单个值）：招投标、融资、并购、开户、补贴申报、土地出让、其他

6. is_bank_relevant: 是否与银行对公业务相关（true/false）。只要能转化为银行对公业务机会即为相关，仅纯娱乐/体育/社会八卦/个人生活类为false

请严格以JSON格式返回，不要有其他文字。"""

        user_content = f"标题：{title}\n内容：{content[:1000]}"

        try:
            result, input_tokens, output_tokens = self._call_ai(system_prompt, user_content)
            return json.loads(result), input_tokens, output_tokens
        except Exception as e:
            logger.error(f"AI分类失败: {e}")
            return {
                "business_category": None,
                "info_type": None,
                "area_tags": [],
                "industry_tags": [],
                "opportunity_type": "其他",
                "is_bank_relevant": True,
            }, 0, 0

    def generate_summary(self, title: str, content: str) -> str:
        """AI生成摘要"""
        system_prompt = """你是一个专业的资讯编辑。请根据给定的资讯内容，生成一段120-150字的核心摘要，要求：
1. 涵盖核心信息和关键数据
2. 语言简洁、准确
3. 适合银行客户经理快速阅读
4. 直接输出摘要内容，不要有其他说明"""

        user_content = f"标题：{title}\n内容：{content[:2000]}"

        try:
            result, in_tok, out_tok = self._call_ai(system_prompt, user_content)
            return result.strip(), in_tok, out_tok
        except Exception as e:
            logger.error(f"AI摘要生成失败: {e}")
            return content[:150] + "...", 0, 0

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
            result, in_tok, out_tok = self._call_ai(system_prompt, user_content)
            return result.strip(), in_tok, out_tok
        except Exception as e:
            logger.error(f"AI业务启示生成失败: {e}")
            return "💡 持续关注该企业动态，适时跟进营销。", 0, 0

    # 7维评分权重配置（参考Market-Impact-Radar模型）
    SCORE_WEIGHTS = {
        "event_severity": 0.20,      # 事件严重性：政策力度/资金规模/影响程度
        "impact_scope": 0.20,        # 影响范围：覆盖企业数量/行业广度/区域范围
        "asset_sensitivity": 0.15,   # 资产敏感度：对银行存贷款/投行/财资业务的直接关联度
        "credibility": 0.15,         # 可信度：来源权威性/信息确定性/是否正式文件
        "novelty": 0.10,             # 新颖度：是否新政策/新趋势/首次发布
        "timeliness": 0.10,          # 时效性：发布时间近度/窗口期紧迫度
        "confidence": 0.10,          # 置信度：信息完整度/可执行性/落地确定性
    }

    def score_quality(self, title: str, content: str) -> tuple:
        """AI 7维质量打分
        返回: (total_score: int, dimensions: dict, input_tokens: int, output_tokens: int)
        """
        system_prompt = """你是一个银行对公业务商机价值评估专家。请根据资讯内容，从以下7个维度评估这条资讯的对公业务商机价值，每个维度0-100分：

1. event_severity（事件严重性）：政策力度、资金规模、影响程度，分值越高表示事件越重大
2. impact_scope（影响范围）：覆盖企业数量、行业广度、区域范围，分值越高表示影响面越广
3. asset_sensitivity（业务相关性/资产敏感度）：与银行对公业务（存贷款、结算、投行、财资、供应链金融、普惠金融、金融市场、企业融资等）的直接关联度，分值越高表示银行业务机会越直接、越可落地。与银行业务完全无关的资讯此项应低于30分
4. credibility（可信度）：来源权威性、信息确定性、是否正式发文，分值越高表示信息越可靠
5. novelty（新颖度）：是否新政策、新趋势、首次发布，分值越高表示越新颖
6. timeliness（时效性）：发布时间近度、窗口期紧迫度，分值越高表示越及时
7. confidence（置信度）：信息完整度、可执行性、落地确定性，分值越高表示越确定可操作

请严格以JSON格式返回，格式如下：
{"event_severity": 80, "impact_scope": 70, "asset_sensitivity": 90, "credibility": 95, "novelty": 60, "timeliness": 85, "confidence": 75}
只返回JSON，不要有其他文字。"""

        user_content = f"标题：{title}\n内容：{content[:2000]}"

        try:
            result, in_tok, out_tok = self._call_ai(system_prompt, user_content)

            # 提取JSON部分（处理markdown代码块等情况）
            result = result.strip()
            if result.startswith("```"):
                # 去除 ```json 或 ``` 标记
                result = re.sub(r'^```(?:json)?\s*', '', result)
                result = re.sub(r'\s*```$', '', result)
                result = result.strip()

            # 尝试找到第一个{和最后一个}之间的内容
            start = result.find('{')
            end = result.rfind('}')
            if start != -1 and end != -1 and end > start:
                result = result[start:end + 1]

            dimensions = json.loads(result)

            # 计算加权总分
            total = 0
            for dim, weight in self.SCORE_WEIGHTS.items():
                score = dimensions.get(dim, 50)
                score = max(0, min(100, int(score)))
                dimensions[dim] = score
                total += score * weight

            total_score = int(round(total))
            total_score = max(0, min(100, total_score))

            return total_score, dimensions, in_tok, out_tok
        except Exception as e:
            logger.error(f"AI 7维打分失败: {e}")
            # 失败时返回默认中等分数
            default_dims = {dim: 50 for dim in self.SCORE_WEIGHTS}
            return 50, default_dims, 0, 0

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
            classification, in_tok, out_tok = self.classify_news(news.title, news.content_raw or "")
            input_tokens_total += in_tok
            output_tokens_total += out_tok

            news.business_category = classification.get("business_category")
            news.info_type = classification.get("info_type")
            news.area_tags = classification.get("area_tags", [])
            news.industry_tags = classification.get("industry_tags", [])

            # 2. 生成摘要
            summary, in_tok, out_tok = self.generate_summary(news.title, news.content_raw or "")
            news.content_summary = summary
            input_tokens_total += in_tok
            output_tokens_total += out_tok

            # 3. 生成业务启示
            tip, in_tok, out_tok = self.generate_business_tip(news.title, news.content_raw or "")
            news.business_tip = tip
            input_tokens_total += in_tok
            output_tokens_total += out_tok

            # 4. 7维质量打分
            score, dimensions, in_tok, out_tok = self.score_quality(news.title, news.content_raw or "")
            news.quality_score = score
            news.score_dimensions = dimensions
            input_tokens_total += in_tok
            output_tokens_total += out_tok

            # 更新状态：取消审核，AI处理后直接发布
            # 若AI判断与银行业务完全无关，则标记为rejected（在classify结果中判断）
            is_bank_relevant = classification.get("is_bank_relevant", True)
            if is_bank_relevant is False:
                news.status = "rejected"
            else:
                news.status = "published"

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
