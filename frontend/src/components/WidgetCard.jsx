import { motion } from 'framer-motion';

export default function WidgetCard({ title, icon, children, className = '' }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.35, ease: [0.2, 0, 0, 1] }}
      className={`widget-tile ${className}`}
    >
      {title && (
        <div className="widget-header">
          {icon && <span className="widget-icon">{icon}</span>}
          <h3 className="widget-title">{title}</h3>
        </div>
      )}
      <div className="widget-body">
        {children}
      </div>
    </motion.div>
  );
}
