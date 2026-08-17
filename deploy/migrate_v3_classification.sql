-- ============================================================
-- v3 分类层迁移：标签字典重构 + 行业标签数据迁移
-- 在 Supabase SQL Editor 执行（幂等，可重复执行）
-- ============================================================

-- 1. 行动分类标签（新一级分类）
INSERT INTO tag_dictionary (tag_type, tag_code, tag_name, tag_color, keywords, sort_order, is_active) VALUES
('action', 'bid_action',      '可投标项目',   '#1a56db', '["招标","投标","采购","中标","招标公告","磋商","询价"]', 1, true),
('action', 'fin_demand',      '融资需求',     '#f59e0b', '["融资","发债","增资","贷款","授信","IPO","定增","并购"]', 2, true),
('action', 'account_chance',  '开户结算机会', '#10b981', '["新设","注册","成立","变更","开户","落户","迁入"]', 3, true),
('action', 'park_project',    '区域产业动态', '#8b5cf6', '["园区","产业","招商","入驻","投资","项目"]', 4, true),
('action', 'policy_ref',      '监管与政策',   '#6b7280', '["政策","通知","公告","办法","规定","条例","意见"]', 5, true)
ON CONFLICT (tag_type, tag_code) DO NOTHING;

-- 2. 区域标签：标准 7 类
INSERT INTO tag_dictionary (tag_type, tag_code, tag_name, tag_color, sort_order, is_active) VALUES
('area', 'chaoyang',  '朝阳区',   '#06b6d4', 1, true),
('area', 'dongcheng', '东城区',   '#0ea5e9', 2, true),
('area', 'tongzhou',  '通州区',   '#14b8a6', 3, true),
('area', 'yizhuang',  '亦庄经开区', '#6366f1', 4, true),
('area', 'beijing',   '北京市级', '#3b82f6', 5, true),
('area', 'national',  '全国性',   '#8b5cf6', 6, true),
('area', 'other',     '其他地区', '#9ca3af', 7, true)
ON CONFLICT (tag_type, tag_code) DO NOTHING;

-- 停用旧区域标签（haidian/fengtai 等非标准区划标签，保留但不激活）
UPDATE tag_dictionary SET is_active = false
WHERE tag_type = 'area' AND tag_code NOT IN ('chaoyang','dongcheng','tongzhou','yizhuang','beijing','national','other');

-- 3. 行业标签：按北京主导产业重构
INSERT INTO tag_dictionary (tag_type, tag_code, tag_name, tag_color, sort_order, is_active) VALUES
('industry', 'finance',                '金融',       '#0ea5e9', 1, true),
('industry', 'tech',                   '科技',       '#6366f1', 2, true),
('industry', 'culture',                '文化',       '#a855f7', 3, true),
('industry', 'business_service',       '商务服务',   '#f59e0b', 4, true),
('industry', 'advanced_manufacturing', '先进制造',   '#ef4444', 5, true),
('industry', 'medical_health',         '医药健康',   '#10b981', 6, true),
('industry', 'digital_economy',        '数字经济',   '#06b6d4', 7, true),
('industry', 'other',                  '其他',       '#9ca3af', 8, true)
ON CONFLICT (tag_type, tag_code) DO NOTHING;

-- 停用旧行业标签（tech/finance 保留映射，其余停用）
UPDATE tag_dictionary SET is_active = false
WHERE tag_type = 'industry'
  AND tag_code NOT IN ('finance','tech','culture','business_service','advanced_manufacturing','medical_health','digital_economy','other');

-- 4. 商机类型标签（新增）
INSERT INTO tag_dictionary (tag_type, tag_code, tag_name, tag_color, sort_order, is_active) VALUES
('opportunity', 'bidding',   '招投标',   '#1a56db', 1, true),
('opportunity', 'financing', '融资',     '#f59e0b', 2, true),
('opportunity', 'merger',    '并购',     '#8b5cf6', 3, true),
('opportunity', 'account',   '开户',     '#10b981', 4, true),
('opportunity', 'subsidy',   '补贴申报', '#06b6d4', 5, true),
('opportunity', 'land',      '土地出让', '#ef4444', 6, true)
ON CONFLICT (tag_type, tag_code) DO NOTHING;

-- 5. 行业标签数据迁移（news_items.industry_tags 旧值 → 新北京产业体系）
-- 旧值 → 新值映射：
--   tech/digital/information/software → tech 或 digital_economy（含"数字"相关词 → digital_economy）
--   finance/banking/insurance/investment → finance
--   manufacturing/advanced_mfg → advanced_manufacturing
--   medical/health/pharma/biotech → medical_health
--   culture/media → culture
--   service/consulting → business_service
--   其余 → other

-- 5.1 纯 tech → tech；含数字/信息关键词的 tech 场景保留 tech（前端已有 digital_economy 维度，简单映射）
UPDATE news_items SET industry_tags = (
    SELECT jsonb_agg(
        CASE tag
            WHEN 'tech' THEN 'tech'
            WHEN 'digital' THEN 'digital_economy'
            WHEN 'information' THEN 'tech'
            WHEN 'software' THEN 'tech'
            WHEN 'internet' THEN 'digital_economy'
            WHEN 'ai' THEN 'tech'
            WHEN 'bigdata' THEN 'digital_economy'
            WHEN 'finance' THEN 'finance'
            WHEN 'banking' THEN 'finance'
            WHEN 'insurance' THEN 'finance'
            WHEN 'securities' THEN 'finance'
            WHEN 'investment' THEN 'finance'
            WHEN 'manufacturing' THEN 'advanced_manufacturing'
            WHEN 'advanced_manufacturing' THEN 'advanced_manufacturing'
            WHEN 'medical' THEN 'medical_health'
            WHEN 'health' THEN 'medical_health'
            WHEN 'healthcare' THEN 'medical_health'
            WHEN 'pharmaceutical' THEN 'medical_health'
            WHEN 'biotech' THEN 'medical_health'
            WHEN 'culture' THEN 'culture'
            WHEN 'media' THEN 'culture'
            WHEN 'cultural_creative' THEN 'culture'
            WHEN 'service' THEN 'business_service'
            WHEN 'consulting' THEN 'business_service'
            WHEN 'professional_service' THEN 'business_service'
            WHEN 'logistics' THEN 'business_service'
            WHEN 'retail' THEN 'business_service'
            WHEN 'trade' THEN 'business_service'
            WHEN 'real_estate' THEN 'other'
            WHEN 'government' THEN 'other'
            WHEN 'education' THEN 'other'
            WHEN 'energy' THEN 'other'
            WHEN 'green_energy' THEN 'other'
            WHEN 'new_energy' THEN 'other'
            WHEN 'agriculture' THEN 'other'
            WHEN 'aviation' THEN 'other'
            WHEN 'aerospace' THEN 'other'
            WHEN 'infrastructure' THEN 'other'
            WHEN 'transportation' THEN 'other'
            WHEN 'materials' THEN 'other'
            WHEN 'auction' THEN 'other'
            WHEN 'heating' THEN 'other'
            WHEN 'green_energy' THEN 'other'
            ELSE 'other'
        END
    ) FROM jsonb_array_elements_text(industry_tags) AS tag
)
WHERE industry_tags IS NOT NULL AND jsonb_array_length(industry_tags) > 0;

-- 5.2 去重 industry_tags（迁移可能产生重复）
UPDATE news_items SET industry_tags = (
    SELECT COALESCE(jsonb_agg(DISTINCT tag), '[]'::jsonb)
    FROM jsonb_array_elements_text(industry_tags) AS tag
)
WHERE industry_tags IS NOT NULL AND jsonb_array_length(industry_tags) > 1;

-- 6. 验证
SELECT tag_type, tag_code, tag_name, is_active FROM tag_dictionary ORDER BY tag_type, sort_order;
SELECT '---' AS sep;
SELECT industry_tags FROM news_items WHERE is_deleted = false LIMIT 5;
