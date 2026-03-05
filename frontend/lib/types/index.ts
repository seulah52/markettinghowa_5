export interface AnalysisReport {
  id: string;
  title: string;
  summary: string;
  sentiment: SentimentData;
  keywords: Keyword[];
  competitors: Competitor[];
  demographics: Demographics;
  createdAt: string;
}

export interface SentimentData {
  positive: number;
  neutral: number;
  negative: number;
}

export interface Keyword {
  word: string;
  count: number;
  trend: 'up' | 'down' | 'stable';
}

export interface Competitor {
  name: string;
  platform: Platform;
  score: number;
  followers: number;
}

export interface Demographics {
  ageGroups: AgeGroup[];
  regions: Region[];
  genderRatio: { male: number; female: number };
}

export interface AgeGroup  { range: string; percentage: number; }
export interface Region    { name: string; percentage: number; }
export type Platform = 'xiaohongshu' | 'taobao' | 'douyin' | 'baidu';

export interface BrandingStory {
  id: string;
  headline: string;
  body: string;
  tags: string[];
}

export interface WanghongProfile {
  id: string;
  name: string;
  platform: Platform;
  followers: number;
  engagementRate: number;
  categories: string[];
  contactInfo?: string;
}

export interface MarketingAsset {
  id: string;
  type: 'image' | 'copy' | 'video_script';
  content: string;
  platform: Platform;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

export interface JobStatus {
  job_id: string;
  status: 'pending' | 'running' | 'done' | 'error';
  progress?: number;
}
