export type ActionType = "watch" | "read" | "test" | "PoC" | "roadmap";
export type Urgency = "critical" | "high" | "medium" | "low";
export type Momentum = "new" | "rising" | "mature";
export type VietnamRelevance = "high" | "medium" | "low";
export type IntelligenceTier = "Tactical" | "Operational" | "Strategic" | "Informational";
export type AdoptionRing = "Adopt" | "Trial" | "Assess" | "Hold";

export interface PracticalIndicators {
  has_code_example?: boolean;
  has_benchmark?: boolean;
  has_api_change?: boolean;
  has_migration_guide?: boolean;
  has_security_patch?: boolean;
}

export interface RecommendationItem {
  action_type: ActionType;
  note: string;
}

export interface InsightListItem {
  id: string;
  title: string;
  summary_short: string | null;
  summary_medium: string | null;
  topics: string[];
  event_type: string | null;
  nature: string | null;
  trust_score: number;
  impact_label: string | null;
  source_url: string;
  confidence: number;
  affected_roles: string[];
  published_at: string | null;
  created_at: string;
  source_id: string;
  source_name: string;
  source_type: string;
  // v2 actionable fields
  signal: string | null;
  why_it_matters: string | null;
  recommendations: Record<string, RecommendationItem> | null;
  risks: string[] | null;
  momentum: Momentum | null;
  urgency: Urgency | null;
  vietnam_relevance: VietnamRelevance | null;
  // v3 taxonomy overhaul
  actionability_score: number | null;
  intelligence_tier: IntelligenceTier | null;
  so_what: string | null;
  adoption_ring: AdoptionRing | null;
  practical_indicators: PracticalIndicators | null;
  primary_image: string | null;
}

export interface InsightReference {
  id: string;
  title: string;
  source_name: string;
  source_url: string;
}

export interface InsightDetail extends InsightListItem {
  summary_medium: string | null;
  status: string;
  updated_at: string;
  source_feed_url: string | null;
  cluster_id: string | null;
  is_primary: boolean;
  references: InsightReference[];
  content_text?: string | null;
}


export interface PaginatedResponse<T> {
  page: number;
  size: number;
  total: number;
  items: T[];
}
