import { useEffect, useState } from 'react';
import type { FileItem } from '@/types/file';
import type { CSSProperties, KeyboardEvent } from 'react';

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
  taggingId: number | null;
  renamingId: number | null;
  activeTagFilters: string[];
  onSelect: (fileId: number, selected: boolean) => void;
  onSelectAll: (selected: boolean) => void;
  onDelete: (fileId: number) => void;
  onTagClick: (tag: string) => void;
  onAddTag: (fileId: number, tag: string) => void;
  onRemoveTag: (fileId: number, tag: string) => void;
  onRename: (fileId: number, newName: string) => void;
}

const defaultColumns: ColumnConfig[] = [
  { key: 'id', label: 'ID' },
  { key: 'name', label: 'Name' },
  { key: 'size', label: 'Size' },
  { key: 'date', label: 'Date' },
  { key: 'tags', label: 'Tags' },
];

const parseTags = (tagsValue: string): string[] => {
  return tagsValue
    .split(',')
    .map((tag) => tag.trim().toLowerCase())
    .filter(Boolean);
};

const renderValue = (file: FileItem, key: keyof FileItem) => {
  return String(file[key] ?? '-');
};

export function FileTable({
  files,
  columns = defaultColumns,
  emptyMessage = 'No files found',
  selectedIds,
  deletingId,
  taggingId,
  renamingId,
  activeTagFilters,
  onSelect,
  onSelectAll,
  onDelete,
  onTagClick,
  onAddTag,
  onRemoveTag,
  onRename,
}: FileTableProps) {
  const [tagInputs, setTagInputs] = useState<Record<number, string>>({});
  const [editingNameId, setEditingNameId] = useState<number | null>(null);
  const [editingName, setEditingName] = useState('');

  useEffect(() => {
    if (renamingId !== null) return;
    if (editingNameId === null) return;
    setEditingNameId(null);
    setEditingName('');
  }, [editingNameId, renamingId]);

  if (files.length === 0) {
    return <div className='text-gray-500 text-center py-4'>{emptyMessage}</div>;
  }

  const allSelected = files.length > 0 && files.every((file) => selectedIds.includes(file.id));

  const beginRename = (file: FileItem) => {
    setEditingNameId(file.id);
    setEditingName(file.name);
  };

  const saveRename = (file: FileItem) => {
    const nextName = editingName.trim();
    setEditingNameId(null);
    if (!nextName || nextName === file.name) {
      setEditingName('');
      return;
    }
    onRename(file.id, nextName);
    setEditingName('');
  };

  const handleRenameKeyDown = (event: KeyboardEvent<HTMLInputElement>, file: FileItem) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      saveRename(file);
      return;
    }
    if (event.key === 'Escape') {
      event.preventDefault();
      setEditingNameId(null);
      setEditingName('');
    }
  };

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
            const rowTags = parseTags(file.tags);

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
                    {column.key === 'name' ? (
                      editingNameId === file.id ? (
                        <input
                          value={editingName}
                          onChange={(e) => setEditingName(e.target.value)}
                          onBlur={() => saveRename(file)}
                          onKeyDown={(event) => handleRenameKeyDown(event, file)}
                          autoFocus
                          disabled={renamingId === file.id}
                          style={inlineInputStyle}
                        />
                      ) : (
                        <button type='button' onClick={() => beginRename(file)} style={fileNameButtonStyle}>
                          {file.name}
                        </button>
                      )
                    ) : column.key === 'tags' ? (
                      <div style={tagsWrapStyle}>
                        {rowTags.length > 0 ? (
                          rowTags.map((tag) => (
                            <span
                              key={`${file.id}-${tag}`}
                              style={{
                                ...tagChipStyle,
                                ...(activeTagFilters.includes(tag) ? activeTagChipStyle : null),
                              }}
                            >
                              <button type='button' onClick={() => onTagClick(tag)} style={tagLabelButtonStyle}>
                                {tag}
                              </button>
                              <button
                                type='button'
                                onClick={(event) => {
                                  event.stopPropagation();
                                  onRemoveTag(file.id, tag);
                                }}
                                disabled={taggingId === file.id}
                                aria-label={`Remove tag ${tag}`}
                                style={tagRemoveButtonStyle}
                              >
                                ×
                              </button>
                            </span>
                          ))
                        ) : (
                          <span>-</span>
                        )}
                        <div style={tagInputWrapStyle}>
                          <input
                            value={tagInputs[file.id] ?? ''}
                            onChange={(e) => setTagInputs((prev) => ({ ...prev, [file.id]: e.target.value }))}
                            onKeyDown={(event) => {
                              if (event.key !== 'Enter') return;
                              event.preventDefault();
                              const nextTag = (tagInputs[file.id] ?? '').trim();
                              if (!nextTag) return;
                              setTagInputs((prev) => ({ ...prev, [file.id]: '' }));
                              onAddTag(file.id, nextTag);
                            }}
                            placeholder='+ tag'
                            disabled={taggingId === file.id}
                            style={tagInputStyle}
                          />
                        </div>
                      </div>
                    ) : (
                      renderValue(file, column.key)
                    )}
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

const tagsWrapStyle: CSSProperties = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: 6,
  alignItems: 'center',
};

const tagChipStyle: CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: 4,
  borderRadius: 999,
  padding: '2px 8px',
  border: '1px solid #d1d5db',
  background: '#f9fafb',
};

const activeTagChipStyle: CSSProperties = {
  border: '1px solid #2563eb',
  background: '#eff6ff',
};

const tagLabelButtonStyle: CSSProperties = {
  background: 'transparent',
  border: 0,
  padding: 0,
  cursor: 'pointer',
  fontSize: 12,
};

const tagRemoveButtonStyle: CSSProperties = {
  background: 'transparent',
  border: 0,
  padding: 0,
  cursor: 'pointer',
  color: '#ef4444',
  fontSize: 14,
  lineHeight: 1,
};

const tagInputWrapStyle: CSSProperties = {
  display: 'inline-flex',
};

const tagInputStyle: CSSProperties = {
  width: 90,
  border: '1px solid #d1d5db',
  borderRadius: 6,
  padding: '2px 6px',
  fontSize: 12,
};

const fileNameButtonStyle: CSSProperties = {
  background: 'transparent',
  border: 0,
  padding: 0,
  cursor: 'pointer',
  textAlign: 'left',
  color: '#2563eb',
};

const inlineInputStyle: CSSProperties = {
  width: '100%',
  border: '1px solid #d1d5db',
  borderRadius: 6,
  padding: '4px 8px',
  fontSize: 13,
};
