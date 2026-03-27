import { useState, useEffect } from 'react';
import WidgetCard from '../WidgetCard';

export default function ClockWidget() {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const id = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const hours = time.getHours().toString().padStart(2, '0');
  const minutes = time.getMinutes().toString().padStart(2, '0');
  const seconds = time.getSeconds().toString().padStart(2, '0');

  const dateStr = time.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  const greeting = time.getHours() < 12 ? 'Good morning' : time.getHours() < 18 ? 'Good afternoon' : 'Good evening';

  return (
    <WidgetCard>
      <div className="flex flex-col items-center justify-center h-full gap-0.5">
        <div className="text-[10px] uppercase tracking-[0.2em] text-glance-muted/60 font-medium mb-1">
          {greeting}
        </div>
        <div className="text-4xl font-bold text-glance-text tracking-tight tabular-nums leading-none">
          {hours}
          <span className="text-glance-accent animate-pulse">:</span>
          {minutes}
          <span className="text-lg text-glance-muted/50 ml-0.5">:{seconds}</span>
        </div>
        <div className="text-[11px] text-glance-muted mt-1.5">{dateStr}</div>
      </div>
    </WidgetCard>
  );
}
