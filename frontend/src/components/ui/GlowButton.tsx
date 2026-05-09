import React from 'react';
import { motion } from 'framer-motion';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface GlowButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  glow?: boolean;
}

export const GlowButton: React.FC<GlowButtonProps> = ({ 
  children, 
  className, 
  variant = 'primary', 
  glow = true,
  ...props 
}) => {
  const variants = {
    primary: 'bg-primary text-background hover:bg-primary/90',
    secondary: 'bg-secondary text-white hover:bg-secondary/90',
    outline: 'border border-primary/50 text-primary hover:bg-primary/10',
    ghost: 'text-white/70 hover:text-white hover:bg-white/5',
  };

  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={cn(
        'px-6 py-2.5 rounded-lg font-medium transition-all duration-300 relative overflow-hidden flex items-center justify-center gap-2',
        variants[variant],
        glow && variant === 'primary' && 'neo-glow',
        glow && variant === 'secondary' && 'neo-glow-purple',
        className
      )}
      {...(props as any)}
    >
      <span className="relative z-10">{children}</span>
      {variant !== 'ghost' && (
        <div className="absolute inset-0 bg-white/20 transform -skew-x-12 -translate-x-full group-hover:animate-shimmer" />
      )}
    </motion.button>
  );
};
