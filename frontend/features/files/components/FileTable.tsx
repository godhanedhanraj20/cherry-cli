import type { FileItem } from '@/types/file';
import type { CSSProperties } from 'react';

interface ColumnConfig {
  key: keyof FileItem;
  label: string;
}

interface FileTableProps {
  files: FileItem[];
  columns?: ColumnConfig[];
  emptyMessage?: string;
  selectedIds: number[];
  deletingId: number | null;
  onSelect: (fileId: number, selected: boolean) => void;
  onSelectAll: (selected: boolean) => void;
  onDelete: (fileId: number) => void;
}

const defaultColumns: ColumnConfig[] = [
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

export function FileTable({
  files,
  columns = defaultColumns,
  emptyMessage = 'No files found',
  selectedIds,
  deletingId,
  onSelect,
  onSelectAll,
  onDelete,
}: FileTableProps) {
  if (files.length === 0) {
    return <div className='text-gray-500 text-center py-4'>{emptyMessage}</div>;
  }

  const allSelected = files.length > 0 && files.every((file) => selectedIds.includes(file.id));

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={thStyle}>
              <input type='checkbox' checked={allSelected} onChange={(e) => onSelectAll(e.target.checked)} />
            </th>
            {columns.map((column) => (
              <th key={column.key} style={thStyle}>
                {column.label}
              </th>
            ))}
            <th style={thStyle}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {files.map((file) => {
            const isSelected = selectedIds.includes(file.id);
            const isDeleting = deletingId === file.id;

            return (
              <tr key={file.id}>
                <td style={tdStyle}>
                  <input
                    type='checkbox'
                    checked={isSelected}
                    onChange={(e) => onSelect(file.id, e.target.checked)}
                    disabled={isDeleting}
                  />
                </td>
                {columns.map((column) => (
                  <td key={`${file.id}-${column.key}`} style={tdStyle}>
                    {renderValue(file, column.key)}
                  </td>
                ))}
                <td style={tdStyle}>
                  <button
                    type='button'
                    onClick={() => onDelete(file.id)}
                    disabled={isDeleting}
                    style={{
                      border: '1px solid #ef4444',
                      background: '#fff',
                      color: '#ef4444',
                      borderRadius: 6,
                      padding: '6px 10px',
                      cursor: isDeleting ? 'not-allowed' : 'pointer',
                      opacity: isDeleting ? 0.6 : 1,
                    }}
                  >
                    {isDeleting ? 'Deleting...' : 'Delete'}
                  </button>
                </td>
              </tr>
            );
          })}
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
