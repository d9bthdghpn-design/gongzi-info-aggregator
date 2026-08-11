-- ============================================================
-- 对公资讯聚合系统 - 数据库初始化脚本
-- PostgreSQL 15+
-- ============================================================

-- 启用UUID扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 1. 用户表 (users)
-- ============================================================
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username        VARCHAR(64) NOT NULL UNIQUE,
    email           VARCHAR(128),
    phone           VARCHAR(20),
    full_name       VARCHAR(64),
    avatar_url      VARCHAR(512),
    department      VARCHAR(128),
    position        VARCHAR(64),
    role            VARCHAR(32) NOT NULL DEFAULT 'viewer',  -- admin/editor/reviewer/viewer
    password_hash   VARCHAR(256) NOT NULL DEFAULT '',       -- 密码哈希（bcrypt）
    sso_provider    VARCHAR(32),                            -- wecom/feishu
    sso_openid      VARCHAR(128),
    is_active       BOOLEAN NOT NULL DEFAULT true,
    last_login_at   TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_sso ON users(sso_provider, sso_openid);

-- ============================================================
-- 2. 标签字典表 (tag_dictionary)
-- ============================================================
CREATE TABLE tag_dictionary (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tag_type        VARCHAR(32) NOT NULL,    -- business/area/industry/info_type
    tag_code        VARCHAR(64) NOT NULL,
    tag_name        VARCHAR(64) NOT NULL,
    tag_color       VARCHAR(16),             -- 标签颜色
    keywords        JSONB DEFAULT '[]',      -- 关键词列表，用于规则引擎
    sort_order      INTEGER NOT NULL DEFAULT 0,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_tag_unique ON tag_dictionary(tag_type, tag_code);
CREATE INDEX idx_tag_type ON tag_dictionary(tag_type, is_active);

-- ============================================================
-- 3. 采集渠道配置表 (crawl_sources)
-- ============================================================
CREATE TABLE crawl_sources (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                    VARCHAR(128) NOT NULL,
    source_type             VARCHAR(32) NOT NULL,   -- gov/park/enterprise/bidding/wechat/xhs
    crawl_type              VARCHAR(32) NOT NULL,   -- web/js/rss/wechat/xhs
    entry_url               VARCHAR(512) NOT NULL,
    area_scope              JSONB DEFAULT '[]',     -- 区域范围标签
    industry_scope          JSONB DEFAULT '[]',     -- 行业范围标签
    crawl_interval_hours    INTEGER NOT NULL DEFAULT 24,
    priority                INTEGER NOT NULL DEFAULT 5,  -- 1-10，越大优先级越高
    is_active               BOOLEAN NOT NULL DEFAULT true,
    selector_config         JSONB DEFAULT '{}',     -- 解析规则配置
    headers                 JSONB DEFAULT '{}',     -- 请求头配置
    proxy_group             VARCHAR(32),            -- 代理池分组
    last_crawl_at           TIMESTAMP WITH TIME ZONE,
    last_crawl_status       VARCHAR(16),            -- success/failed
    last_error_msg          TEXT,
    created_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_crawl_active ON crawl_sources(is_active, priority);
CREATE INDEX idx_crawl_type ON crawl_sources(crawl_type);

-- ============================================================
-- 4. 资讯主表 (news_items)
-- ============================================================
CREATE TABLE news_items (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title               VARCHAR(512) NOT NULL,
    content_raw         TEXT,                       -- 原始正文
    content_summary     VARCHAR(500),               -- AI生成摘要
    business_category   VARCHAR(64),                -- 业务分类标签code
    area_tags           JSONB DEFAULT '[]',         -- 区域标签数组
    industry_tags       JSONB DEFAULT '[]',         -- 行业标签数组
    info_type           VARCHAR(32),                -- 资讯类型: policy/bidding/enterprise/park
    source_type         VARCHAR(32),                -- 来源类型
    source_channel      VARCHAR(128),               -- 来源渠道名称
    source_url          VARCHAR(1024),              -- 原始URL(仅后台)
    publish_date        DATE,                       -- 发布日期
    business_tip        TEXT,                       -- AI生成的业务启示
    quality_score       INTEGER DEFAULT 0,          -- 商机价值评分 0-100
    dedup_hash          VARCHAR(64),                -- 内容去重哈希
    status              VARCHAR(32) NOT NULL DEFAULT 'pending_review',  -- pending_review/published/rejected/ai_failed
    reviewer_id         UUID REFERENCES users(id),
    reviewed_at         TIMESTAMP WITH TIME ZONE,
    review_comment      VARCHAR(512),
    view_count          INTEGER NOT NULL DEFAULT 0,
    lead_count          INTEGER NOT NULL DEFAULT 0,
    is_deleted          BOOLEAN NOT NULL DEFAULT false,
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 核心索引
CREATE INDEX idx_news_status_date ON news_items(status, publish_date DESC);
CREATE INDEX idx_news_business_date ON news_items(business_category, publish_date DESC) WHERE is_deleted = false;
CREATE INDEX idx_news_area ON news_items USING GIN(area_tags) WHERE is_deleted = false;
CREATE INDEX idx_news_industry ON news_items USING GIN(industry_tags) WHERE is_deleted = false;
CREATE INDEX idx_news_info_type ON news_items(info_type, publish_date DESC) WHERE is_deleted = false;
CREATE UNIQUE INDEX idx_news_dedup_hash ON news_items(dedup_hash) WHERE dedup_hash IS NOT NULL;
CREATE UNIQUE INDEX idx_news_source_url ON news_items(source_url) WHERE source_url IS NOT NULL;
CREATE INDEX idx_news_quality ON news_items(quality_score DESC) WHERE status = 'published' AND is_deleted = false;
CREATE INDEX idx_news_published ON news_items(publish_date DESC) WHERE status = 'published' AND is_deleted = false;

-- ============================================================
-- 5. 线索表 (leads)
-- ============================================================
CREATE TABLE leads (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name        VARCHAR(256) NOT NULL,
    credit_code         VARCHAR(32),                -- 统一社会信用代码
    industry            VARCHAR(64),                -- 所属行业
    area                VARCHAR(64),                -- 所在区域
    contact_person      VARCHAR(64),
    contact_title       VARCHAR(64),                -- 联系人职务
    contact_phone       VARCHAR(32),
    intent_business     JSONB DEFAULT '[]',         -- 意向业务
    project_desc        TEXT,                       -- 项目描述
    expected_date       DATE,                       -- 预计落地时间
    lead_source         VARCHAR(32) DEFAULT 'manual', -- 线索来源
    source_news_id      UUID REFERENCES news_items(id),
    priority            INTEGER DEFAULT 3,          -- 优先级 1-5
    status              VARCHAR(32) NOT NULL DEFAULT 'new',  -- new/active/converted/lost/released
    reporter_id         UUID REFERENCES users(id),
    assignee_id         UUID REFERENCES users(id),
    public_pool         BOOLEAN NOT NULL DEFAULT false,  -- 是否在公海池
    protect_expire_at   TIMESTAMP WITH TIME ZONE,   -- 保护期到期时间
    last_followup_time  TIMESTAMP WITH TIME ZONE,
    next_followup_time  TIMESTAMP WITH TIME ZONE,
    is_deleted          BOOLEAN NOT NULL DEFAULT false,
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_leads_status_created ON leads(status, created_at DESC) WHERE is_deleted = false;
CREATE INDEX idx_leads_assignee ON leads(assignee_id, status) WHERE is_deleted = false;
CREATE INDEX idx_leads_public_pool ON leads(public_pool, status) WHERE public_pool = true AND is_deleted = false;
CREATE INDEX idx_leads_company ON leads(company_name) WHERE is_deleted = false;
CREATE INDEX idx_leads_area ON leads(area) WHERE is_deleted = false;

-- ============================================================
-- 6. 线索跟进记录表 (lead_followups)
-- ============================================================
CREATE TABLE lead_followups (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id         UUID NOT NULL REFERENCES leads(id),
    followup_type   VARCHAR(32) NOT NULL,    -- phone/visit/email/meeting/other
    content         TEXT NOT NULL,
    next_action     VARCHAR(512),
    next_time       TIMESTAMP WITH TIME ZONE,
    follower_id     UUID NOT NULL REFERENCES users(id),
    followup_time   TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    attachments     JSONB DEFAULT '[]',      -- 附件列表
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_followups_lead ON lead_followups(lead_id, followup_time DESC);
CREATE INDEX idx_followups_follower ON lead_followups(follower_id, followup_time DESC);

-- ============================================================
-- 7. 每日简报表 (daily_briefings)
-- ============================================================
CREATE TABLE daily_briefings (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brief_date          DATE NOT NULL,
    area_scope          VARCHAR(64),
    content_json        JSONB NOT NULL DEFAULT '{}',
    total_count         INTEGER NOT NULL DEFAULT 0,
    category_counts     JSONB DEFAULT '{}',
    is_pushed           BOOLEAN NOT NULL DEFAULT false,
    pushed_at           TIMESTAMP WITH TIME ZONE,
    created_by          UUID REFERENCES users(id),
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_briefing_date ON daily_briefings(brief_date);
CREATE INDEX idx_briefing_pushed ON daily_briefings(is_pushed, brief_date DESC);

-- ============================================================
-- 8. 采集日志表 (crawl_logs)
-- ============================================================
CREATE TABLE crawl_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id       UUID NOT NULL REFERENCES crawl_sources(id),
    crawl_start     TIMESTAMP WITH TIME ZONE NOT NULL,
    crawl_end       TIMESTAMP WITH TIME ZONE,
    total_fetched   INTEGER NOT NULL DEFAULT 0,
    new_count       INTEGER NOT NULL DEFAULT 0,
    dup_count       INTEGER NOT NULL DEFAULT 0,
    error_count     INTEGER NOT NULL DEFAULT 0,
    error_msg       TEXT,
    status          VARCHAR(16) NOT NULL DEFAULT 'running',  -- running/success/failed
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_crawl_logs_source ON crawl_logs(source_id, crawl_start DESC);
CREATE INDEX idx_crawl_logs_status ON crawl_logs(status, crawl_start DESC);

-- ============================================================
-- 9. AI处理日志表 (ai_process_logs)
-- ============================================================
CREATE TABLE ai_process_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    news_id         UUID NOT NULL REFERENCES news_items(id),
    process_type    VARCHAR(32) NOT NULL,    -- classify/summarize/tip/score/all
    input_tokens    INTEGER NOT NULL DEFAULT 0,
    output_tokens   INTEGER NOT NULL DEFAULT 0,
    model_version   VARCHAR(64),
    raw_output      TEXT,
    is_modified     BOOLEAN NOT NULL DEFAULT false,
    modified_fields JSONB DEFAULT '[]',
    duration_ms     INTEGER NOT NULL DEFAULT 0,
    success         BOOLEAN NOT NULL DEFAULT true,
    error_msg       TEXT,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ai_logs_news ON ai_process_logs(news_id, created_at DESC);
CREATE INDEX idx_ai_logs_type ON ai_process_logs(process_type, created_at DESC);
CREATE INDEX idx_ai_logs_success ON ai_process_logs(success, created_at DESC);

-- ============================================================
-- 10. 操作日志表 (operation_logs)
-- ============================================================
CREATE TABLE operation_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(id),
    action          VARCHAR(64) NOT NULL,    -- create/update/delete/audit/assign
    target_type     VARCHAR(32) NOT NULL,    -- news/lead/user/source
    target_id       UUID NOT NULL,
    old_value       JSONB,
    new_value       JSONB,
    ip_address      VARCHAR(64),
    user_agent      VARCHAR(512),
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_op_logs_user ON operation_logs(user_id, created_at DESC);
CREATE INDEX idx_op_logs_target ON operation_logs(target_type, target_id);
CREATE INDEX idx_op_logs_action ON operation_logs(action, created_at DESC);

-- ============================================================
-- 11. 业务专题表 (topics)
-- ============================================================
CREATE TABLE topics (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title           VARCHAR(256) NOT NULL,
    description     TEXT,
    cover_image     VARCHAR(512),
    filter_config   JSONB NOT NULL DEFAULT '{}',   -- 筛选条件配置
    sort_order      INTEGER NOT NULL DEFAULT 0,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_topics_active ON topics(is_active, sort_order);

-- ============================================================
-- 初始化数据
-- ============================================================

-- 注意：管理员用户不在此处创建，请部署后运行 init_db.py 或通过 /api/v1/auth/register 接口创建
-- 默认账号: admin / admin123

-- 初始化业务分类标签
INSERT INTO tag_dictionary (tag_type, tag_code, tag_name, tag_color, sort_order, keywords) VALUES
('business', 'deposit', '存款业务', '#3b82f6', 1, '["存款","开户","结算","资金"]'),
('business', 'loan', '贷款业务', '#ef4444', 2, '["贷款","融资","授信","抵押","担保"]'),
('business', 'investment_bank', '投行业务', '#8b5cf6', 3, '["发债","上市","并购","重组","ABS"]'),
('business', 'treasury', '财资管理', '#f59e0b', 4, '["现金管理","财资","流动性","资金池"]'),
('business', 'supply_chain', '供应链金融', '#10b981', 5, '["供应链","应收账款","保理","票据"]')
ON CONFLICT DO NOTHING;

-- 初始化区域标签
INSERT INTO tag_dictionary (tag_type, tag_code, tag_name, tag_color, sort_order) VALUES
('area', 'chaoyang', '朝阳区', '#06b6d4', 1),
('area', 'haidian', '海淀区', '#0ea5e9', 2),
('area', 'fengtai', '丰台区', '#14b8a6', 3)
ON CONFLICT DO NOTHING;

-- 初始化行业标签
INSERT INTO tag_dictionary (tag_type, tag_code, tag_name, tag_color, sort_order) VALUES
('industry', 'tech', '信息技术', '#6366f1', 1),
('industry', 'finance', '金融服务', '#0ea5e9', 2),
('industry', 'manufacturing', '制造业', '#f59e0b', 3),
('industry', 'real_estate', '房地产', '#ef4444', 4),
('industry', 'medical', '医药健康', '#10b981', 5),
('industry', 'education', '教育培训', '#8b5cf6', 6),
('industry', 'retail', '零售消费', '#ec4899', 7),
('industry', 'logistics', '物流运输', '#f97316', 8),
('industry', 'energy', '能源环保', '#84cc16', 9),
('industry', 'culture', '文化传媒', '#a855f7', 10),
('industry', 'government', '政府机构', '#64748b', 11)
ON CONFLICT DO NOTHING;

-- 初始化资讯类型标签
INSERT INTO tag_dictionary (tag_type, tag_code, tag_name, tag_color, sort_order) VALUES
('info_type', 'policy', '政策动态', '#3b82f6', 1),
('info_type', 'bidding', '招投标', '#ef4444', 2),
('info_type', 'enterprise', '企业动态', '#10b981', 3),
('info_type', 'park', '园区动态', '#f59e0b', 4)
ON CONFLICT DO NOTHING;

-- 初始化示例采集渠道
INSERT INTO crawl_sources (name, source_type, crawl_type, entry_url, area_scope, priority, selector_config) VALUES
('朝阳区政府官网', 'gov', 'web', 'https://www.bjchy.gov.cn/', '["chaoyang"]', 8,
 '{"list_selector": ".news-list li", "title_selector": "a", "link_selector": "a@href", "date_selector": ".date", "content_selector": ".article-content"}'),
('海淀区政府官网', 'gov', 'web', 'https://www.bjhd.gov.cn/', '["haidian"]', 8,
 '{"list_selector": ".news-list li", "title_selector": "a", "link_selector": "a@href", "date_selector": ".date", "content_selector": ".article-content"}'),
('中国政府采购网', 'bidding', 'web', 'http://www.ccgp.gov.cn/', '[]', 9,
 '{"list_selector": ".vT-srch-result-list li", "title_selector": "a", "link_selector": "a@href", "date_selector": ".date", "content_selector": ".vF_detail_main"}')
ON CONFLICT DO NOTHING;

-- 初始化示例资讯数据（用于演示）
INSERT INTO news_items (title, content_raw, content_summary, business_category, area_tags, industry_tags, info_type, source_type, source_channel, publish_date, business_tip, quality_score, status) VALUES
('朝阳区发布2026年重点项目清单，总投资超5000亿',
 '朝阳区政府今日发布2026年重点建设项目清单，涵盖基础设施、产业升级、民生改善等多个领域，总投资额超过5000亿元。其中，CBD东扩项目、数字经济产业园、国际金融城等重大项目备受关注。',
 '朝阳区发布2026年重点项目清单，总投资超5000亿，涵盖基础设施、产业升级、民生改善等领域，CBD东扩、数字经济产业园等重大项目在列。',
 'loan', '["chaoyang"]', '["real_estate","tech"]', 'policy',
 '政府官网', '朝阳区政府', '2026-08-06',
 '💡 可重点对接CBD东扩项目涉及的园区开发企业，提供项目贷款、供应链金融等综合金融服务；数字经济产业园可批量拓展科技型中小企业开户及授信。',
 85, 'published'),
('某科技公司完成D轮融资10亿元，估值超百亿',
 '国内知名人工智能企业XX科技今日宣布完成D轮融资10亿元，由多家知名投资机构领投。融资后公司估值超过100亿元，将用于研发投入和市场扩张。公司总部位于海淀区中关村，员工规模超过1000人。',
 'XX科技完成10亿元D轮融资，估值超百亿，资金将用于研发和扩张，公司位于海淀中关村，员工超千人。',
 'deposit', '["haidian"]', '["tech"]', 'enterprise',
 '企业动态', '36氪', '2026-08-06',
 '💡 该公司估值百亿且有大额融资到账，是优质存款客户目标，可上门拜访提供定制化现金管理方案；同时可关注其上下游供应链企业，拓展批量获客机会。',
 92, 'published'),
('丰台区数字经济产业园招标公告',
 '丰台区数字经济产业园配套设施建设项目公开招标，预算金额2.5亿元。招标内容包括园区智能化系统建设、数据中心基础设施、网络安全设备等。投标截止时间为2026年9月15日。',
 '丰台区数字经济产业园配套设施招标，预算2.5亿，含智能化系统、数据中心、网络安全等，9月15日截标。',
 'supply_chain', '["fengtai"]', '["tech"]', 'bidding',
 '招投标平台', '中国政府采购网', '2026-08-05',
 '💡 可关注中标企业，提供履约保函、应收账款保理等供应链金融服务；园区运营方可对接园区贷、租金收入质押贷款等产品。',
 78, 'published'),
('央行发布最新货币政策执行报告，强调支持实体经济',
 '中国人民银行发布2026年第二季度货币政策执行报告，强调继续实施稳健的货币政策，加大对实体经济的支持力度，重点支持小微企业、科技创新、绿色发展等领域。',
 '央行发布二季度货币政策报告，稳健货币政策不变，加大支持实体经济，重点支持小微、科创、绿色发展。',
 'loan', '["chaoyang","haidian","fengtai"]', '["finance"]', 'policy',
 '政府官网', '人民银行', '2026-08-05',
 '💡 货币政策偏宽松，可加大对公贷款投放力度，特别是小微企业和科创企业；绿色金融产品可作为差异化竞争亮点重点推广。',
 70, 'published'),
('中关村软件园新增20家专精特新企业入驻',
 '中关村软件园今日宣布，又有20家专精特新企业正式入驻园区，涵盖人工智能、集成电路、生物医药等前沿领域。园区已累计入驻企业超过800家，年产值超千亿元。',
 '中关村软件园新增20家专精特新企业，覆盖AI、集成电路、生物医药等领域，累计入驻超800家，年产值超千亿。',
 'deposit', '["haidian"]', '["tech","medical"]', 'park',
 '园区公众号', '中关村软件园', '2026-08-04',
 '💡 20家新入驻企业是批量获客好机会，可联合园区运营方开展专场推介；专精特新企业有专属信贷产品，可精准营销。',
 82, 'published')
ON CONFLICT DO NOTHING;

-- 初始化示例专题
INSERT INTO topics (title, description, filter_config, sort_order, is_active) VALUES
('数字经济专题', '聚焦数字经济领域政策、企业动态、园区建设等资讯',
 '{"industry_tags":["tech"],"info_types":["policy","enterprise","park"]}', 1, true),
('基建投资专题', '关注重大基建项目招标、投资动态、政策支持等',
 '{"info_types":["bidding","policy"],"business_category":"loan"}', 2, true),
('专精特新专题', '专精特新企业融资、上市、政策扶持等动态',
 '{"industry_tags":["tech","manufacturing","medical"]}', 3, true)
ON CONFLICT DO NOTHING;

-- ============================================================
-- 更新时间触发器
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为有updated_at的表添加触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_tag_dict_updated_at BEFORE UPDATE ON tag_dictionary
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_crawl_sources_updated_at BEFORE UPDATE ON crawl_sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_news_updated_at BEFORE UPDATE ON news_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_briefings_updated_at BEFORE UPDATE ON daily_briefings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_topics_updated_at BEFORE UPDATE ON topics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 线索保护期到期自动回收函数
-- ============================================================
CREATE OR REPLACE FUNCTION expire_lead_protection()
RETURNS VOID AS $$
BEGIN
    UPDATE leads
    SET public_pool = true,
        assignee_id = NULL,
        status = 'released',
        updated_at = NOW()
    WHERE public_pool = false
      AND protect_expire_at IS NOT NULL
      AND protect_expire_at < NOW()
      AND status = 'active';
END;
$$ LANGUAGE plpgsql;

-- 完成
-- 注意：不同云数据库（如Supabase）的数据库名可能不是 gongzi_info，此处使用动态获取
DO $$ BEGIN
    EXECUTE 'COMMENT ON DATABASE ' || current_database() || ' IS ''对公资讯聚合系统数据库''';
EXCEPTION WHEN OTHERS THEN NULL;
END $$;
