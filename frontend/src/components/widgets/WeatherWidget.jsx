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

  if (data.source === 'offline') {
    return (
      <WidgetCard title={data.city || 'Weather'} icon="weather">
        <div className="flex flex-col items-center justify-center h-full gap-1">
          <div className="text-[11px] px-2 py-1 rounded-full border border-glance-border text-glance-muted">
            WEATHER
          </div>
          <div className="text-sm text-glance-muted">{data.description}</div>
          <div className="text-[10px] text-glance-muted/50 mt-1">
            Add WEATHER_API_KEY in .env for live data
          </div>
        </div>
      </WidgetCard>
    );
  }

  const icon = ICON_MAP[data.icon] || { symbol: '*', label: 'WEATHER' };

  return (
    <WidgetCard title={data.city} icon="weather">
      <div className="flex flex-col items-center justify-center h-full gap-0.5">
        <div className="text-[10px] tracking-[0.14em] px-2 py-0.5 rounded-full border border-glance-accent/40 text-glance-accent bg-glance-accent-dim mb-1 flex items-center gap-1.5">
          <span className="text-[14px] leading-none">{icon.symbol}</span>
          <span>{icon.label}</span>
        </div>
        <div className="text-3xl font-bold text-glance-text leading-none">
          {Math.round(data.temp)}
          <span className="text-xl ml-1">C</span>
        </div>
        <div className="text-[11px] text-glance-muted capitalize mt-1">{data.description}</div>
        <div className="flex items-center gap-3 mt-2 text-[10px] text-glance-muted/70">
          <span>Feels {Math.round(data.feels_like)}C</span>
          <span className="w-px h-3 bg-glance-border" />
          <span>RH {data.humidity}%</span>
        </div>
      </div>
    </WidgetCard>
  );
}
