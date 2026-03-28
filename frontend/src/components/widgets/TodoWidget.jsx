import WidgetCard from '../WidgetCard';

function priorityClass(priority) {
  if (priority >= 4) return 'text-glance-danger';
  if (priority === 3) return 'text-glance-warning';
  if (priority === 2) return 'text-glance-accent';
  return 'text-glance-muted';
}

export default function TodoWidget({ data }) {
  if (!data) {
    return (
      <WidgetCard title="Todo" icon="todo">
        <div className="flex items-center justify-center h-full text-glance-muted text-sm">
          Waiting for data...
        </div>
      </WidgetCard>
    );
  }

  const tasks = data.tasks || [];

  if (data.status === 'unconfigured') {
    return (
      <WidgetCard title="Todo" icon="todo">
        <div className="flex flex-col gap-2 text-xs text-glance-muted pt-1">
          <div>Todoist not connected.</div>
          <div className="text-[11px] text-glance-text/90">Add TODOIST_API_TOKEN in backend/.env.</div>
        </div>
      </WidgetCard>
    );
  }

  if (data.status === 'error') {
    return (
      <WidgetCard title="Todo" icon="todo">
        <div className="flex flex-col gap-2 text-xs text-glance-muted pt-1">
          <div>Todoist connection error.</div>
          <div className="text-[11px] text-glance-text/90">{data.message || 'Unable to load tasks'}</div>
        </div>
      </WidgetCard>
    );
  }

  return (
    <WidgetCard title="Todo" icon="todo">
      <div className="flex flex-col gap-1.5 pt-1">
        <div className="text-[10px] uppercase tracking-[0.12em] text-glance-muted/70">
          Source: {data.source || 'todoist'}
        </div>

        {tasks.length === 0 && (
          <div className="text-sm text-glance-muted text-center py-2">No open tasks</div>
        )}

        {tasks.slice(0, 10).map((task, idx) => (
          <div
            key={task.id || idx}
            className="flex items-start gap-2 py-1.5 border-b border-glance-border/20 last:border-0"
          >
            <span className={`text-[10px] font-mono mt-0.5 shrink-0 ${priorityClass(task.priority)}`}>
              P{task.priority || 1}
            </span>
            <div className="min-w-0 flex-1">
              <div className="text-xs text-glance-text line-clamp-1">{task.content}</div>
              {task.due && <div className="text-[10px] text-glance-muted mt-0.5">Due: {task.due}</div>}
            </div>
          </div>
        ))}
      </div>
    </WidgetCard>
  );
}
