import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hoverable?: boolean;
  onClick?: () => void;
}

const PADDING_CLASSES = {
  none: '',
  sm:   'p-4',
  md:   'p-5',
  lg:   'p-6',
};

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  padding = 'md',
  hoverable = false,
  onClick,
}) => {
  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-2xl transition-all duration-150 ${
        hoverable ? 'hover:shadow-aq-card-hover cursor-pointer' : ''
      } ${PADDING_CLASSES[padding]} ${className}`}
      style={{
        boxShadow: '0 1px 3px rgba(15,35,64,0.08), 0 0 0 1px rgba(15,35,64,0.06)',
      }}
    >
      {children}
    </div>
  );
};

export default Card;
