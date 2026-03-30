import type { FileItem } from '@/types/file';
import type { CSSProperties } from 'react';

interface FileTableProps {
  files: FileItem[];
}

const columns: Array<{ key: keyof FileItem; label: string }> = [
  { key: 'id', label: 'ID' },
  { key: 'name', label: 'Name' },
  { key: 'size', label: 'Size' },
  { key: 'date', label: 'Date' },
  { key: 'tags', label: 'Tags' },
];

const renderValue = (file: FileItem, key: keyof FileItem) => {
  const value = file[key];
  if (key === 'tags' && (!value || String(value).trim() === '')) {
    return '-';
  }
  return String(value ?? '-');
};

export function FileTable({ files }: FileTableProps) {
  if (files.length === 0) {
    return <p>No files found.</p>;
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key} style={thStyle}>
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {files.map((file) => (
            <tr key={file.id}>
              {columns.map((column) => (
                <td key={`${file.id}-${column.key}`} style={tdStyle}>
                  {renderValue(file, column.key)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const thStyle: CSSProperties = {
  textAlign: 'left',
  padding: '10px 12px',
  borderBottom: '1px solid #e5e7eb',
  fontSize: 13,
};

const tdStyle: CSSProperties = {
  padding: '10px 12px',
  borderBottom: '1px solid #f3f4f6',
  fontSize: 13,
};
