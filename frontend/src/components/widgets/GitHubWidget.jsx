import WidgetCard from '../WidgetCard';

const WEEKS_TO_SHOW = 10;
const CELL_SIZE_PX = 8;

const EVENT_LABELS = {
  PushEvent: 'PUSH',
  PullRequestEvent: 'PR',
  IssuesEvent: 'ISSUE',
  CreateEvent: 'CREATE',
  DeleteEvent: 'DELETE',
  WatchEvent: 'STAR',
  ForkEvent: 'FORK',
  IssueCommentEvent: 'COMMENT',
};

function timeAgo(dateStr) {
  if (!dateStr) return 'now';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function normalizeContributionLevel(level) {
  const parsed = Number(level);
  if (!Number.isFinite(parsed)) return 0;
  return Math.max(0, Math.min(4, Math.round(parsed)));
}

function contributionColor(level) {
  const normalized = normalizeContributionLevel(level);
  if (normalized >= 4) return '#39d353';
  if (normalized === 3) return '#26a641';
  if (normalized === 2) return '#006d32';
  if (normalized === 1) return '#0e4429';
  return 'rgba(100,116,139,0.24)';
}

export default function GitHubWidget({ data }) {
  if (!data) {
    return (
      <WidgetCard title="GitHub" icon="github">
        <div className="flex items-center justify-center h-full text-glance-muted text-sm">
          Waiting for data…
        </div>
      </WidgetCard>
    );
  }

  const weeks = data.contributions?.weeks || [];
  const normalizedWeeks = (() => {
    const trailing = weeks.slice(-WEEKS_TO_SHOW);
    if (trailing.length >= WEEKS_TO_SHOW) return trailing;

    const missing = WEEKS_TO_SHOW - trailing.length;
    const emptyWeek = [0, 0, 0, 0, 0, 0, 0];
    return [...Array.from({ length: missing }, () => emptyWeek), ...trailing];
  })();

  return (
    <WidgetCard title={`GitHub · ${data.username}`} icon="github" scaleWithCard={false}>
      <div className="flex flex-col gap-2 pt-1">
        <div className="flex items-center justify-between">
          <div className="text-[10px] uppercase tracking-[0.12em] text-glance-muted/80">Contribution Graph</div>
          <div className="text-[10px] text-glance-muted/60">{data.source}</div>
        </div>

        {weeks.length > 0 ? (
          <div className="w-full overflow-x-auto pb-1">
            <div
              className="inline-grid gap-[2px]"
              style={{ gridTemplateColumns: `repeat(${normalizedWeeks.length}, ${CELL_SIZE_PX}px)` }}
            >
              {normalizedWeeks.map((week, weekIndex) => (
                <div
                  key={`week-${weekIndex}`}
                  className="grid gap-[2px]"
                  style={{ gridTemplateRows: `repeat(7, ${CELL_SIZE_PX}px)` }}
                >
                  {week.map((level, dayIndex) => (
                    <span
                      key={`${weekIndex}-${dayIndex}`}
                      className="rounded-[2px] block"
                      style={{
                        backgroundColor: contributionColor(level),
                        width: `${CELL_SIZE_PX}px`,
                        height: `${CELL_SIZE_PX}px`,
                      }}
                      title={`Level ${level}`}
                    />
                  ))}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-[11px] text-glance-muted">Contribution graph unavailable right now</div>
        )}

        {data.events?.length === 0 && (
          <div className="text-sm text-glance-muted text-center">No recent public activity</div>
        )}
        {data.events?.map((event) => (
          <div
            key={event.id}
            className="flex items-center justify-between text-xs gap-2 py-1 border-b border-glance-border/20 last:border-0"
          >
            <span className="text-glance-muted whitespace-nowrap">
              {EVENT_LABELS[event.type] || event.type}
            </span>
            <span className="text-glance-text truncate flex-1 text-right">
              {event.repo}
            </span>
            <span className="text-glance-muted whitespace-nowrap">
              {timeAgo(event.created_at)}
            </span>
          </div>
        ))}
      </div>
    </WidgetCard>
  );
}
