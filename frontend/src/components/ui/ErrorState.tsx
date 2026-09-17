import React from 'react';
import { AlertCircle, RotateCcw } from 'lucide-react';
import { Button } from './Button';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Information couldn\'t be loaded right now',
  message,
  onRetry,
  className = '',
}) => {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 text-center rounded-2xl bg-slate-50 border border-slate-200/90 space-y-3 ${className}`}
    >
      <div className="p-3 rounded-full bg-slate-100 text-slate-600">
        <AlertCircle className="w-6 h-6 text-slate-600" />
      </div>

      <div className="space-y-1 max-w-md">
        <h3 className="text-sm font-bold text-slate-900 tracking-tight">{title}</h3>
        <p className="text-xs text-slate-600 leading-relaxed font-normal">{message}</p>
      </div>

      {onRetry && (
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          icon={<RotateCcw className="w-3.5 h-3.5" />}
          className="mt-1"
        >
          Try again
        </Button>
      )}
    </div>
  );
};

export default ErrorState;
