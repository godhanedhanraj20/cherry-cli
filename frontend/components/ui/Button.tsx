import * as React from 'react';

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement>;

export function Button({ children, ...props }: ButtonProps) {
  return (
    <button
      {...props}
      style={{
        width: '100%',
        padding: '10px 12px',
        borderRadius: 8,
        border: 'none',
        background: '#111827',
        color: '#ffffff',
        fontSize: 14,
        fontWeight: 600,
        cursor: props.disabled ? 'not-allowed' : 'pointer',
        opacity: props.disabled ? 0.6 : 1,
        ...(props.style || {}),
      }}
    >
      {children}
    </button>
  );
}
