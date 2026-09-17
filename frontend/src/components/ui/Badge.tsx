import React from 'react';

export type BadgeVariant = 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'accent' | 'brand' | 'beige';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
  className?: string;
  icon?: React.ReactNode;
}

const VARIANT_STYLES: Record<BadgeVariant, React.CSSProperties> = {
  success: { background: '#f0fdf4', color: '#15803d', border: '1px solid #bbf7d0' },
  warning: { background: '#fffbeb', color: '#92400e', border: '1px solid #fde68a' },
  danger:  { background: '#fff1f2', color: '#be123c', border: '1px solid #fecdd3' },
  info:    { background: '#eff6ff', color: '#1d4ed8', border: '1px solid #bfdbfe' },
  neutral: { background: '#f8fafc', color: '#475569', border: '1px solid #e2e8f0' },
  accent:  { background: '#e6f2f2', color: '#008080', border: '1px solid #b2d8d8' },
  brand:   { background: '#e6f2f2', color: '#008080', border: '1px solid #b2d8d8' },
  beige:   { background: '#F5F5DC', color: '#4a4a28', border: '1px solid #e6e6cc' },
};

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'md',
  className = '',
  icon,
}) => {
  const sizeStyle = size === 'sm'
    ? { padding: '2px 8px', fontSize: '10px', lineHeight: '1.4' }
    : { padding: '3px 10px', fontSize: '11px', lineHeight: '1.4' };

  return (
    <span
      className={`inline-flex items-center gap-1 font-semibold rounded-full ${className}`}
      style={{ ...VARIANT_STYLES[variant], ...sizeStyle, letterSpacing: '0.01em' }}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      <span>{children}</span>
    </span>
  );
};

export default Badge;
