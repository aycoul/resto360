import { useCallback, useEffect, useState } from 'react';
import { api, getAccessToken } from '../api/client';

interface AnalyticsSummary {
  views_today: number;
  views_week: number;
  views_month: number;
  unique_today: number;
  menu_items: number;
}

/**
 * Hook to fetch analytics summary for the authenticated user's restaurant.
 * Returns views and menu item counts for dashboard display.
 */
export function useAnalyticsSummary() {
  const [data, setData] = useState<AnalyticsSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchSummary = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setIsLoading(false);
      return;
    }

    try {
      const result = await api.get<AnalyticsSummary>('/api/v1/analytics/summary/');
      setData(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch analytics'));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  return {
    data,
    isLoading,
    error,
    refetch: fetchSummary,
  };
}

interface TrackViewParams {
  restaurant_slug: string;
  session_id: string;
  source?: 'qr' | 'link' | 'whatsapp' | 'other';
  user_agent?: string;
}

/**
 * Track a menu view event.
 * Called from the public menu page on load.
 */
export async function trackMenuView(params: TrackViewParams): Promise<void> {
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

  try {
    await fetch(`${API_BASE}/api/v1/analytics/track/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        restaurant_slug: params.restaurant_slug,
        session_id: params.session_id,
        source: params.source || 'link',
        user_agent: params.user_agent || (typeof navigator !== 'undefined' ? navigator.userAgent : ''),
      }),
    });
  } catch (error) {
    // Silently fail - tracking should not block user experience
    console.error('Failed to track menu view:', error);
  }
}

/**
 * Get or create a session ID for tracking unique visitors.
 * Uses localStorage to persist across page refreshes.
 */
export function getOrCreateSessionId(): string {
  if (typeof window === 'undefined') {
    return '';
  }

  const STORAGE_KEY = 'resto360_session_id';
  let sessionId = localStorage.getItem(STORAGE_KEY);

  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem(STORAGE_KEY, sessionId);
  }

  return sessionId;
}

/**
 * Detect the source of menu access from URL parameters.
 */
export function detectSource(): 'qr' | 'link' | 'whatsapp' | 'other' {
  if (typeof window === 'undefined') {
    return 'link';
  }

  const params = new URLSearchParams(window.location.search);
  const source = params.get('source');

  if (source === 'qr') return 'qr';
  if (source === 'whatsapp') return 'whatsapp';

  // Detect referrer for additional context
  const referrer = document.referrer;
  if (referrer.includes('whatsapp.com') || referrer.includes('web.whatsapp.com')) {
    return 'whatsapp';
  }

  return 'link';
}
