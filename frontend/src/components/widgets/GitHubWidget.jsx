import WidgetCard from '../WidgetCard';

const EVENT_LABELS = {
  PushEvent: '📤 Push',
  PullRequestEvent: '🔀 PR',
  IssuesEvent: '🐛 Issue',
  CreateEvent: '✨ Create',
  DeleteEvent: '🗑️ Delete',
  WatchEvent: '⭐ Star',
  ForkEvent: '🍴 Fork',
  IssueCommentEvent: '💬 Comment',
};

function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function GitHubWidget({ data }) {
  if (!data) {
    return (
      <WidgetCard title="GitHub" icon="🐙">
        <div className="flex items-center justify-center h-full text-glance-muted text-sm">
          Waiting for data…
        </div>
      </WidgetCard>
    );
  }

  return (
    <WidgetCard title={`GitHub · ${data.username}`} icon="🐙">
      <div className="flex flex-col gap-2 pt-1">
        {data.events?.length === 0 && (
          <div className="text-sm text-glance-muted text-center">No recent activity</div>
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
