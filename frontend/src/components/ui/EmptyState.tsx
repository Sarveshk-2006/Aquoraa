import React from 'react';
import { Layers } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description: string;
  badge?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  badge,
  icon,
  action,
  className = '',
}) => {
  return (
    <div
      className={`flex flex-col items-center justify-center p-10 text-center border border-dashed border-slate-200/90 rounded-2xl bg-white/80 space-y-3 ${className}`}
    >
      <div className="p-3 rounded-full bg-slate-50 text-slate-400 border border-slate-100">
        {icon || <Layers className="w-6 h-6 text-slate-400" />}
      </div>
      <div className="space-y-1 max-w-sm">
        <h3 className="text-sm font-bold text-slate-900 tracking-tight">{title}</h3>
        <p className="text-xs text-slate-500 leading-relaxed font-normal">{description}</p>
      </div>
      {badge && (
        <span className="px-2.5 py-0.5 text-[10px] font-semibold rounded-full bg-slate-100 text-slate-600 border border-slate-200">
          {badge}
        </span>
      )}
      {action && <div className="pt-1">{action}</div>}
    </div>
  );
};

export default EmptyState;
