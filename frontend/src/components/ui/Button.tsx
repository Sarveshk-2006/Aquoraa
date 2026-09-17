import React from 'react';
import { Loader2 } from 'lucide-react';

export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  icon?: React.ReactNode;
  children: React.ReactNode;
}

const VARIANT_STYLES: Record<ButtonVariant, React.CSSProperties & { className: string }> = {
  primary: {
    className: 'text-white font-semibold transition-all duration-150 focus-visible:ring-2 focus-visible:ring-offset-1',
    background: 'var(--aq-teal)',
  },
  secondary: {
    className: 'text-slate-800 font-semibold border border-slate-200 bg-slate-100 hover:bg-slate-200 transition-all duration-150',
  },
  outline: {
    className: 'text-[#008080] font-semibold border bg-white hover:bg-[#e6f2f2] transition-all duration-150',
    borderColor: 'rgba(0,128,128,0.30)',
  },
  ghost: {
    className: 'text-slate-600 hover:text-[#008080] hover:bg-[#e6f2f2] transition-all duration-150',
  },
  danger: {
    className: 'text-white font-semibold bg-rose-600 hover:bg-rose-700 transition-all duration-150',
  },
};

const SIZE_CLASSES: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-xs rounded-lg gap-1.5',
  md: 'px-4 py-2 text-[13px] rounded-xl gap-2',
  lg: 'px-5 py-2.5 text-sm rounded-xl gap-2.5',
};

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  icon,
  children,
  className = '',
  disabled,
  style,
  ...props
}) => {
  const variantConfig = VARIANT_STYLES[variant];
  const { className: variantClass, ...variantStyle } = variantConfig;

  return (
    <button
      disabled={disabled || isLoading}
      className={`inline-flex items-center justify-center focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed select-none cursor-pointer ${variantClass} ${SIZE_CLASSES[size]} ${className}`}
      style={{ ...variantStyle, ...style }}
      onMouseEnter={(e) => {
        if (variant === 'primary' && !disabled && !isLoading) {
          (e.currentTarget as HTMLElement).style.background = 'var(--aq-teal-dark)';
        }
      }}
      onMouseLeave={(e) => {
        if (variant === 'primary') {
          (e.currentTarget as HTMLElement).style.background = 'var(--aq-teal)';
        }
      }}
      {...props}
    >
      {isLoading ? (
        <Loader2 className="w-3.5 h-3.5 animate-spin" />
      ) : icon ? (
        <span className="shrink-0">{icon}</span>
      ) : null}
      <span>{children}</span>
    </button>
  );
};

export default Button;
