import * as React from 'react';

type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

export function Input(props: InputProps) {
  return (
    <input
      {...props}
      style={{
        width: '100%',
        padding: '10px 12px',
        borderRadius: 8,
        border: '1px solid #d1d5db',
        fontSize: 14,
        ...(props.style || {}),
      }}
    />
  );
}
