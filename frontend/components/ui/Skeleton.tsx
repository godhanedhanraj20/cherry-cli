import type { CSSProperties } from 'react';

interface SkeletonProps {
  height?: number;
  width?: string | number;
  style?: CSSProperties;
}

export function Skeleton({ height = 14, width = '100%', style }: SkeletonProps) {
  return (
    <div
      aria-hidden='true'
      style={{
        height,
        width,
        borderRadius: 6,
        background: '#e5e7eb',
        ...style,
      }}
    />
  );
}
