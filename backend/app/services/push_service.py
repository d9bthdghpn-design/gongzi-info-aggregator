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
    """将简报格式化为推送文本（每条资讯标注来源和发布日期）"""
    content = briefing.content_json or {}
    lines = []
    lines.append(f"📋 对公资讯早报 {briefing.brief_date}")
    lines.append(f"今日共 {briefing.total_count} 条资讯")

    high_value = content.get("high_value_count", 0)
    if high_value:
        lines.append(f"⭐ 高价值商机 {high_value} 条")

    lines.append("")

    categories = content.get("categories", [])
    for cat in categories:
        icon = cat.get("icon", "📌")
        name = cat.get("category_name", cat.get("category_code", ""))
        count = cat.get("count", 0)
        lines.append(f"{icon} {name}（{count}条）")
        for item in cat.get("items", [])[:5]:
            title = item.get("title", "")
            score = item.get("quality_score", 0)
            source = item.get("source_channel", "")
            pub_date = item.get("publish_date", "")
            source_url = item.get("source_url", "")
            # 标题加原文超链接（Markdown格式）
            if source_url:
                title_display = f"[{title[:50]}]({source_url})"
            else:
                title_display = title[:50]
            # 格式: [评分] [来源] 标题（发布日期）
            source_part = f"[{source}] " if source else ""
            date_part = f"（{pub_date}）" if pub_date else ""
            lines.append(f"  [{score}分] {source_part}{title_display}{date_part}")
        lines.append("")

    lines.append("详情请登录系统查看")
    return "\n".join(lines)


def format_high_value_message(news) -> str:
    """格式化高价值商机即时推送（标注来源和发布日期，标题加原文链接）"""
    lines = []
    lines.append("🔥 高价值商机提醒")
    lines.append("")
    if news.source_url:
        lines.append(f"标题：[{news.title}]({news.source_url})")
    else:
        lines.append(f"标题：{news.title}")
    if news.business_category:
        lines.append(f"分类：{news.business_category}")
    if news.source_channel:
        lines.append(f"来源：{news.source_channel}")
    if news.publish_date:
        lines.append(f"发布日期：{news.publish_date}")
    if news.quality_score:
        lines.append(f"评分：{news.quality_score}")
    if news.business_tip:
        lines.append(f"业务启示：{news.business_tip[:200]}")
    lines.append("")
    lines.append("请登录系统查看详情并跟进")
    return "\n".join(lines)
