import { useEffect, useMemo, useState } from 'react';
import WidgetCard from '../WidgetCard';

function toDateLabel(isoValue) {
  if (!isoValue) return '';
  try {
    const date = new Date(isoValue);
    return date.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });
  } catch {
    return '';
  }
}

function sessionLabel(session) {
  if (!session) return 'Session';
  const status = String(session.status || '').toLowerCase();
  if (status === 'live') return `${session.name} (live)`;
  if (status === 'completed') return `${session.name} (done)`;
  return `${session.name} (upcoming)`;
}

function SeasonDriversTable({ rows }) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="text-[10px] uppercase tracking-[0.12em] text-glance-muted/70">Driver standings</div>
      {rows.length === 0 && <div className="text-xs text-glance-muted">No standings available</div>}
      {rows.slice(0, 10).map((row) => (
        <div
          key={`${row.position}-${row.driver?.code || row.driver?.name}`}
          className="grid grid-cols-[20px_minmax(0,1fr)_42px] items-center gap-2 text-xs py-1 border-b border-glance-border/20 last:border-0"
        >
          <span className="text-glance-muted font-mono">{row.position}</span>
          <div className="min-w-0">
            <div className="text-glance-text truncate font-semibold">
              {row.driver?.code || row.driver?.name || 'Driver'}
            </div>
            <div className="text-[10px] text-glance-muted truncate">{row.team || '-'}</div>
          </div>
          <span className="text-glance-accent text-right font-mono">{row.points}</span>
        </div>
      ))}
    </div>
  );
}

function SeasonConstructorsTable({ rows }) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="text-[10px] uppercase tracking-[0.12em] text-glance-muted/70">Team standings</div>
      {rows.length === 0 && <div className="text-xs text-glance-muted">No standings available</div>}
      {rows.slice(0, 10).map((row) => (
        <div
          key={`${row.position}-${row.team?.name || row.position}`}
          className="grid grid-cols-[20px_minmax(0,1fr)_42px] items-center gap-2 text-xs py-1 border-b border-glance-border/20 last:border-0"
        >
          <span className="text-glance-muted font-mono">{row.position}</span>
          <div className="min-w-0">
            <div className="text-glance-text truncate font-semibold">{row.team?.name || 'Team'}</div>
            <div className="text-[10px] text-glance-muted truncate">{row.team?.nationality || '-'}</div>
          </div>
          <span className="text-glance-accent text-right font-mono">{row.points}</span>
        </div>
      ))}
    </div>
  );
}

function SessionTable({ session }) {
  if (!session) {
    return <div className="text-xs text-glance-muted">No session selected</div>;
  }

  const standings = session.standings || [];
  if (standings.length === 0) {
    return (
      <div className="text-xs text-glance-muted bg-glance-accent-dim/20 border border-glance-border/30 rounded-md px-2 py-2">
        {session.status === 'scheduled'
          ? `Starts ${toDateLabel(session.start) || 'soon'}`
          : 'Standings are not available yet'}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-1.5">
      <div className="text-[10px] uppercase tracking-[0.12em] text-glance-muted/70">{session.name} standings</div>
      {standings.slice(0, 10).map((row) => (
        <div
          key={`${session.session_key}-${row.position}-${row.driver?.code || row.driver_number}`}
          className="grid grid-cols-[20px_minmax(0,1fr)_64px] items-center gap-2 text-xs py-1 border-b border-glance-border/20 last:border-0"
        >
          <span className="text-glance-muted font-mono">{row.position}</span>
          <div className="min-w-0">
            <div className="text-glance-text truncate font-semibold">
              {row.driver?.code || row.driver?.name || row.driver_number}
            </div>
            <div className="text-[10px] text-glance-muted truncate">{row.team || '-'}</div>
          </div>
          <div className="text-right min-w-0">
            <div className="text-glance-accent font-mono text-[11px] truncate">{row.metric || '-'}</div>
            <div className="text-[10px] text-glance-muted truncate">{row.gap || ''}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function F1Widget({ data }) {
  const safeData = data || {};
  const isRaceWeek = !!safeData.is_race_week;
  const drivers = safeData.driver_standings || [];
  const constructors = safeData.constructor_standings || [];
  const sessions = safeData.race_weekend?.sessions || [];
  const latestSessionKey = safeData.race_weekend?.latest_completed_session_key;

  const sessionMap = useMemo(() => {
    const map = new Map();
    for (const session of sessions) {
      map.set(`session:${session.session_key}`, session);
    }
    return map;
  }, [sessions]);

  const viewOptions = useMemo(() => {
    if (!isRaceWeek) return [];
    return [
      { value: 'season:drivers', label: 'Season: Drivers' },
      { value: 'season:teams', label: 'Season: Teams' },
      ...sessions.map((session) => ({
        value: `session:${session.session_key}`,
        label: sessionLabel(session),
      })),
    ];
  }, [isRaceWeek, sessions]);

  const [selectedView, setSelectedView] = useState('season:drivers');

  useEffect(() => {
    if (!isRaceWeek) {
      setSelectedView('season:drivers');
      return;
    }

    const optionValues = new Set(viewOptions.map((option) => option.value));
    if (optionValues.has(selectedView)) {
      return;
    }

    const preferred = latestSessionKey ? `session:${latestSessionKey}` : 'season:drivers';
    setSelectedView(optionValues.has(preferred) ? preferred : 'season:drivers');
  }, [isRaceWeek, latestSessionKey, selectedView, viewOptions]);

  const selectedSession = isRaceWeek ? sessionMap.get(selectedView) : null;
  const raceLabel = safeData.race_weekend?.race?.name || 'No race this week';

  if (!data) {
    return (
      <WidgetCard title="F1" icon="f1">
        <div className="flex items-center justify-center h-full text-glance-muted text-sm">Waiting for data...</div>
      </WidgetCard>
    );
  }

  return (
    <WidgetCard title="F1" icon="f1">
      <div className="flex flex-col gap-2 pt-1">
        <div className="flex items-center justify-between gap-2 text-[10px] uppercase tracking-[0.12em] text-glance-muted/70">
          <span className="truncate">Season {safeData.season || '-'}, Round {safeData.standings_round || '-'}</span>
          <span className="text-glance-accent/80">{safeData.source || 'f1'}</span>
        </div>

        {isRaceWeek && (
          <div className="space-y-1.5">
            <div className="text-[11px] text-glance-text/90 truncate">{raceLabel}</div>
            <select
              value={selectedView}
              onChange={(event) => setSelectedView(event.target.value)}
              className="w-full bg-glance-bg/50 border border-glance-border/40 rounded-md px-2 py-1 text-xs text-glance-text focus:outline-none focus:ring-1 focus:ring-glance-accent"
            >
              {viewOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        )}

        {!isRaceWeek && (
          <div className="text-[10px] uppercase tracking-[0.1em] text-glance-warning/90">
            Not race week. Showing season standings.
          </div>
        )}

        {isRaceWeek && selectedView === 'season:drivers' && <SeasonDriversTable rows={drivers} />}
        {isRaceWeek && selectedView === 'season:teams' && <SeasonConstructorsTable rows={constructors} />}
        {isRaceWeek && selectedView.startsWith('session:') && <SessionTable session={selectedSession} />}

        {!isRaceWeek && (
          <div className="grid grid-cols-1 gap-3">
            <SeasonDriversTable rows={drivers.slice(0, 6)} />
            <SeasonConstructorsTable rows={constructors.slice(0, 6)} />
          </div>
        )}
      </div>
    </WidgetCard>
  );
}
