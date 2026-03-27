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

export default function CricketWidget({ data }) {
  if (!data) {
    return (
      <WidgetCard title="Cricket" icon="🏏">
        <div className="flex items-center justify-center h-full text-glance-muted text-sm">
          Waiting for data…
        </div>
      </WidgetCard>
    );
  }

  const matches = data.matches || [];

  return (
    <WidgetCard title="Cricket" icon="🏏">
      <div className="flex flex-col gap-2.5 pt-1">
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
        {data.source === 'sample' && (
          <div className="text-[9px] text-glance-muted/50 text-center">
            sample data — configure API for live scores
          </div>
        )}
      </div>
    </WidgetCard>
  );
}
