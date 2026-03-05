-- Analysis Jobs
CREATE TABLE analysis_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  keyword TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  result JSONB,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Branding Stories
CREATE TABLE branding_stories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_name TEXT NOT NULL,
  story TEXT NOT NULL,
  tags TEXT[],
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Wanghong Profiles
CREATE TABLE wanghong_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  platform TEXT NOT NULL,
  followers INTEGER,
  engagement_rate NUMERIC,
  categories TEXT[],
  contact_info TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- RLS Policies
ALTER TABLE analysis_jobs     ENABLE ROW LEVEL SECURITY;
ALTER TABLE branding_stories  ENABLE ROW LEVEL SECURITY;
ALTER TABLE wanghong_profiles ENABLE ROW LEVEL SECURITY;
