import { useState, useCallback, useEffect, useRef } from 'react';
import { Responsive } from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

import { useWebSocket } from '../hooks/useWebSocket';
import { useTheme } from '../context/ThemeContext';
import ClockWidget from './widgets/ClockWidget';
import SystemWidget from './widgets/SystemWidget';
import WeatherWidget from './widgets/WeatherWidget';
import GitHubWidget from './widgets/GitHubWidget';
import CricketWidget from './widgets/CricketWidget';
import NewsWidget from './widgets/NewsWidget';
import TrendingWidget from './widgets/TrendingWidget';
import LofiWidget from './widgets/LofiWidget';
import CalendarWidget from './widgets/CalendarWidget';
import TodoWidget from './widgets/TodoWidget';

const STORAGE_KEY = 'glanceos-layouts';

const DEFAULT_LAYOUTS = {
  lg: [
    { i: 'clock',    x: 0,  y: 0, w: 3, h: 3, minW: 2, minH: 2 },
    { i: 'lofi',     x: 3,  y: 0, w: 3, h: 3, minW: 2, minH: 2 },
    { i: 'weather',  x: 6,  y: 0, w: 3, h: 3, minW: 2, minH: 2 },
    { i: 'system',   x: 9,  y: 0, w: 3, h: 3, minW: 2, minH: 2 },
    { i: 'cricket',  x: 0,  y: 3, w: 4, h: 5, minW: 3, minH: 3 },
    { i: 'news',     x: 4,  y: 3, w: 4, h: 5, minW: 3, minH: 3 },
    { i: 'trending', x: 8,  y: 3, w: 4, h: 5, minW: 3, minH: 3 },
    { i: 'calendar', x: 0,  y: 8, w: 4, h: 4, minW: 3, minH: 3 },
    { i: 'github',   x: 4,  y: 8, w: 8, h: 4, minW: 4, minH: 2 },
    { i: 'todo',     x: 0,  y: 12, w: 12, h: 3, minW: 4, minH: 2 },
  ],
  md: [
    { i: 'clock',    x: 0, y: 0, w: 5, h: 3, minW: 2, minH: 2 },
    { i: 'lofi',     x: 5, y: 0, w: 5, h: 3, minW: 2, minH: 2 },
    { i: 'weather',  x: 0, y: 3, w: 5, h: 3, minW: 2, minH: 2 },
    { i: 'system',   x: 5, y: 3, w: 5, h: 3, minW: 2, minH: 2 },
    { i: 'cricket',  x: 0, y: 6, w: 5, h: 5, minW: 3, minH: 3 },
    { i: 'news',     x: 5, y: 6, w: 5, h: 5, minW: 3, minH: 3 },
    { i: 'trending', x: 0, y: 11, w: 5, h: 5, minW: 3, minH: 3 },
    { i: 'github',   x: 5, y: 11, w: 5, h: 4, minW: 3, minH: 2 },
    { i: 'calendar', x: 0, y: 16, w: 10, h: 4, minW: 4, minH: 3 },
    { i: 'todo',     x: 0, y: 20, w: 10, h: 4, minW: 4, minH: 2 },
  ],
  sm: [
    { i: 'clock',    x: 0, y: 0,  w: 6, h: 3, minW: 2, minH: 2 },
    { i: 'lofi',     x: 0, y: 3,  w: 6, h: 3, minW: 2, minH: 2 },
    { i: 'weather',  x: 0, y: 6,  w: 6, h: 3, minW: 2, minH: 2 },
    { i: 'system',   x: 0, y: 9,  w: 6, h: 3, minW: 2, minH: 2 },
    { i: 'cricket',  x: 0, y: 12, w: 6, h: 5, minW: 3, minH: 3 },
    { i: 'news',     x: 0, y: 17, w: 6, h: 5, minW: 3, minH: 3 },
    { i: 'trending', x: 0, y: 22, w: 6, h: 5, minW: 3, minH: 3 },
    { i: 'github',   x: 0, y: 27, w: 6, h: 4, minW: 3, minH: 2 },
    { i: 'calendar', x: 0, y: 31, w: 6, h: 4, minW: 3, minH: 3 },
    { i: 'todo',     x: 0, y: 35, w: 6, h: 4, minW: 3, minH: 2 },
  ],
};

function loadLayouts() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      const merged = {};

      for (const bp of Object.keys(DEFAULT_LAYOUTS)) {
        const defaults = DEFAULT_LAYOUTS[bp] || [];
        const saved = Array.isArray(parsed?.[bp]) ? parsed[bp] : [];
        const savedById = new Map(saved.map(item => [item.i, item]));

        merged[bp] = defaults.map(item => ({
          ...item,
          ...(savedById.get(item.i) || {}),
        }));
      }

      return merged;
    }
  } catch { /* ignore */ }
  return DEFAULT_LAYOUTS;
}

function saveLayouts(layouts) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(layouts));
  } catch { /* ignore */ }
}

export default function Dashboard() {
  const { widgetData, connected } = useWebSocket();
  const { theme, themePreference, toggleTheme } = useTheme();
  const [layouts, setLayouts] = useState(loadLayouts);
  const gridContainerRef = useRef(null);
  const [gridWidth, setGridWidth] = useState(1200);

  useEffect(() => {
    const container = gridContainerRef.current;
    if (!container) return;

    const measure = () => {
      const nextWidth = container.clientWidth || window.innerWidth || 1200;
      setGridWidth(nextWidth);
    };

    measure();

    if (typeof ResizeObserver !== 'undefined') {
      const observer = new ResizeObserver(() => measure());
      observer.observe(container);
      return () => observer.disconnect();
    }

    window.addEventListener('resize', measure);
    return () => window.removeEventListener('resize', measure);
  }, []);

  const onLayoutChange = useCallback((_layout, allLayouts) => {
    setLayouts(allLayouts);
    saveLayouts(allLayouts);
  }, []);

  const resetLayout = useCallback(() => {
    setLayouts(DEFAULT_LAYOUTS);
    saveLayouts(DEFAULT_LAYOUTS);
  }, []);

  return (
    <div className="w-full h-screen bg-glance-bg overflow-auto">
      {/* ── Top bar ─────────────────────────────────── */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-glance-bg/80 border-b border-glance-border/50">
        <div className="flex items-center justify-between px-5 py-3">
          <div className="flex items-center gap-3">
            <h1 className="text-base font-semibold text-glance-text tracking-tight flex items-center gap-2">
              <span className="widget-icon-badge">GOS</span>
              GlanceOS
            </h1>
            <div className="flex items-center gap-1.5 ml-2 px-2 py-0.5 rounded-full bg-glance-accent-dim">
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  connected ? 'bg-glance-success' : 'bg-glance-danger'
                }`}
              />
              <span className="text-[10px] text-glance-muted font-medium">
                {connected ? 'Live' : 'Offline'}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={resetLayout}
              className="text-[11px] text-glance-muted/60 hover:text-glance-muted px-2 py-1 rounded-md hover:bg-glance-accent-dim transition-all cursor-pointer"
              title="Reset tile layout"
            >
              ↻ Reset
            </button>
            <button
              onClick={toggleTheme}
              className="text-[11px] text-glance-muted hover:text-glance-text px-2.5 py-1 rounded-md hover:bg-glance-accent-dim transition-all cursor-pointer"
              title="Cycle theme mode (Auto -> Light -> Dark)"
            >
              {themePreference === 'auto'
                ? `Auto · ${theme === 'dark' ? 'Dark' : 'Light'}`
                : `Manual · ${theme === 'dark' ? 'Dark' : 'Light'}`}
            </button>
          </div>
        </div>
      </header>

      {/* ── Tile grid ───────────────────────────────── */}
      <div className="p-3" ref={gridContainerRef}>
        <Responsive
          className="layout"
          width={gridWidth}
          layouts={layouts}
          onLayoutChange={onLayoutChange}
          breakpoints={{ lg: 1200, md: 900, sm: 480 }}
          cols={{ lg: 12, md: 10, sm: 6 }}
          rowHeight={56}
          isDraggable={true}
          isResizable={true}
          compactType="vertical"
          margin={[12, 12]}
          containerPadding={[0, 0]}
          useCSSTransforms={true}
          draggableHandle=".widget-header"
        >
          <div key="clock">
            <ClockWidget />
          </div>
          <div key="lofi">
            <LofiWidget data={widgetData.lofi} />
          </div>
          <div key="weather">
            <WeatherWidget data={widgetData.weather} />
          </div>
          <div key="system">
            <SystemWidget data={widgetData.system} />
          </div>
          <div key="cricket">
            <CricketWidget data={widgetData.cricket} />
          </div>
          <div key="news">
            <NewsWidget data={widgetData.news} />
          </div>
          <div key="trending">
            <TrendingWidget data={widgetData.trending} />
          </div>
          <div key="github">
            <GitHubWidget data={widgetData.github} />
          </div>
          <div key="calendar">
            <CalendarWidget data={widgetData.calendar} />
          </div>
          <div key="todo">
            <TodoWidget data={widgetData.todo} />
          </div>
        </Responsive>
      </div>
    </div>
  );
}
