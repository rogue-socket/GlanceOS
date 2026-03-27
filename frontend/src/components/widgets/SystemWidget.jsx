import WidgetCard from '../WidgetCard';

function ProgressBar({ value, color = 'bg-glance-accent' }) {
  return (
    <div className="w-full h-1.5 bg-glance-bg rounded-full overflow-hidden">
      <div
        className={`h-full rounded-full transition-all duration-700 ease-out ${color}`}
        style={{ width: `${Math.min(value, 100)}%` }}
      />
    </div>
  );
}

function colorForPercent(pct) {
  if (pct > 85) return 'bg-glance-danger';
  if (pct > 60) return 'bg-glance-warning';
  return 'bg-glance-success';
}

function formatBytes(bytes) {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

export default function SystemWidget({ data }) {
  if (!data) {
    return (
      <WidgetCard title="System" icon="💻">
        <div className="flex items-center justify-center h-full text-glance-muted text-sm">
          Waiting for data…
        </div>
      </WidgetCard>
    );
  }

  const { cpu, memory, disk } = data;

  return (
    <WidgetCard title="System" icon="💻">
      <div className="flex flex-col gap-3 pt-1">
        {/* CPU */}
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-glance-muted">CPU ({cpu.cores} cores)</span>
            <span className="text-glance-text font-medium">{cpu.percent}%</span>
          </div>
          <ProgressBar value={cpu.percent} color={colorForPercent(cpu.percent)} />
        </div>

        {/* Memory */}
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-glance-muted">Memory</span>
            <span className="text-glance-text font-medium">
              {formatBytes(memory.used)} / {formatBytes(memory.total)}
            </span>
          </div>
          <ProgressBar value={memory.percent} color={colorForPercent(memory.percent)} />
        </div>

        {/* Disk */}
        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-glance-muted">Disk</span>
            <span className="text-glance-text font-medium">
              {formatBytes(disk.used)} / {formatBytes(disk.total)}
            </span>
          </div>
          <ProgressBar value={disk.percent} color={colorForPercent(disk.percent)} />
        </div>
      </div>
    </WidgetCard>
  );
}
