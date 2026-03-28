import { useState, useEffect, useRef } from 'react';
import WidgetCard from '../WidgetCard';

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

export default function ClockWidget() {
  const [time, setTime] = useState(new Date());
  const rootRef = useRef(null);
  const [sizes, setSizes] = useState({
    title: 12,
    clock: 64,
    seconds: 24,
    date: 13,
  });

  useEffect(() => {
    const id = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;

    const measure = () => {
      const { width, height } = root.getBoundingClientRect();
      const usableW = Math.max(width - 12, 120);
      const usableH = Math.max(height - 16, 120);

      const clock = clamp(Math.min(usableW * 0.23, usableH * 0.5), 36, 180);
      const seconds = clamp(clock * 0.35, 14, 64);
      const title = clamp(clock * 0.18, 10, 28);
      const date = clamp(clock * 0.2, 11, 30);

      setSizes({ title, clock, seconds, date });
    };

    measure();

    if (typeof ResizeObserver !== 'undefined') {
      const observer = new ResizeObserver(measure);
      observer.observe(root);
      return () => observer.disconnect();
    }

    window.addEventListener('resize', measure);
    return () => window.removeEventListener('resize', measure);
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
    <WidgetCard scaleWithCard={false}>
      <div ref={rootRef} className="w-full h-full flex flex-col items-center justify-center text-center gap-1">
        <div
          className="uppercase tracking-[0.2em] text-glance-muted/60 font-medium"
          style={{ fontSize: `${sizes.title}px` }}
        >
          {greeting}
        </div>
        <div
          className="font-bold text-glance-text tracking-tight tabular-nums leading-none"
          style={{ fontSize: `${sizes.clock}px` }}
        >
          {hours}
          <span className="text-glance-accent animate-pulse">:</span>
          {minutes}
          <span className="text-glance-muted/50 ml-1" style={{ fontSize: `${sizes.seconds}px` }}>
            :{seconds}
          </span>
        </div>
        <div className="text-glance-muted" style={{ fontSize: `${sizes.date}px` }}>
          {dateStr}
        </div>
      </div>
    </WidgetCard>
  );
}
