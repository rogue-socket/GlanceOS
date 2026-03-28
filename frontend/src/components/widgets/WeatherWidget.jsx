import WidgetCard from '../WidgetCard';

const ICON_MAP = {
  '01d': 'CLEAR', '01n': 'NIGHT',
  '02d': 'PARTLY', '02n': 'CLOUD',
  '03d': 'CLOUD', '03n': 'CLOUD',
  '04d': 'CLOUD', '04n': 'CLOUD',
  '09d': 'RAIN', '09n': 'RAIN',
  '10d': 'SHOWERS', '10n': 'RAIN',
  '11d': 'STORM', '11n': 'STORM',
  '13d': 'SNOW', '13n': 'SNOW',
  '50d': 'MIST', '50n': 'MIST',
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

  const icon = ICON_MAP[data.icon] || 'WEATHER';

  return (
    <WidgetCard title={data.city} icon="weather">
      <div className="flex flex-col items-center justify-center h-full gap-0.5">
        <div className="text-[10px] tracking-[0.18em] px-2 py-0.5 rounded-full border border-glance-accent/40 text-glance-accent bg-glance-accent-dim mb-1">
          {icon}
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
