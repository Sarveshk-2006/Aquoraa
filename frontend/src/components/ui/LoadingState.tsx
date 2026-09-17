import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingStateProps {
  message?: string;
  variant?: 'spinner' | 'skeleton' | 'map';
}

export const StatSkeleton: React.FC = () => (
  <div className="p-4 rounded-xl bg-white border border-slate-200/80 animate-pulse space-y-2">
    <div className="h-3 bg-slate-200 rounded w-1/3"></div>
    <div className="h-7 bg-slate-200 rounded w-2/3"></div>
    <div className="h-3 bg-slate-100 rounded w-1/2"></div>
  </div>
);

export const CardSkeleton: React.FC = () => (
  <div className="p-5 rounded-xl bg-white border border-slate-200/80 animate-pulse space-y-4">
    <div className="flex items-center justify-between">
      <div className="h-4 bg-slate-200 rounded w-1/3"></div>
      <div className="h-4 bg-slate-100 rounded w-1/6"></div>
    </div>
    <div className="h-20 bg-slate-100 rounded-lg"></div>
    <div className="space-y-2">
      <div className="h-3 bg-slate-200 rounded w-5/6"></div>
      <div className="h-3 bg-slate-100 rounded w-4/6"></div>
    </div>
  </div>
);

export const MapSkeleton: React.FC = () => (
  <div className="w-full h-80 rounded-2xl bg-slate-200/70 border border-slate-200 animate-pulse flex flex-col items-center justify-center space-y-3 relative overflow-hidden">
    <div className="w-10 h-10 rounded-full bg-slate-300/80 flex items-center justify-center">
      <Loader2 className="w-5 h-5 text-slate-500 animate-spin" />
    </div>
    <span className="text-xs font-semibold text-slate-600">Rendering Geographic Canvas...</span>
  </div>
);

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading flood intelligence data...',
  variant = 'spinner',
}) => {
  if (variant === 'map') {
    return <MapSkeleton />;
  }

  if (variant === 'skeleton') {
    return (
      <div className="space-y-4 max-w-6xl mx-auto p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatSkeleton />
          <StatSkeleton />
          <StatSkeleton />
          <StatSkeleton />
        </div>
        <MapSkeleton />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center p-12 space-y-3 bg-white/60 border border-slate-200/60 rounded-2xl shadow-2xs">
      <Loader2 className="w-7 h-7 animate-spin text-sky-600" />
      <p className="text-xs font-semibold text-slate-700">{message}</p>
    </div>
  );
};

export default LoadingState;
