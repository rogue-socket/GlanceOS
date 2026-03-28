import WidgetCard from '../WidgetCard';

const ICON_MAP = {
  '01d': { symbol: '☀', label: 'CLEAR' },
  '01n': { symbol: '☾', label: 'NIGHT' },
  '02d': { symbol: '⛅', label: 'PARTLY' },
  '02n': { symbol: '☁', label: 'CLOUD' },
  '03d': { symbol: '☁', label: 'CLOUD' },
  '03n': { symbol: '☁', label: 'CLOUD' },
  '04d': { symbol: '☁', label: 'CLOUD' },
  '04n': { symbol: '☁', label: 'CLOUD' },
  '09d': { symbol: '☂', label: 'RAIN' },
  '09n': { symbol: '☂', label: 'RAIN' },
  '10d': { symbol: '☔', label: 'SHOWERS' },
  '10n': { symbol: '☔', label: 'SHOWERS' },
  '11d': { symbol: '⚡', label: 'STORM' },
  '11n': { symbol: '⚡', label: 'STORM' },
  '13d': { symbol: '❄', label: 'SNOW' },
  '13n': { symbol: '❄', label: 'SNOW' },
  '50d': { symbol: '≋', label: 'MIST' },
  '50n': { symbol: '≋', label: 'MIST' },
};

function toNumber(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function weatherPalette(iconCode) {
  if (!iconCode) {
    return {
      top: 'rgba(2,132,199,0.24)',
      bottom: 'rgba(15,23,42,0.26)',
      glow: 'rgba(56,189,248,0.24)',
      ring: 'rgba(56,189,248,0.38)',
    };
  }

  const code = String(iconCode);
  if (code.startsWith('01') || code.startsWith('02')) {
    return {
      top: 'rgba(251,191,36,0.22)',
      bottom: 'rgba(56,189,248,0.16)',
      glow: 'rgba(251,191,36,0.24)',
      ring: 'rgba(251,191,36,0.35)',
    };
  }
  if (code.startsWith('09') || code.startsWith('10')) {
    return {
      top: 'rgba(56,189,248,0.24)',
      bottom: 'rgba(30,64,175,0.2)',
      glow: 'rgba(56,189,248,0.26)',
      ring: 'rgba(56,189,248,0.35)',
    };
  }
  if (code.startsWith('11')) {
    return {
      top: 'rgba(100,116,139,0.26)',
      bottom: 'rgba(30,41,59,0.3)',
      glow: 'rgba(148,163,184,0.26)',
      ring: 'rgba(148,163,184,0.35)',
    };
  }
  if (code.startsWith('13')) {
    return {
      top: 'rgba(125,211,252,0.24)',
      bottom: 'rgba(148,163,184,0.22)',
      glow: 'rgba(186,230,253,0.24)',
      ring: 'rgba(186,230,253,0.35)',
    };
  }

  return {
    top: 'rgba(2,132,199,0.24)',
    bottom: 'rgba(15,23,42,0.26)',
    glow: 'rgba(56,189,248,0.24)',
    ring: 'rgba(56,189,248,0.38)',
  };
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function toPercent(value) {
  const n = toNumber(value);
  if (n === null) return null;
  return clamp(Math.round(n), 0, 100);
}

function comfortScore(temp, feelsLike, humidity) {
  if (temp === null || feelsLike === null || humidity === null) return null;

  const thermalDeltaPenalty = Math.abs(temp - feelsLike) * 4.5;
  const humidityPenalty = Math.max(0, humidity - 60) * 0.7;
  const drynessPenalty = Math.max(0, 35 - humidity) * 0.35;

  const raw = 100 - thermalDeltaPenalty - humidityPenalty - drynessPenalty;
  return clamp(Math.round(raw), 0, 100);
}

function comfortLabel(score) {
  if (score === null) return { label: 'Unknown', color: 'text-glance-muted' };
  if (score >= 80) return { label: 'Great', color: 'text-glance-success' };
  if (score >= 60) return { label: 'Okay', color: 'text-glance-accent' };
  if (score >= 40) return { label: 'Humid', color: 'text-glance-warning' };
  return { label: 'Harsh', color: 'text-glance-danger' };
}

function cityLabel(city) {
  if (!city) return 'Weather';
  return city.replace(',', ', ');
}

function roundedTemp(value) {
  const n = toNumber(value);
  return n === null ? '--' : Math.round(n);
}

function formatWind(value) {
  const n = toNumber(value);
  if (n === null) return '--';
  if (n < 10) return `${n.toFixed(1)} km/h`;
  return `${Math.round(n)} km/h`;
}

function freshnessMeta(source, fetchedAt) {
  if (source === 'offline') {
    return {
      label: 'Offline',
      chipClass: 'bg-glance-danger/15 border-glance-danger/40 text-glance-danger',
      ageText: 'Live feed unavailable',
    };
  }

  const parsed = fetchedAt ? Date.parse(fetchedAt) : NaN;
  if (!Number.isFinite(parsed)) {
    return {
      label: 'Live',
      chipClass: 'bg-glance-success/15 border-glance-success/35 text-glance-success',
      ageText: 'Updated recently',
    };
  }

  const ageMinutes = Math.max(0, Math.floor((Date.now() - parsed) / 60000));

  if (ageMinutes < 5) {
    return {
      label: 'Live',
      chipClass: 'bg-glance-success/15 border-glance-success/35 text-glance-success',
      ageText: 'Updated just now',
    };
  }
  if (ageMinutes < 15) {
    return {
      label: 'Recent',
      chipClass: 'bg-glance-accent/15 border-glance-accent/40 text-glance-accent',
      ageText: `Updated ${ageMinutes}m ago`,
    };
  }
  if (ageMinutes < 45) {
    return {
      label: 'Stale',
      chipClass: 'bg-glance-warning/15 border-glance-warning/40 text-glance-warning',
      ageText: `Updated ${ageMinutes}m ago`,
    };
  }

  return {
    label: 'Old',
    chipClass: 'bg-glance-danger/15 border-glance-danger/40 text-glance-danger',
    ageText: `Updated ${ageMinutes}m ago`,
  };
}

export default function WeatherWidget({ data }) {
  if (!data) {
    return (
      <WidgetCard title="Weather" icon="weather">
        <div className="flex items-center justify-center h-full text-glance-muted text-sm">
          Waiting for data…
        </div>
      </WidgetCard>
    );
  }

  const icon = ICON_MAP[data.icon] || { symbol: '*', label: 'WEATHER' };
  const palette = weatherPalette(data.icon);
  const temp = toNumber(data.temp);
  const feelsLike = toNumber(data.feels_like);
  const humidity = toNumber(data.humidity);
  const windKph = toNumber(data.wind_kph);
  const humidityPct = toPercent(humidity);
  const comfort = comfortScore(temp, feelsLike, humidity);
  const comfortMeta = comfortLabel(comfort);
  const freshness = freshnessMeta(data.source, data.fetched_at);
  const offlineReason = data.reason || data.description || 'Weather feed unavailable.';
  const isOffline = data.source === 'offline';

  return (
    <WidgetCard title="Weather" icon="weather">
      <div
        className="relative h-full overflow-hidden rounded-xl border border-glance-border/45 px-3 py-3"
        style={{
          background: `linear-gradient(160deg, ${palette.top}, ${palette.bottom})`,
        }}
      >
        <div
          className="absolute -top-8 -right-8 h-20 w-20 rounded-full blur-2xl"
          style={{ background: palette.glow }}
        />
        <div className="absolute -bottom-6 -left-6 h-16 w-16 rounded-full blur-2xl bg-glance-accent/15" />

        <div className="absolute inset-0 bg-[radial-gradient(circle_at_15%_18%,rgba(255,255,255,0.12),transparent_42%)] pointer-events-none" />

        <div className="relative h-full flex flex-col justify-between">
          <div className="flex items-center justify-between gap-2">
            <div className="text-[11px] text-glance-text/90 uppercase tracking-[0.11em] truncate">
              {cityLabel(data.city)}
            </div>
            <div className={`text-[10px] uppercase tracking-[0.1em] px-2 py-0.5 rounded-full border ${freshness.chipClass}`}>
              {freshness.label}
            </div>
          </div>

          <div className="grid grid-cols-[auto_1fr] gap-2.5 items-center mt-1.5">
            <div
              className="h-12 w-12 rounded-2xl border flex items-center justify-center text-[24px] leading-none shadow-[0_6px_22px_-12px_rgba(56,189,248,0.75)]"
              style={{
                borderColor: palette.ring,
                background: 'rgba(15,23,42,0.28)',
              }}
            >
              {icon.symbol}
            </div>
            <div className="min-w-0">
              <div className="flex items-end gap-1">
                <div className="text-4xl font-bold text-glance-text leading-none tabular-nums">
                  {roundedTemp(temp)}
                </div>
                <div className="text-base text-glance-text/80 leading-none mb-0.5">°C</div>
              </div>
              <div className="text-[12px] text-glance-text/90 uppercase tracking-[0.1em] mt-0.5 truncate">
                {icon.label}
              </div>
            </div>
          </div>

          <div className="space-y-0.5 mt-1">
            <div className="text-[12px] text-glance-text/85 capitalize line-clamp-2 leading-snug">
              {data.description}
            </div>
            <div className="text-[10px] text-glance-muted/85">
              {freshness.ageText}
            </div>
          </div>

          {isOffline && (
            <div className="rounded-lg border border-glance-danger/30 bg-glance-danger/10 px-2 py-1.5 mt-1">
              <div className="text-[10px] text-glance-danger/90 leading-snug">
                {offlineReason}
              </div>
              <div className="text-[10px] text-glance-muted mt-0.5">
                Add WEATHER_API_KEY in backend/.env for live weather.
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-2 mt-1.5">
            <div className="rounded-lg border border-glance-border/35 bg-glance-bg/30 px-2 py-1.5 min-w-0">
              <div className="text-[10px] uppercase tracking-[0.1em] text-glance-muted/85">Feels Like</div>
              <div className="text-sm text-glance-text font-medium mt-0.5 tabular-nums">
                {roundedTemp(feelsLike)}°C
              </div>
            </div>
            <div className="rounded-lg border border-glance-border/35 bg-glance-bg/30 px-2 py-1.5 min-w-0">
              <div className="text-[10px] uppercase tracking-[0.1em] text-glance-muted/85">Humidity</div>
              <div className="text-sm text-glance-text font-medium mt-0.5 tabular-nums">
                {humidityPct === null ? '--' : `${humidityPct}%`}
              </div>
              <div className="w-full h-1 rounded-full bg-glance-bg/50 mt-1 overflow-hidden">
                <div
                  className="h-full rounded-full bg-glance-accent transition-all duration-700"
                  style={{ width: `${humidityPct ?? 0}%` }}
                />
              </div>
            </div>
            <div className="rounded-lg border border-glance-border/35 bg-glance-bg/30 px-2 py-1.5 min-w-0">
              <div className="text-[10px] uppercase tracking-[0.1em] text-glance-muted/85">Wind</div>
              <div className="text-sm text-glance-text font-medium mt-0.5 tabular-nums">
                {formatWind(windKph)}
              </div>
            </div>
            <div className="rounded-lg border border-glance-border/35 bg-glance-bg/30 px-2 py-1.5 min-w-0">
              <div className="text-[10px] uppercase tracking-[0.1em] text-glance-muted/85">Comfort</div>
              <div className={`text-sm font-semibold mt-0.5 tabular-nums ${comfortMeta.color}`}>
                {comfort === null ? '--' : `${comfort}%`}
              </div>
              <div className={`text-[10px] mt-0.5 uppercase tracking-[0.08em] ${comfortMeta.color}`}>
                {comfortMeta.label}
              </div>
            </div>
          </div>
        </div>
      </div>
    </WidgetCard>
  );
}
