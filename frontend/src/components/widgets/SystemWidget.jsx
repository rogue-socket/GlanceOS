import WidgetCard from '../WidgetCard';

function clampPercent(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return 0;
  return Math.max(0, Math.min(100, n));
}

function ProgressBar({ value, color = 'bg-glance-accent' }) {
  const clamped = clampPercent(value);
  return (
    <div className="w-full h-1.5 bg-glance-bg rounded-full overflow-hidden">
      <div
        className={`h-full rounded-full transition-all duration-700 ease-out ${color}`}
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}

function stateForPercent(pct) {
  const p = clampPercent(pct);
  if (p >= 85) {
    return {
      label: 'High',
      bar: 'bg-glance-danger',
      text: 'text-glance-danger',
      chip: 'bg-glance-danger/15 border-glance-danger/35 text-glance-danger',
    };
  }
  if (p >= 60) {
    return {
      label: 'Watch',
      bar: 'bg-glance-warning',
      text: 'text-glance-warning',
      chip: 'bg-glance-warning/15 border-glance-warning/35 text-glance-warning',
    };
  }

  return {
    label: 'Healthy',
    bar: 'bg-glance-success',
    text: 'text-glance-success',
    chip: 'bg-glance-success/15 border-glance-success/35 text-glance-success',
  };
}

function stateForTemp(celsius) {
  if (typeof celsius !== 'number') {
    return {
      label: 'Unknown',
      text: 'text-glance-muted',
      chip: 'bg-glance-bg/40 border-glance-border text-glance-muted',
    };
  }

  if (celsius >= 85) {
    return {
      label: 'Hot',
      text: 'text-glance-danger',
      chip: 'bg-glance-danger/15 border-glance-danger/35 text-glance-danger',
    };
  }
  if (celsius >= 70) {
    return {
      label: 'Warm',
      text: 'text-glance-warning',
      chip: 'bg-glance-warning/15 border-glance-warning/35 text-glance-warning',
    };
  }

  return {
    label: 'Cool',
    text: 'text-glance-success',
    chip: 'bg-glance-success/15 border-glance-success/35 text-glance-success',
  };
}

function formatBytes(bytes) {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

function formatTemp(tempData) {
  const c = tempData?.cpu_c;
  if (typeof c !== 'number') return 'N/A';
  return `${c.toFixed(1)}C`;
}

function tempSource(tempData) {
  const source = tempData?.source;
  if (!source || source === 'unavailable') return 'sensor unavailable';
  return source;
}

function MetricCard({ title, subtitle, percent, details }) {
  const state = stateForPercent(percent);
  const clamped = clampPercent(percent);

  return (
    <div className="rounded-lg border border-glance-border/45 bg-glance-bg/25 px-2.5 py-2">
      <div className="flex items-center justify-between gap-2 mb-1">
        <div className="text-[10px] uppercase tracking-[0.11em] text-glance-muted/85">{title}</div>
        <div className={`text-xs font-semibold tabular-nums ${state.text}`}>{Math.round(clamped)}%</div>
      </div>
      <ProgressBar value={clamped} color={state.bar} />
      <div className="flex items-center justify-between mt-1.5 gap-2">
        <div className="text-[10px] text-glance-muted truncate">{subtitle}</div>
        <div className="text-[10px] text-glance-text/85 whitespace-nowrap">{details}</div>
      </div>
    </div>
  );
}

export default function SystemWidget({ data }) {
  if (!data) {
    return (
      <WidgetCard title="System" icon="system">
        <div className="flex items-center justify-center h-full text-glance-muted text-sm">
          Waiting for data…
        </div>
      </WidgetCard>
    );
  }

  const { cpu, memory, disk, temperature } = data;
  const cpuState = stateForPercent(cpu?.percent);
  const tempC = typeof temperature?.cpu_c === 'number' ? temperature.cpu_c : null;
  const tempState = stateForTemp(tempC);

  return (
    <WidgetCard title="System" icon="system">
      <div className="flex flex-col gap-2.5 pt-1">
        <div className="grid grid-cols-2 gap-2">
          <div className="rounded-lg border border-glance-border/45 bg-glance-bg/25 px-2.5 py-2">
            <div className="flex items-center justify-between mb-1">
              <div className="text-[10px] uppercase tracking-[0.11em] text-glance-muted/85">CPU Load</div>
              <div className={`text-[10px] px-1.5 py-0.5 rounded-full border ${cpuState.chip}`}>
                {cpuState.label}
              </div>
            </div>
            <div className="text-xl font-semibold text-glance-text tabular-nums leading-none">
              {Math.round(clampPercent(cpu?.percent))}
              <span className="text-sm text-glance-muted ml-0.5">%</span>
            </div>
            <div className="text-[10px] text-glance-muted mt-1">{cpu?.cores || 0} logical cores</div>
          </div>

          <div className="rounded-lg border border-glance-border/45 bg-glance-bg/25 px-2.5 py-2">
            <div className="flex items-center justify-between mb-1">
              <div className="text-[10px] uppercase tracking-[0.11em] text-glance-muted/85">CPU Temp</div>
              <div className={`text-[10px] px-1.5 py-0.5 rounded-full border ${tempState.chip}`}>
                {tempState.label}
              </div>
            </div>
            <div className={`text-xl font-semibold tabular-nums leading-none ${tempState.text}`}>
              {formatTemp(temperature)}
            </div>
            <div className="text-[10px] text-glance-muted mt-1 truncate">{tempSource(temperature)}</div>
          </div>
        </div>

        <MetricCard
          title="CPU"
          subtitle="Processor utilization"
          percent={cpu?.percent}
          details={`${Math.round(clampPercent(cpu?.percent))}%`}
        />

        <MetricCard
          title="Memory"
          subtitle={`${formatBytes(memory?.used)} / ${formatBytes(memory?.total)}`}
          percent={memory?.percent}
          details={`${Math.round(clampPercent(memory?.percent))}%`}
        />

        <MetricCard
          title="Disk"
          subtitle={`${formatBytes(disk?.used)} / ${formatBytes(disk?.total)}`}
          percent={disk?.percent}
          details={`${Math.round(clampPercent(disk?.percent))}%`}
        />
      </div>
    </WidgetCard>
  );
}
