import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';

const ICON_BADGE_MAP = {
  '💻': 'SYS',
  '🌤️': 'WTH',
  '🐙': 'GIT',
  '🏏': 'CRT',
  '📰': 'NWS',
  '🔥': 'TRD',
};

function resolveHeadingIcon(icon) {
  if (!icon) return null;
  if (typeof icon !== 'string') return icon;

  const badge = ICON_BADGE_MAP[icon];
  if (badge) {
    return <span className="widget-icon-badge">{badge}</span>;
  }

  return <span className="widget-icon-fallback">{icon}</span>;
}

export default function WidgetCard({ title, icon, children, className = '' }) {
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
      <div className="widget-body">
        <div className="widget-content" style={{ zoom: contentScale }}>
          {children}
        </div>
      </div>
    </motion.div>
  );
}
