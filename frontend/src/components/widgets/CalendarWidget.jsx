import WidgetCard from '../WidgetCard';

function formatWhen(event) {
  if (!event) return '';
  if (event.all_day) {
    return event.start ? `${event.start.split(' ')[0]} · All day` : 'All day';
  }

  if (!event.start) return 'Time unavailable';
  const parts = event.start.split(' ');
  if (parts.length < 2) return event.start;
  return `${parts[0]} · ${parts[1]}`;
}

export default function CalendarWidget({ data }) {
  if (!data) {
    return (
      <WidgetCard title="Calendar" icon="calendar">
        <div className="flex items-center justify-center h-full text-glance-muted text-sm">
          Waiting for data...
        </div>
      </WidgetCard>
    );
  }

  const events = data.events || [];

  if (data.status === 'unconfigured') {
    return (
      <WidgetCard title="Calendar" icon="calendar">
        <div className="flex flex-col gap-2 text-xs text-glance-muted pt-1">
          <div>Google Calendar not connected.</div>
          <div className="text-[11px] text-glance-text/90">
            Add GOOGLE_CALENDAR_ICS_URL or GOOGLE_CALENDAR_ID + GOOGLE_CALENDAR_API_KEY in backend/.env.
          </div>
        </div>
      </WidgetCard>
    );
  }

  if (data.status === 'error') {
    return (
      <WidgetCard title="Calendar" icon="calendar">
        <div className="flex flex-col gap-2 text-xs text-glance-muted pt-1">
          <div>Calendar connection error.</div>
          <div className="text-[11px] text-glance-text/90">{data.message || 'Unable to load events'}</div>
        </div>
      </WidgetCard>
    );
  }

  return (
    <WidgetCard title="Calendar" icon="calendar">
      <div className="flex flex-col gap-1.5 pt-1">
        <div className="text-[10px] uppercase tracking-[0.12em] text-glance-muted/70">
          Source: {data.source || 'google'}
        </div>

        {events.length === 0 && (
          <div className="text-sm text-glance-muted text-center py-2">No upcoming events</div>
        )}

        {events.map((event, idx) => (
          <div
            key={event.id || idx}
            className="flex items-start gap-2 py-1.5 border-b border-glance-border/20 last:border-0"
          >
            <span className="text-glance-accent/70 text-[10px] font-mono mt-0.5 shrink-0">
              {String(idx + 1).padStart(2, '0')}
            </span>
            <div className="min-w-0 flex-1">
              <div className="text-xs text-glance-text line-clamp-1">{event.title}</div>
              <div className="text-[10px] text-glance-muted mt-0.5">{formatWhen(event)}</div>
              {event.location && (
                <div className="text-[10px] text-glance-muted/80 line-clamp-1">{event.location}</div>
              )}
            </div>
          </div>
        ))}
      </div>
    </WidgetCard>
  );
}
