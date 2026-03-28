import { isValidElement, useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';

const ICON_BADGE_MAP = {
  system: 'SYS',
  weather: 'WTH',
  github: 'GIT',
  cricket: 'CRT',
  news: 'NWS',
  trending: 'TRD',
  lofi: 'LOF',
  clock: 'CLK',
  '💻': 'SYS',
  '🌤️': 'WTH',
  '🐙': 'GIT',
  '🏏': 'CRT',
  '📰': 'NWS',
  '🔥': 'TRD',
};

const LEGACY_ICON_MAP = {
  '💻': 'system',
  '🌤️': 'weather',
  '🐙': 'github',
  '🏏': 'cricket',
  '📰': 'news',
  '🔥': 'trending',
};

const SVG_ICON_NAMES = new Set([
  'system',
  'weather',
  'github',
  'cricket',
  'news',
  'trending',
  'lofi',
  'clock',
]);

function IconSvg({ iconName }) {
  switch (iconName) {
    case 'system':
      return (
        <svg viewBox="0 0 24 24" className="widget-icon-svg" aria-hidden="true">
          <rect x="3" y="4" width="18" height="12" rx="2" />
          <path d="M8 20h8" />
          <path d="M12 16v4" />
        </svg>
      );
    case 'weather':
      return (
        <svg viewBox="0 0 24 24" className="widget-icon-svg" aria-hidden="true">
          <path d="M7 17h9a4 4 0 0 0 0-8 5 5 0 0 0-9.5 1A3.5 3.5 0 0 0 7 17z" />
          <path d="M7 6.5V5" />
          <path d="M10.2 7.5l1-1" />
          <path d="M3.8 7.5l-1-1" />
        </svg>
      );
    case 'github':
      return (
        <svg viewBox="0 0 24 24" className="widget-icon-svg" aria-hidden="true">
          <path d="M12 3.5a8.5 8.5 0 0 0-2.7 16.6c.4.1.6-.2.6-.5v-1.7c-2.5.5-3.1-1-3.1-1-.4-1-.9-1.3-.9-1.3-.8-.5.1-.5.1-.5.9.1 1.4.9 1.4.9.8 1.4 2.2 1 2.7.8.1-.6.3-1 .6-1.2-2-.2-4.2-1-4.2-4.5 0-1 .4-1.9.9-2.6-.1-.2-.4-1.1.1-2.3 0 0 .8-.2 2.7 1a9.1 9.1 0 0 1 4.9 0c1.9-1.2 2.7-1 2.7-1 .5 1.2.2 2.1.1 2.3.6.7.9 1.6.9 2.6 0 3.5-2.2 4.3-4.3 4.5.3.3.7.8.7 1.7v2.5c0 .3.2.6.6.5A8.5 8.5 0 0 0 12 3.5z" />
        </svg>
      );
    case 'cricket':
      return (
        <svg viewBox="0 0 24 24" className="widget-icon-svg" aria-hidden="true">
          <path d="M5 19l6-6" />
          <path d="M8 22l8-8" />
          <circle cx="16.5" cy="7.5" r="3" />
        </svg>
      );
    case 'news':
      return (
        <svg viewBox="0 0 24 24" className="widget-icon-svg" aria-hidden="true">
          <rect x="4" y="5" width="16" height="14" rx="2" />
          <path d="M8 9h8" />
          <path d="M8 12h8" />
          <path d="M8 15h5" />
        </svg>
      );
    case 'trending':
      return (
        <svg viewBox="0 0 24 24" className="widget-icon-svg" aria-hidden="true">
          <path d="M4 16l5-5 4 4 7-8" />
          <path d="M14 7h6v6" />
        </svg>
      );
    case 'lofi':
      return (
        <svg viewBox="0 0 24 24" className="widget-icon-svg" aria-hidden="true">
          <circle cx="12" cy="12" r="7" />
          <circle cx="12" cy="12" r="2" />
          <path d="M12 5v3" />
          <path d="M19 12h-3" />
        </svg>
      );
    case 'clock':
      return (
        <svg viewBox="0 0 24 24" className="widget-icon-svg" aria-hidden="true">
          <circle cx="12" cy="12" r="8" />
          <path d="M12 8v5" />
          <path d="M12 13l3 2" />
        </svg>
      );
    default:
      return null;
  }
}

function resolveHeadingIcon(icon) {
  if (!icon) return null;
  if (isValidElement(icon)) return icon;
  if (typeof icon !== 'string') return null;

  const normalized = (LEGACY_ICON_MAP[icon] || icon).trim().toLowerCase();
  if (SVG_ICON_NAMES.has(normalized)) {
    return (
      <span className="widget-icon-svg-wrap">
        <IconSvg iconName={normalized} />
      </span>
    );
  }

  const badge = ICON_BADGE_MAP[icon] || ICON_BADGE_MAP[normalized];
  if (badge) {
    return <span className="widget-icon-badge">{badge}</span>;
  }

  const shortCode = normalized.slice(0, 3).toUpperCase();
  return <span className="widget-icon-badge">{shortCode || 'WGT'}</span>;
}

export default function WidgetCard({
  title,
  icon,
  children,
  className = '',
  scaleWithCard = true,
  bodyClassName = '',
  contentClassName = '',
}) {
  const cardRef = useRef(null);
  const [contentScale, setContentScale] = useState(1);

  useEffect(() => {
    const card = cardRef.current;
    if (!card) return;

    const measure = () => {
      const { width, height } = card.getBoundingClientRect();

      if (width < 260 || height < 160) {
        setContentScale(0.8);
        return;
      }
      if (width < 320 || height < 200) {
        setContentScale(0.88);
        return;
      }
      if (width < 420 || height < 240) {
        setContentScale(0.94);
        return;
      }

      setContentScale(1);
    };

    measure();

    if (typeof ResizeObserver !== 'undefined') {
      const observer = new ResizeObserver(measure);
      observer.observe(card);
      return () => observer.disconnect();
    }

    window.addEventListener('resize', measure);
    return () => window.removeEventListener('resize', measure);
  }, []);

  return (
    <motion.div
      ref={cardRef}
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.35, ease: [0.2, 0, 0, 1] }}
      className={`widget-tile ${className}`}
    >
      {title && (
        <div className="widget-header">
          {icon && <span className="widget-icon">{resolveHeadingIcon(icon)}</span>}
          <h3 className="widget-title">{title}</h3>
        </div>
      )}
      <div className={`widget-body ${bodyClassName}`}>
        <div
          className={`widget-content ${contentClassName}`}
          style={{ zoom: scaleWithCard ? contentScale : 1 }}
        >
          {children}
        </div>
      </div>
    </motion.div>
  );
}
