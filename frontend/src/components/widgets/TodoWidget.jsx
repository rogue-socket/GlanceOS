import { useEffect, useState } from 'react';
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
  const sections = data.sections || [];
  const displaySections = sections.length > 0 ? sections : (tasks.length > 0 ? [{ id: 'inbox', name: 'Inbox', tasks }] : []);
  const [collapsed, setCollapsed] = useState({});

  useEffect(() => {
    setCollapsed((prev) => {
      const next = {};
      for (const section of displaySections) {
        const key = String(section.id || section.name || 'section');
        next[key] = prev[key] ?? false;
      }
      return next;
    });
  }, [displaySections]);

  function toggleSection(section) {
    const key = String(section.id || section.name || 'section');
    setCollapsed((prev) => ({ ...prev, [key]: !prev[key] }));
  }

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
        <div className="flex items-center justify-between gap-2 text-[10px] uppercase tracking-[0.12em] text-glance-muted/70">
          <span className="flex items-center gap-1"><span aria-hidden="true">🗂</span>Inbox only</span>
          <div className="flex items-center gap-2 normal-case tracking-normal">
            <a href={data.view_url || 'todoist://inbox'} className="text-glance-accent hover:underline">
              <span aria-hidden="true">↗</span> Open Inbox
            </a>
            <a href={data.add_task_url || 'todoist://addtask'} className="text-glance-accent hover:underline">
              <span aria-hidden="true">＋</span> Add Task
            </a>
          </div>
        </div>

        <div className="text-[10px] uppercase tracking-[0.12em] text-glance-muted/70">
          Source: {data.source || 'todoist'}
        </div>

        {tasks.length === 0 && (
          <div className="text-sm text-glance-muted text-center py-2">No open Inbox tasks</div>
        )}

        {displaySections.slice(0, 6).map((section, sectionIdx) => {
          const key = String(section.id || section.name || sectionIdx);
          const isCollapsed = !!collapsed[key];

          return (
            <div key={section.id || sectionIdx} className="border-b border-glance-border/20 last:border-0">
              <button
                type="button"
                onClick={() => toggleSection(section)}
                className="w-full flex items-center justify-between gap-2 py-1 text-left"
              >
                <span className="text-[10px] uppercase tracking-[0.1em] text-glance-accent/90 flex items-center gap-1">
                  <span
                    aria-hidden="true"
                    className={`inline-block transition-transform duration-150 ${isCollapsed ? '' : 'rotate-90'}`}
                  >
                    ▸
                  </span>
                  {section.name || 'Section'}
                </span>
                <span className="text-[10px] text-glance-muted tabular-nums">{(section.tasks || []).length}</span>
              </button>

              {!isCollapsed && (
                <div className="flex flex-col gap-1 pb-1">
                  {(section.tasks || []).slice(0, 5).map((task, idx) => (
                    <a
                      key={task.id || idx}
                      href={task.todoist_url || `todoist://task?id=${task.id}`}
                      className="flex items-start gap-2 py-1 rounded-sm hover:bg-glance-accent-dim/35"
                    >
                      <span className={`text-[10px] font-mono mt-0.5 shrink-0 ${priorityClass(task.priority)}`}>
                        P{task.priority || 1}
                      </span>
                      <div className="min-w-0 flex-1">
                        <div className="text-xs text-glance-text line-clamp-1 flex items-center gap-1">
                          <span className="text-glance-muted" aria-hidden="true">○</span>
                          <span>{task.content}</span>
                        </div>
                        {task.due && <div className="text-[10px] text-glance-muted mt-0.5 ml-[13px]">Due: {task.due}</div>}
                      </div>
                    </a>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </WidgetCard>
  );
}
