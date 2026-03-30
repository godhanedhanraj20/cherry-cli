import * as React from 'react';

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  loading?: boolean;
};

export function Button({ children, loading = false, disabled, ...props }: ButtonProps) {
  const isDisabled = Boolean(disabled || loading);

  return (
    <button
      {...props}
      disabled={isDisabled}
      style={{
        width: '100%',
        padding: '10px 12px',
        borderRadius: 8,
        border: 'none',
        background: '#111827',
        color: '#ffffff',
        fontSize: 14,
        fontWeight: 600,
        cursor: isDisabled ? 'not-allowed' : 'pointer',
        opacity: isDisabled ? 0.6 : 1,
        ...(props.style || {}),
      }}
    >
      {loading ? 'Loading...' : children}
    </button>
  );
}
