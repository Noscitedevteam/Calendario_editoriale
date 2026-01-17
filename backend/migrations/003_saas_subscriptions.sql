-- =============================================
-- NOSCITE SaaS - Subscription Management Schema
-- =============================================

-- Piani di abbonamento
CREATE TABLE IF NOT EXISTS subscription_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,  -- 'basic', 'standard', 'pro'
    display_name VARCHAR(100) NOT NULL,
    price_monthly DECIMAL(10,2) NOT NULL,
    price_yearly DECIMAL(10,2),
    
    -- Limiti Brand e Utenti
    max_brands INTEGER NOT NULL DEFAULT 1,
    max_users INTEGER NOT NULL DEFAULT 1,
    
    -- Limiti Generazione
    monthly_calendar_generations INTEGER NOT NULL DEFAULT 3,
    monthly_text_tokens INTEGER NOT NULL DEFAULT 50000,
    monthly_images INTEGER NOT NULL DEFAULT 20,
    
    -- Features
    has_export_excel BOOLEAN DEFAULT FALSE,
    has_activity_log BOOLEAN DEFAULT FALSE,
    has_advanced_roles BOOLEAN DEFAULT FALSE,
    has_api_access BOOLEAN DEFAULT FALSE,
    has_crm_integration BOOLEAN DEFAULT FALSE,
    has_auto_publishing BOOLEAN DEFAULT FALSE,
    has_analytics BOOLEAN DEFAULT FALSE,
    has_ab_testing BOOLEAN DEFAULT FALSE,
    
    -- Extra a consumo (per Pro)
    allows_overage BOOLEAN DEFAULT FALSE,
    overage_price_per_1k_tokens DECIMAL(10,4),
    overage_price_per_image DECIMAL(10,4),
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Organizzazioni/Aziende (tenant)
CREATE TABLE IF NOT EXISTS organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    vat_number VARCHAR(50),  -- P.IVA
    address TEXT,
    
    -- Subscription
    plan_id INTEGER REFERENCES subscription_plans(id),
    subscription_status VARCHAR(20) DEFAULT 'trial',  -- trial, active, past_due, cancelled
    trial_ends_at TIMESTAMP,
    subscription_starts_at TIMESTAMP,
    subscription_ends_at TIMESTAMP,
    
    -- Stripe/Payment
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Utenti con ruoli per organizzazione
CREATE TABLE IF NOT EXISTS organization_users (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL DEFAULT 'viewer',  -- owner, admin, editor, viewer
    invited_by INTEGER REFERENCES users(id),
    invited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accepted_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    UNIQUE(organization_id, user_id)
);

-- Tracking utilizzo mensile
CREATE TABLE IF NOT EXISTS usage_tracking (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,  -- Primo giorno del mese
    period_end DATE NOT NULL,    -- Ultimo giorno del mese
    
    -- Contatori
    calendar_generations_used INTEGER DEFAULT 0,
    text_tokens_used INTEGER DEFAULT 0,
    images_generated INTEGER DEFAULT 0,
    
    -- Overage (extra oltre il limite)
    overage_tokens INTEGER DEFAULT 0,
    overage_images INTEGER DEFAULT 0,
    overage_cost DECIMAL(10,2) DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(organization_id, period_start)
);

-- Activity Log (per Standard e Pro)
CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,  -- 'calendar.generated', 'post.created', 'image.generated', etc.
    entity_type VARCHAR(50),       -- 'calendar', 'post', 'brand', etc.
    entity_id INTEGER,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Associazione Brand a Organizzazione
ALTER TABLE brands ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES organizations(id);

-- Indici per performance
CREATE INDEX IF NOT EXISTS idx_org_users_org ON organization_users(organization_id);
CREATE INDEX IF NOT EXISTS idx_org_users_user ON organization_users(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_org_period ON usage_tracking(organization_id, period_start);
CREATE INDEX IF NOT EXISTS idx_activity_org ON activity_logs(organization_id);
CREATE INDEX IF NOT EXISTS idx_activity_created ON activity_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_brands_org ON brands(organization_id);

-- =============================================
-- Inserimento Piani Default
-- =============================================

INSERT INTO subscription_plans (
    name, display_name, price_monthly, price_yearly,
    max_brands, max_users,
    monthly_calendar_generations, monthly_text_tokens, monthly_images,
    has_export_excel, has_activity_log, has_advanced_roles,
    has_api_access, has_crm_integration, has_auto_publishing,
    has_analytics, has_ab_testing, allows_overage,
    overage_price_per_1k_tokens, overage_price_per_image
) VALUES 
(
    'basic', 'Basic', 29.00, 290.00,
    1, 1,
    3, 50000, 20,
    FALSE, FALSE, FALSE,
    FALSE, FALSE, FALSE,
    FALSE, FALSE, FALSE,
    NULL, NULL
),
(
    'standard', 'Standard', 79.00, 790.00,
    5, 5,
    15, 200000, 150,
    TRUE, TRUE, TRUE,
    FALSE, TRUE, TRUE,
    TRUE, FALSE, FALSE,
    NULL, NULL
),
(
    'pro', 'Pro', 199.00, 1990.00,
    -1, -1,  -- -1 = illimitato
    100, 1000000, 500,
    TRUE, TRUE, TRUE,
    TRUE, TRUE, TRUE,
    TRUE, TRUE, TRUE,
    0.002, 0.05
)
ON CONFLICT (name) DO UPDATE SET
    price_monthly = EXCLUDED.price_monthly,
    price_yearly = EXCLUDED.price_yearly,
    max_brands = EXCLUDED.max_brands,
    max_users = EXCLUDED.max_users,
    monthly_calendar_generations = EXCLUDED.monthly_calendar_generations,
    monthly_text_tokens = EXCLUDED.monthly_text_tokens,
    monthly_images = EXCLUDED.monthly_images,
    has_export_excel = EXCLUDED.has_export_excel,
    has_activity_log = EXCLUDED.has_activity_log,
    has_advanced_roles = EXCLUDED.has_advanced_roles,
    has_api_access = EXCLUDED.has_api_access,
    has_crm_integration = EXCLUDED.has_crm_integration,
    has_auto_publishing = EXCLUDED.has_auto_publishing,
    has_analytics = EXCLUDED.has_analytics,
    has_ab_testing = EXCLUDED.has_ab_testing,
    allows_overage = EXCLUDED.allows_overage,
    updated_at = CURRENT_TIMESTAMP;

