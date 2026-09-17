import React from 'react';

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  badge?: React.ReactNode;
  action?: React.ReactNode;
  icon?: React.ReactNode;
  className?: string;
}

export const SectionHeader: React.FC<SectionHeaderProps> = ({
  title,
  subtitle,
  badge,
  action,
  icon,
  className = '',
}) => {
  return (
    <div className={`flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${className}`}>
      <div className="space-y-0.5">
        <div className="flex items-center gap-2 flex-wrap">
          {icon && <span className="text-sky-600 shrink-0">{icon}</span>}
          <h2 className="text-lg font-bold text-slate-900 tracking-tight">{title}</h2>
          {badge}
        </div>
        {subtitle && <p className="text-xs text-slate-500 font-medium leading-normal">{subtitle}</p>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
};

export default SectionHeader;
