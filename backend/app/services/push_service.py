"""
推送服务 - 飞书/企微机器人 Webhook
"""
import json
import logging
import httpx
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


def _post_json(url: str, payload: dict) -> dict:
    """发送 POST JSON 请求"""
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.post(url, json=payload)
            return resp.json()
    except Exception as e:
        logger.error(f"Webhook 请求异常: {e}")
        return {}


def _send_feishu(webhook_url: str, text: str, secret: str = "") -> bool:
    """发送飞书机器人消息"""
    payload = {
        "msg_type": "text",
        "content": {"text": text},
    }
    if secret:
        import time
        import hmac
        import hashlib
        import base64
        timestamp = str(int(time.time()))
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"), digestmod=hashlib.sha256
        ).digest()
        sign = base64.b64encode(hmac_code).decode("utf-8")
        payload["timestamp"] = timestamp
        payload["sign"] = sign

    result = _post_json(webhook_url, payload)
    if result.get("code") == 0 or result.get("StatusCode") == 0:
        return True
    logger.error(f"飞书推送失败: {result}")
    return False


def _send_wecom(webhook_url: str, text: str) -> bool:
    """发送企微机器人消息"""
    payload = {
        "msgtype": "text",
        "text": {"content": text},
    }
    result = _post_json(webhook_url, payload)
    if result.get("errcode") == 0:
        return True
    logger.error(f"企微推送失败: {result}")
    return False


def send_message(text: str) -> dict:
    """
    发送消息到所有已配置的机器人。
    返回 {"feishu": bool, "wecom": bool}
    """
    results = {"feishu": False, "wecom": False}

    if settings.FEISHU_WEBHOOK_URL:
        results["feishu"] = _send_feishu(
            settings.FEISHU_WEBHOOK_URL, text, settings.FEISHU_WEBHOOK_SECRET
        )

    if settings.WECOM_WEBHOOK_URL:
        results["wecom"] = _send_wecom(settings.WECOM_WEBHOOK_URL, text)

    if not settings.FEISHU_WEBHOOK_URL and not settings.WECOM_WEBHOOK_URL:
        logger.warning("未配置任何推送 Webhook，消息未发送")

    return results


def format_briefing_message(briefing) -> str:
    """将简报格式化为推送文本（v4行动分类+分类统计头）"""
    content = briefing.content_json or {}
    lines = []
    lines.append(f"📋 对公商机早报 {briefing.brief_date}")

    # v4分类统计头
    categories = content.get("categories", [])
    cat_stats = []
    for cat in categories:
        name = cat.get("category_name", cat.get("category_code", ""))
        count = cat.get("count", 0)
        if count > 0:
            cat_stats.append(f"{name}{count}")
    if cat_stats:
        lines.append(f"今日新增 {briefing.total_count} 条商机：{' · '.join(cat_stats)}")

    high_value = content.get("high_value_count", 0)
    if high_value:
        lines.append(f"⭐ 高价值商机 {high_value} 条")

    lines.append("")

    for cat in categories:
        icon = cat.get("icon", "📌")
        name = cat.get("category_name", cat.get("category_code", ""))
        count = cat.get("count", 0)
        if count == 0:
            continue
        lines.append(f"{icon} {name}（{count}条）")
        for item in cat.get("items", [])[:5]:
            title = item.get("title", "")
            score = item.get("quality_score", 0)
            source = item.get("source_channel", "")
            pub_date = item.get("publish_date", "")
            source_url = item.get("source_url", "")
            if source_url:
                title_display = f"[{title[:50]}]({source_url})"
            else:
                title_display = title[:50]
            source_part = f"[{source}] " if source else ""
            date_part = f"（{pub_date}）" if pub_date else ""
            lines.append(f"  [{score}分] {source_part}{title_display}{date_part}")
        lines.append("")

    lines.append("详情请登录系统查看")
    return "\n".join(lines)


def format_high_value_message(news) -> str:
    """格式化高价值商机即时推送（v4行动分类名）"""
    v4_categories = {
        "bid_action": "可投标项目",
        "fin_demand": "融资需求",
        "account_chance": "开户与结算机会",
        "park_project": "区域产业动态",
        "policy_ref": "监管与政策",
    }
    lines = []
    lines.append("🔥 高价值商机雷达")
    lines.append("")
    if news.source_url:
        lines.append(f"标题：[{news.title}]({news.source_url})")
    else:
        lines.append(f"标题：{news.title}")
    if news.business_category:
        cat_name = v4_categories.get(news.business_category, news.business_category)
        lines.append(f"行动分类：{cat_name}")
    if news.source_channel:
        lines.append(f"来源：{news.source_channel}")
    if news.publish_date:
        lines.append(f"发布日期：{news.publish_date}")
    if news.quality_score:
        lines.append(f"商机评分：{news.quality_score}")
    if news.business_tip:
        lines.append(f"业务启示：{news.business_tip[:200]}")
    lines.append("")
    lines.append("请登录系统查看详情并转线索跟进")
    return "\n".join(lines)


def push_daily_briefing(briefing) -> dict:
    """推送每日早报到飞书+企微"""
    text = format_briefing_message(briefing)
    return send_message(text)


def push_high_value_alert(news) -> dict:
    """推送高价值即时雷达"""
    text = format_high_value_message(news)
    return send_message(text)
