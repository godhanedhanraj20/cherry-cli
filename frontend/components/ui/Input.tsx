import * as React from 'react';

type InputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  error?: boolean;
};

export function Input({ error = false, disabled, ...props }: InputProps) {
  return (
    <input
      {...props}
      disabled={disabled}
      style={{
        width: '100%',
        padding: '10px 12px',
        borderRadius: 8,
        border: `1px solid ${error ? '#ef4444' : '#d1d5db'}`,
        fontSize: 14,
        opacity: disabled ? 0.6 : 1,
        background: disabled ? '#f9fafb' : '#fff',
        transition: 'all 160ms ease-in-out',
        ...(props.style || {}),
      }}
    />
  );
}
