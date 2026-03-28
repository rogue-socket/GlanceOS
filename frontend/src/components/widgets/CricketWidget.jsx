import { useEffect, useMemo, useState } from 'react';
import WidgetCard from '../WidgetCard';

const STATUS_COLORS = {
  'In Progress': 'text-glance-success',
  'Live': 'text-glance-success',
  'Complete': 'text-glance-muted',
  'Stumps': 'text-glance-warning',
};

function statusColor(status) {
  if (!status) return 'text-glance-muted';
  const lower = status.toLowerCase();
  if (lower.includes('live') || lower.includes('progress') || lower.includes('batting'))
    return 'text-glance-success';
  if (lower.includes('won') || lower.includes('complete') || lower.includes('result'))
    return 'text-glance-accent';
  if (lower.includes('start') || lower.includes('upcoming'))
    return 'text-glance-warning';
  return 'text-glance-muted';
}

function resolveCricketApiBaseUrl() {
  const envUrl = import.meta.env.VITE_BACKEND_URL;
  if (envUrl) {
    try {
      const parsed = new URL(envUrl);
      let path = parsed.pathname.replace(/\/+$/, '');
      if (path.endsWith('/api')) {
        return `${parsed.origin}${path}`;
      }
      return `${parsed.origin}${path}/api`;
    } catch {
      // Fall through to same-origin fallback.
    }
  }

  if (typeof window !== 'undefined' && window.location?.origin) {
    return `${window.location.origin}/api`;
  }

  return '/api';
}

function extractWidgetPayload(payload) {
  if (payload?.type === 'cricket' && payload?.data) {
    return payload.data;
  }
  if (payload && typeof payload === 'object') {
    return payload;
  }
  return null;
}

function formatRefreshTime(isoValue) {
  if (!isoValue) return '--';
  try {
    return new Date(isoValue).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });
  } catch {
    return '--';
  }
}

export default function CricketWidget({ data }) {
  const [apiData, setApiData] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState('');

  async function refreshNow() {
    setIsRefreshing(true);
    setRefreshError('');
    try {
      const base = resolveCricketApiBaseUrl();
      const resp = await fetch(`${base}/cricket/refresh`, { method: 'POST' });
      if (!resp.ok) {
        setRefreshError('Refresh failed');
        return;
      }

      const payload = await resp.json();
      const next = extractWidgetPayload(payload);
      if (next) {
        setApiData(next);
      }
    } catch {
      setRefreshError('Refresh failed');
    } finally {
      setIsRefreshing(false);
    }
  }

  useEffect(() => {
    if (data) {
      setApiData(null);
      return;
    }

    let cancelled = false;

    async function loadFromApi() {
      try {
        const base = resolveCricketApiBaseUrl();
        const resp = await fetch(`${base}/cricket`, { method: 'GET' });
        if (!resp.ok) return;
        const payload = await resp.json();
        if (cancelled) return;
        const next = extractWidgetPayload(payload);
        if (next) {
          setApiData(next);
        }
      } catch {
        // Ignore network errors; websocket can still recover.
      }
    }

    loadFromApi();
    const timer = setInterval(loadFromApi, 120000);

    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [data]);

  const effectiveData = useMemo(() => apiData || data, [apiData, data]);

  if (!effectiveData) {
    return (
      <WidgetCard title="Cricket" icon="cricket">
        <div className="flex flex-col gap-2.5 pt-1">
          <div className="flex items-center justify-between gap-2">
            <div className="text-[10px] uppercase tracking-[0.12em] text-glance-muted/70">
              No cached match data
            </div>
            <button
              type="button"
              onClick={refreshNow}
              disabled={isRefreshing}
              className="text-[10px] px-2 py-1 rounded-md border border-glance-border/50 text-glance-accent hover:bg-glance-accent-dim disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isRefreshing ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
          <div className="text-sm text-glance-muted text-center py-2">
            Waiting for scheduled fetch or manual refresh
          </div>
          {refreshError && (
            <div className="text-[10px] text-glance-danger text-center">{refreshError}</div>
          )}
        </div>
      </WidgetCard>
    );
  }

  const matches = effectiveData.matches || [];
  const schedule = effectiveData.schedule || null;
  const autoAt = formatRefreshTime(effectiveData.last_auto_refresh_at);
  const manualAt = formatRefreshTime(effectiveData.last_manual_refresh_at);

  return (
    <WidgetCard title="Cricket" icon="cricket">
      <div className="flex flex-col gap-2.5 pt-1">
        <div className="flex items-center justify-between gap-2">
          <div className="text-[10px] uppercase tracking-[0.12em] text-glance-muted/70">
            source: {effectiveData.source || 'cricket'}
          </div>
          <button
            type="button"
            onClick={refreshNow}
            disabled={isRefreshing}
            className="text-[10px] px-2 py-1 rounded-md border border-glance-border/50 text-glance-accent hover:bg-glance-accent-dim disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {isRefreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-[10px] px-2 py-0.5 rounded-full border border-glance-border/40 text-glance-muted">
            Auto: {autoAt}
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded-full border border-glance-border/40 text-glance-muted">
            Manual: {manualAt}
          </span>
        </div>
        {schedule && (
          <div className="text-[10px] text-glance-muted/70">
            Auto: {schedule.window_start} - {schedule.window_end}, final {schedule.final_call}
          </div>
        )}
        {refreshError && (
          <div className="text-[10px] text-glance-danger">{refreshError}</div>
        )}
        {matches.length === 0 && (
          <div className="text-sm text-glance-muted text-center py-2">
            No live matches
          </div>
        )}
        {matches.map((m, i) => (
          <div
            key={m.id || i}
            className="bg-glance-bg/40 rounded-lg px-3 py-2 border border-glance-border/30 hover:border-glance-accent/20 transition-colors"
          >
            {/* Match title */}
            <div className="text-[10px] text-glance-muted truncate mb-1.5">
              {m.title}
            </div>
            {/* Scores */}
            <div className="flex items-center justify-between gap-2">
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-glance-text">
                    {m.team1?.name}
                  </span>
                  <span className="text-xs font-mono text-glance-accent">
                    {m.team1?.score || '—'}
                  </span>
                </div>
                <div className="flex items-center justify-between mt-0.5">
                  <span className="text-xs font-bold text-glance-text">
                    {m.team2?.name}
                  </span>
                  <span className="text-xs font-mono text-glance-accent">
                    {m.team2?.score || '—'}
                  </span>
                </div>
              </div>
            </div>
            {/* Status */}
            <div className={`text-[10px] mt-1 font-medium truncate ${statusColor(m.status)}`}>
              ● {m.status}
            </div>
          </div>
        ))}
        {effectiveData.source === 'sample' && (
          <div className="text-[9px] text-glance-muted/50 text-center">
            sample data — configure API for live scores
          </div>
        )}
      </div>
    </WidgetCard>
  );
}
