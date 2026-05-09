/**
 * API Service Layer for RTI-Lens Frontend
 * Handles all backend API communication
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// Types
export interface QARequest {
  question: string;
  top_k?: number;
}

export interface QAResponse {
  answer: string;
  sources: Array<{
    order_number: string;
    ministry: string;
    order_date?: string;
    section?: string;
    score: number;
    text: string;
  }>;
  confidence: 'low' | 'medium' | 'high';
  calls_remaining?: number;
  faithful?: boolean;
  session_id?: string;
  thread_id?: string;
}

export interface PredictRequest {
  ministry: string;
  section_cited: string;
  appeal_level: 'first_appeal' | 'second_appeal';
  raw_text: string;
  order_date?: string;
}

export interface PredictResponse {
  prediction: 'allowed' | 'denied';
  probability: number;
  confidence: 'low' | 'medium' | 'high';
  disclaimer: string;
  low_data_warning: boolean;
  model_card?: any;
}

export interface DraftRequest {
  ministry: string;
  section_cited: string;
  context: string;
}

export interface DraftResponse {
  improved_query: string;
  change_notes: Array<{
    original: string;
    revised: string;
    reason: string;
  }>;
  avoid_phrases: string[];
  sources: Array<{
    order_number: string;
    outcome: string;
    section?: string;
    relevance: string;
  }>;
}

export interface DenialRate {
  ministry_id: number;
  ministry: string;
  total_orders: number;
  denied_count: number;
  allowed_count: number;
  denial_rate: number;
  override_rate: number;
}

export interface SectionHeatmap {
  section_cited: string;
  ministry: string;
  total_citations: number;
  overturned_count: number;
  misuse_rate: number;
}

export interface OverrideTrend {
  date: string;
  allowed_count: number;
  denied_count: number;
  override_rate: number;
}

// API Client
class APIClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const error = await response.json().catch(() => ({
          detail: `HTTP ${response.status}: ${response.statusText}`
        }));
        throw new Error(error.detail || 'API request failed');
      }

      return await response.json();
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      throw error;
    }
  }

  // Q&A Endpoints
  async askQuestion(request: QARequest): Promise<QAResponse> {
    return this.request<QAResponse>('/qa', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Prediction Endpoints
  async predictOutcome(request: PredictRequest): Promise<PredictResponse> {
    return this.request<PredictResponse>('/predict', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Draft Generation Endpoints
  async generateDraft(request: DraftRequest): Promise<DraftResponse> {
    return this.request<DraftResponse>('/draft', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Analytics Endpoints
  async getDenialRates(params?: {
    year_from?: number;
    year_to?: number;
    ministry_id?: number;
  }): Promise<DenialRate[]> {
    const queryParams = new URLSearchParams();
    if (params?.year_from) queryParams.append('year_from', params.year_from.toString());
    if (params?.year_to) queryParams.append('year_to', params.year_to.toString());
    if (params?.ministry_id) queryParams.append('ministry_id', params.ministry_id.toString());

    const query = queryParams.toString();
    return this.request<DenialRate[]>(`/analytics/denial-rates${query ? `?${query}` : ''}`);
  }

  async getSectionHeatmap(): Promise<SectionHeatmap[]> {
    return this.request<SectionHeatmap[]>('/analytics/section-heatmap');
  }

  async getOverrideTrends(): Promise<OverrideTrend[]> {
    return this.request<OverrideTrend[]>('/analytics/override-trends');
  }

  async getMinistryOrders(
    ministryId: number,
    offset: number = 0,
    limit: number = 100
  ): Promise<any[]> {
    return this.request<any[]>(
      `/analytics/ministry/${ministryId}/orders?offset=${offset}&limit=${limit}`
    );
  }

  // Dashboard Endpoints
  async getDashboardStats(): Promise<any> {
    return this.request<any>('/dashboard/stats');
  }

  async getDashboardGraph(): Promise<any> {
    return this.request<any>('/dashboard/graph');
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; [key: string]: any }> {
    return this.request<any>('/health', { method: 'GET' });
  }
}

// Export singleton instance
export const api = new APIClient();

// Export class for testing or custom instances
export default APIClient;
