/**
 * React hooks for API calls with loading and error states
 */
import { useState, useCallback } from 'react';
import { api } from '../services/api';
import type {
  QARequest,
  QAResponse,
  PredictRequest,
  PredictResponse,
  DraftRequest,
  DraftResponse,
  DenialRate,
  SectionHeatmap,
  OverrideTrend,
} from '../services/api';

interface UseAPIState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export function useQA() {
  const [state, setState] = useState<UseAPIState<QAResponse>>({
    data: null,
    loading: false,
    error: null,
  });

  const askQuestion = useCallback(async (request: QARequest) => {
    setState({ data: null, loading: true, error: null });
    try {
      const data = await api.askQuestion(request);
      setState({ data, loading: false, error: null });
      return data;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to get answer';
      setState({ data: null, loading: false, error: errorMessage });
      throw error;
    }
  }, []);

  return { ...state, askQuestion };
}

export function usePredict() {
  const [state, setState] = useState<UseAPIState<PredictResponse>>({
    data: null,
    loading: false,
    error: null,
  });

  const predict = useCallback(async (request: PredictRequest) => {
    setState({ data: null, loading: true, error: null });
    try {
      const data = await api.predictOutcome(request);
      setState({ data, loading: false, error: null });
      return data;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to predict outcome';
      setState({ data: null, loading: false, error: errorMessage });
      throw error;
    }
  }, []);

  return { ...state, predict };
}

export function useDraft() {
  const [state, setState] = useState<UseAPIState<DraftResponse>>({
    data: null,
    loading: false,
    error: null,
  });

  const generateDraft = useCallback(async (request: DraftRequest) => {
    setState({ data: null, loading: true, error: null });
    try {
      const data = await api.generateDraft(request);
      setState({ data, loading: false, error: null });
      return data;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to generate draft';
      setState({ data: null, loading: false, error: errorMessage });
      throw error;
    }
  }, []);

  return { ...state, generateDraft };
}

export function useAnalytics() {
  const [denialRates, setDenialRates] = useState<UseAPIState<DenialRate[]>>({
    data: null,
    loading: false,
    error: null,
  });

  const [sectionHeatmap, setSectionHeatmap] = useState<UseAPIState<SectionHeatmap[]>>({
    data: null,
    loading: false,
    error: null,
  });

  const [overrideTrends, setOverrideTrends] = useState<UseAPIState<OverrideTrend[]>>({
    data: null,
    loading: false,
    error: null,
  });

  const fetchDenialRates = useCallback(async (params?: {
    year_from?: number;
    year_to?: number;
    ministry_id?: number;
  }) => {
    setDenialRates({ data: null, loading: true, error: null });
    try {
      const data = await api.getDenialRates(params);
      setDenialRates({ data, loading: false, error: null });
      return data;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch denial rates';
      setDenialRates({ data: null, loading: false, error: errorMessage });
      throw error;
    }
  }, []);

  const fetchSectionHeatmap = useCallback(async () => {
    setSectionHeatmap({ data: null, loading: true, error: null });
    try {
      const data = await api.getSectionHeatmap();
      setSectionHeatmap({ data, loading: false, error: null });
      return data;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch section heatmap';
      setSectionHeatmap({ data: null, loading: false, error: errorMessage });
      throw error;
    }
  }, []);

  const fetchOverrideTrends = useCallback(async () => {
    setOverrideTrends({ data: null, loading: true, error: null });
    try {
      const data = await api.getOverrideTrends();
      setOverrideTrends({ data, loading: false, error: null });
      return data;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch override trends';
      setOverrideTrends({ data: null, loading: false, error: errorMessage });
      throw error;
    }
  }, []);

  return {
    denialRates,
    sectionHeatmap,
    overrideTrends,
    fetchDenialRates,
    fetchSectionHeatmap,
    fetchOverrideTrends,
  };
}
