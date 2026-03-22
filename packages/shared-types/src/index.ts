// GENERATED FILE — do not edit manually. Run: make types

export interface ContentSlot {
  date: string;
  platform: string;
  content_type: string;
  topic: string;
  goal: string;
}

export interface CalendarInput {
  niche: string;
  platforms: string[];
  posting_frequency: number;
  historical_posts?: string[];
}

export interface CalendarOutput {
  content_plan: ContentSlot[];
}

export interface RepurposedItem {
  platform: string;
  content: string;
  format: string;
}

export interface RepurposeInput {
  original_content: string;
  source_platform: string;
  target_platforms: string[];
}

export interface RepurposeOutput {
  repurposed: RepurposedItem[];
}

export interface CoachInput {
  content: string;
  platform: string;
  goal?: string;
}

export interface CoachOutput {
  score: number;
  suggestions: string[];
  summary: string;
}

export interface TrendItem {
  topic: string;
  score: number;
  platforms: string[];
  summary: string;
}

export interface RadarInput {
  niche: string;
  platforms: string[];
  limit?: number;
}

export interface RadarOutput {
  trends: TrendItem[];
  scanned_at: string;
}

export interface User {
  id: string;
  email: string;
  name: string;
  is_active: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}
