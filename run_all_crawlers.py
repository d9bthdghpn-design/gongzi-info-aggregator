"""
统一数据采集入口（每日一键运行）
串行执行所有采集脚本，每个脚本用子进程隔离：
- 单脚本崩溃不影响其他源
- 输出每个源的结果汇总

用法: python run_all_crawlers.py
"""
import subprocess
import sys
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PYTHON = sys.executable
BASE = os.path.dirname(os.path.abspath(__file__))

# 采集脚本清单（顺序执行）
CRAWLERS = [
    # P0: 北京本地招投标（bid_action）
    ("crawl_beijing_bidding.py",       "北京市政府采购网(招投标)"),
    # P1: 融资类（fin_demand）
    ("crawl_v3_sources.py",            "巨潮/北交所/货币网/投资北京"),
    # 区域政策（policy_ref / park_project）
    ("crawl_east_beijing.py",          "东部区域政策(金融局/科委/朝阳/东城/通州/CBD)"),
    ("crawl_east_beijing_v2.py",       "亦庄/国资委/中关村朝阳园"),
    ("crawl_fgw_jxj.py",               "发改委/经信局"),
    ("crawl_liangqu.py",               "两区公共信息服务平台"),
]


def run_crawler(script: str, label: str, timeout: int = 600) -> dict:
    """运行单个采集脚本（子进程隔离）"""
    path = os.path.join(BASE, script)
    if not os.path.exists(path):
        return {"label": label, "script": script, "status": "SKIP", "detail": "脚本不存在"}

    logger.info(f"▶ 开始采集: {label} ({script})")
    try:
        result = subprocess.run(
            [PYTHON, path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=BASE,
            encoding="utf-8",
            errors="replace",
        )
        output = (result.stdout or "") + (result.stderr or "")
        # 提取最后几行有效输出
        lines = [l for l in output.strip().split("\n") if l.strip()][-6:]
        summary = " | ".join(l.strip()[:80] for l in lines)
        if result.returncode == 0:
            return {"label": label, "script": script, "status": "OK", "detail": summary}
        else:
            return {"label": label, "script": script, "status": "PARTIAL", "detail": summary}
    except subprocess.TimeoutExpired:
        return {"label": label, "script": script, "status": "TIMEOUT", "detail": f"超过{timeout}秒"}
    except Exception as e:
        return {"label": label, "script": script, "status": "ERROR", "detail": str(e)[:80]}


def main():
    print("=" * 60)
    print(f"对公资讯聚合系统 - 数据采集 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print("=" * 60)

    results = []
    for script, label in CRAWLERS:
        res = run_crawler(script, label)
        results.append(res)

    # 汇总
    print("\n" + "=" * 60)
    print("采集结果汇总")
    print("=" * 60)
    ok = 0
    for r in results:
        status_icon = {"OK": "✅", "PARTIAL": "⚠️", "TIMEOUT": "⏰", "ERROR": "❌", "SKIP": "⏭️"}.get(r["status"], "❓")
        print(f"  {status_icon} {r['label']}: {r['status']}")
        if r["detail"]:
            print(f"       {r['detail']}")
        if r["status"] in ("OK", "PARTIAL"):
            ok += 1
    print(f"\n完成: {ok}/{len(results)} 个源正常或部分采集")
    print("提示: 采集数据默认进入 pending_review，如需直接发布可运行 batch_publish_and_filter.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
