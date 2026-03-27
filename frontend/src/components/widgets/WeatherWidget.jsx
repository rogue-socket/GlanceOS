import WidgetCard from '../WidgetCard';

const ICON_MAP = {
  '01d': '☀️', '01n': '🌙',
  '02d': '⛅', '02n': '☁️',
  '03d': '☁️', '03n': '☁️',
  '04d': '☁️', '04n': '☁️',
  '09d': '🌧️', '09n': '🌧️',
  '10d': '🌦️', '10n': '🌧️',
  '11d': '⛈️', '11n': '⛈️',
  '13d': '❄️', '13n': '❄️',
  '50d': '🌫️', '50n': '🌫️',
};

export default function WeatherWidget({ data }) {
  if (!data) {
    return (
      <WidgetCard title="Weather" icon="🌤️">
        <div className="flex items-center justify-center h-full text-glance-muted text-sm">
          Waiting for data…
        </div>
      </WidgetCard>
    );
  }

  if (data.error) {
    return (
      <WidgetCard title="Weather" icon="🌤️">
        <div className="flex items-center justify-center h-full text-glance-muted text-sm">
          {data.error}
        </div>
      </WidgetCard>
    );
  }

  const icon = ICON_MAP[data.icon] || '🌡️';

  return (
    <WidgetCard title={data.city} icon="🌤️">
      <div className="flex flex-col items-center justify-center h-full gap-0.5">
        <div className="text-3xl mb-1">{icon}</div>
        <div className="text-3xl font-bold text-glance-text leading-none">
          {Math.round(data.temp)}°
        </div>
        <div className="text-[11px] text-glance-muted capitalize mt-1">{data.description}</div>
        <div className="flex items-center gap-3 mt-2 text-[10px] text-glance-muted/70">
          <span>Feels {Math.round(data.feels_like)}°</span>
          <span className="w-px h-3 bg-glance-border" />
          <span>💧 {data.humidity}%</span>
        </div>
      </div>
    </WidgetCard>
  );
}
