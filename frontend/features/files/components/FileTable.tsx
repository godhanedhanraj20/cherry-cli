import type { FileItem } from '@/types/file';
import type { CSSProperties } from 'react';

interface FileTableProps {
  files: FileItem[];
}

export function FileTable({ files }: FileTableProps) {
  if (files.length === 0) {
    return <p>No files found.</p>;
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={thStyle}>ID</th>
            <th style={thStyle}>Name</th>
            <th style={thStyle}>Size</th>
            <th style={thStyle}>Date</th>
            <th style={thStyle}>Tags</th>
          </tr>
        </thead>
        <tbody>
          {files.map((file) => (
            <tr key={file.id}>
              <td style={tdStyle}>{file.id}</td>
              <td style={tdStyle}>{file.name}</td>
              <td style={tdStyle}>{file.size}</td>
              <td style={tdStyle}>{file.date}</td>
              <td style={tdStyle}>{file.tags || '-'}</td>
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
