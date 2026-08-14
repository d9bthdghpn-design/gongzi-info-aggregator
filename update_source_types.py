"""更新crawl_sources表source_type和采集间隔"""
import os
import sys

os.environ.setdefault("DATABASE_URL", "postgresql://postgres.sljoxgawgfdhchyibvdx:Ljz8248282%40@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres")
os.environ.setdefault("ENVIRONMENT", "production")
os.environ.setdefault("JWT_SECRET_KEY", "gOINcX8fj49sh2rUyna6W1JuBeqtFzTVMERQvKoYZPAbC7lH")
os.environ.setdefault("CORS_ORIGINS", "https://gongzi-info-aggregator.onrender.com")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

result = db.execute(text("SELECT source_type, COUNT(*) FROM crawl_sources GROUP BY source_type")).fetchall()
print("当前source_type分布:", result)

db.execute(text("UPDATE crawl_sources SET source_type='bidding_trade', crawl_interval_hours=2 WHERE name LIKE '%招标%' OR name LIKE '%投标%' OR name LIKE '%公共资源%' OR name LIKE '%产权%'"))
db.execute(text("UPDATE crawl_sources SET source_type='corp_finance', crawl_interval_hours=6 WHERE name LIKE '%金融%' OR name LIKE '%货币%' OR name LIKE '%巨潮%' OR name LIKE '%北交所%'"))
db.execute(text("UPDATE crawl_sources SET source_type='park_project', crawl_interval_hours=6 WHERE name LIKE '%园区%' OR name LIKE '%亦庄%' OR name LIKE '%CBD%' OR name LIKE '%朝阳园%' OR name LIKE '%投资北京%'"))
db.execute(text("UPDATE crawl_sources SET source_type='policy', crawl_interval_hours=6 WHERE (source_type NOT IN ('bidding_trade','corp_finance','park_project')) OR source_type IS NULL"))
db.commit()

result2 = db.execute(text("SELECT source_type, COUNT(*) FROM crawl_sources GROUP BY source_type")).fetchall()
print("更新后source_type分布:", result2)
db.close()
print("crawl_sources表更新完成")
