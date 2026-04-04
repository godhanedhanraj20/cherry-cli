'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import type { CSSProperties } from 'react';

import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { deleteFiles, getFiles, renameFile, searchFiles, updateFileTag, uploadFile } from '@/features/files/api';
import { FileTable } from '@/features/files/components/FileTable';
import { useAuthGuard } from '@/hooks/useAuthGuard';
import { handleApiError } from '@/services/error-handler';
import type { FileItem, FileSort, FileTypeFilter } from '@/types/file';

const DEFAULT_LIMIT = 20;
const MIN_LOADING_TIME = 300;

export default function DashboardPage() {
  const { isCheckingAuth, isAuthorized } = useAuthGuard();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const currentRequestIdRef = useRef(0);

  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [page, setPage] = useState(1);
  const [sort, setSort] = useState<FileSort>('date');
  const [typeFilter, setTypeFilter] = useState<FileTypeFilter>('');
  const [tagInput, setTagInput] = useState('');
  const [tagFilters, setTagFilters] = useState<string[]>([]);
  const [debouncedTagFilters, setDebouncedTagFilters] = useState<string[]>([]);
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');

  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [deletingBulk, setDeletingBulk] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [tagError, setTagError] = useState<string | null>(null);
  const [renameError, setRenameError] = useState<string | null>(null);
  const [taggingId, setTaggingId] = useState<number | null>(null);
  const [renamingId, setRenamingId] = useState<number | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const normalizeTag = (tag: string) => tag.trim().toLowerCase();

  useEffect(() => {
    const delay = setTimeout(() => {
      const parsed = tagInput
        .split(',')
        .map((tag) => normalizeTag(tag))
        .filter(Boolean);
      setTagFilters(Array.from(new Set(parsed)));
    }, 500);

    return () => clearTimeout(delay);
  }, [tagInput]);

  useEffect(() => {
    setDebouncedTagFilters(tagFilters);
  }, [tagFilters]);

  useEffect(() => {
    const delay = setTimeout(() => {
      setDebouncedQuery(query.trim());
    }, 500);

    return () => clearTimeout(delay);
  }, [query]);

  const hasQuery = useMemo(() => debouncedQuery.trim().length > 0, [debouncedQuery]);

  const isSearchMode = useMemo(() => {
    return Boolean(hasQuery || typeFilter || debouncedTagFilters.length > 0);
  }, [debouncedTagFilters.length, hasQuery, typeFilter]);

  useEffect(() => {
    setPage(1);
  }, [debouncedQuery]);

  useEffect(() => {
    setSelectedIds([]);
  }, [page, sort, typeFilter, debouncedTagFilters, debouncedQuery]);

  useEffect(() => {
    if (!isAuthorized) {
      return;
    }

    let isMounted = true;

    const fetchFiles = async () => {
      const requestId = ++currentRequestIdRef.current;
      const start = Date.now();
      setLoading(true);
      setError(null);
      try {
        const params = {
          page,
          limit: DEFAULT_LIMIT,
          sort,
          ...(hasQuery && { query: debouncedQuery }),
          ...(typeFilter && { type: typeFilter }),
          ...(debouncedTagFilters.length > 0 && { tag: debouncedTagFilters.join(',') }),
        };

        const shouldUseSearch = isSearchMode && Boolean(hasQuery || typeFilter || debouncedTagFilters.length > 0);
        const response = shouldUseSearch ? await searchFiles(params) : await getFiles(params);
        const normalizedFiles = 'files' in response ? response.files ?? [] : response.results ?? [];

        if (!isMounted) return;
        if (requestId !== currentRequestIdRef.current) return;
        setFiles(normalizedFiles);
      } catch (err) {
        if (!isMounted) return;
        if (requestId !== currentRequestIdRef.current) return;
        setError(handleApiError(err));
      } finally {
        const elapsed = Date.now() - start;
        if (elapsed < MIN_LOADING_TIME) {
          await new Promise((resolve) => setTimeout(resolve, MIN_LOADING_TIME - elapsed));
        }
        if (!isMounted) return;
        if (requestId !== currentRequestIdRef.current) return;
        setLoading(false);
      }
    };

    fetchFiles();

    return () => {
      isMounted = false;
    };
  }, [debouncedQuery, debouncedTagFilters, hasQuery, isAuthorized, isSearchMode, page, reloadKey, sort, typeFilter]);

  const triggerRefetch = () => setReloadKey((prev) => prev + 1);

  const handleUploadClick = () => {
    if (uploading) return;
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = event.target.files;
    if (!selectedFiles || selectedFiles.length === 0 || uploading) {
      return;
    }
    if (selectedFiles.length > 1) {
      setUploadError('Only one file allowed');
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      return;
    }
    const selectedFile = selectedFiles[0];

    setUploadError(null);
    setDeleteError(null);
    setTagError(null);
    setRenameError(null);
    setUploading(true);
    try {
      await uploadFile(selectedFile);
      triggerRefetch();
    } catch (err) {
      setUploadError(handleApiError(err));
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDeleteSingle = async (fileId: number) => {
    if (deletingId !== null || deletingBulk) return;

    const confirmed = window.confirm(`Delete file ${fileId}?`);
    if (!confirmed) return;

    setDeleteError(null);
    setTagError(null);
    setRenameError(null);
    setDeletingId(fileId);
    try {
      setFiles((prev) => prev.filter((file) => file.id !== fileId));
      const result = await deleteFiles({ file_ids: [fileId] });
      if (result.failed > 0) {
        const detail = result.errors?.map((item) => `[${item.file_id}] ${item.error}`).join('; ');
        setDeleteError(`Deleted: ${result.deleted}, Failed: ${result.failed}${detail ? ` (${detail})` : ''}`);
      } else {
        setDeleteError(null);
      }
      setSelectedIds([]);
      triggerRefetch();
    } catch (err) {
      setDeleteError(handleApiError(err));
    } finally {
      setDeletingId(null);
    }
  };

  const handleSelect = (fileId: number, selected: boolean) => {
    setSelectedIds((prev) => {
      if (selected) {
        if (prev.includes(fileId)) return prev;
        return [...prev, fileId];
      }
      return prev.filter((id) => id !== fileId);
    });
  };

  const handleSelectAll = (selected: boolean) => {
    if (!selected) {
      setSelectedIds([]);
      return;
    }
    setSelectedIds(files.map((file) => file.id));
  };

  const handleDeleteSelected = async () => {
    if (selectedIds.length === 0 || deletingBulk || deletingId !== null) return;

    const confirmed = window.confirm(`Delete ${selectedIds.length} selected file(s)?`);
    if (!confirmed) return;

    setDeleteError(null);
    setTagError(null);
    setRenameError(null);
    setDeletingBulk(true);
    try {
      setFiles((prev) => prev.filter((file) => !selectedIds.includes(file.id)));
      const result = await deleteFiles({ file_ids: selectedIds });
      if (result.failed > 0) {
        const detail = result.errors?.map((item) => `[${item.file_id}] ${item.error}`).join('; ');
        setDeleteError(`Deleted: ${result.deleted}, Failed: ${result.failed}${detail ? ` (${detail})` : ''}`);
      } else {
        setDeleteError(null);
      }
      setSelectedIds([]);
      triggerRefetch();
    } catch (err) {
      setDeleteError(handleApiError(err));
    } finally {
      setDeletingBulk(false);
    }
  };

  const parseFileTags = (tagString: string) =>
    tagString
      .split(',')
      .map((tag) => normalizeTag(tag))
      .filter(Boolean);

  const handleTagClick = (tag: string) => {
    const trimmed = normalizeTag(tag);
    if (!trimmed) return;
    setTagFilters((prev) => {
      if (prev.includes(trimmed)) {
        return prev.filter((item) => item !== trimmed);
      }
      return [...prev, trimmed];
    });
    setTagInput((prev) => {
      const parsed = prev
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean);
      if (parsed.includes(trimmed)) {
        return parsed.filter((item) => item !== trimmed).join(', ');
      }
      return [...parsed, trimmed].join(', ');
    });
    setPage(1);
  };

  const handleAddTag = async (fileId: number, rawTag: string) => {
    setTagError(null);
    setRenameError(null);
    const nextTag = normalizeTag(rawTag);
    if (!nextTag) {
      setTagError('Tag cannot be empty');
      return;
    }
    const target = files.find((file) => file.id === fileId);
    if (!target) return;
    const existingTags = parseFileTags(target.tags);
    if (existingTags.includes(nextTag)) {
      setTagError(`Tag "${nextTag}" already exists`);
      return;
    }

    setTaggingId(fileId);
    try {
      await updateFileTag({ file_id: fileId, tag: nextTag });
      setFiles((prev) =>
        prev.map((file) =>
          file.id === fileId
            ? {
                ...file,
                tags: [...parseFileTags(file.tags), nextTag].join(', '),
              }
            : file,
        ),
      );
    } catch (err) {
      setTagError(handleApiError(err));
      triggerRefetch();
    } finally {
      setTaggingId(null);
    }
  };

  const handleRemoveTag = async (fileId: number, tag: string) => {
    setTagError(null);
    setRenameError(null);
    const normalizedTag = normalizeTag(tag);
    if (!normalizedTag) return;
    setTaggingId(fileId);
    try {
      await updateFileTag({ file_id: fileId, tag: normalizedTag, action: 'remove' });
      setFiles((prev) =>
        prev.map((file) =>
          file.id === fileId
            ? {
                ...file,
                tags: parseFileTags(file.tags)
                  .filter((item) => item !== normalizedTag)
                  .join(', '),
              }
            : file,
        ),
      );
    } catch (err) {
      setTagError(handleApiError(err));
      triggerRefetch();
    } finally {
      setTaggingId(null);
    }
  };

  const handleRename = async (fileId: number, newName: string) => {
    setTagError(null);
    setRenameError(null);
    const trimmed = newName.trim();
    if (!trimmed) {
      setRenameError('Name cannot be empty');
      return;
    }
    const target = files.find((file) => file.id === fileId);
    if (!target) return;

    const oldExt = target.name.includes('.') ? target.name.split('.').pop() ?? '' : '';
    const candidateName = oldExt && !trimmed.includes('.') ? `${trimmed}.${oldExt}` : trimmed;
    const newExt = candidateName.includes('.') ? candidateName.split('.').pop() ?? '' : '';
    if (oldExt && oldExt !== newExt) {
      setRenameError(`File extension must remain .${oldExt}`);
      return;
    }

    setRenamingId(fileId);
    try {
      await renameFile({ file_id: fileId, new_name: candidateName });
      setFiles((prev) => prev.map((file) => (file.id === fileId ? { ...file, name: candidateName } : file)));
    } catch (err) {
      setRenameError(handleApiError(err));
      triggerRefetch();
    } finally {
      setRenamingId(null);
    }
  };

  if (isCheckingAuth) {
    return (
      <main style={{ minHeight: '100vh', display: 'grid', placeItems: 'center' }}>
        <p>Checking session...</p>
      </main>
    );
  }

  if (!isAuthorized) {
    return null;
  }

  return (
    <main style={{ display: 'grid', gridTemplateColumns: '220px 1fr', minHeight: '100vh' }}>
      <aside style={{ borderRight: '1px solid #e5e7eb', padding: 16 }}>
        <h2 style={{ marginTop: 0 }}>Menu</h2>
        <nav style={{ display: 'grid', gap: 8 }}>
          <div style={menuItemStyle}>Dashboard</div>
          <div style={menuItemStyle}>Search (placeholder)</div>
        </nav>
      </aside>

      <section style={{ display: 'grid', gridTemplateRows: '64px 1fr' }}>
        <header
          style={{
            borderBottom: '1px solid #e5e7eb',
            display: 'grid',
            gridTemplateColumns: '140px 1fr auto auto',
            alignItems: 'center',
            gap: 12,
            padding: '0 16px',
          }}
        >
          <h1 style={{ margin: 0, fontSize: 20 }}>Dashboard</h1>
          <Input
            type='text'
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setPage(1);
            }}
            placeholder='Search by name...'
          />
          <Button
            onClick={() => {
              setQuery('');
              setPage(1);
            }}
            disabled={loading || query.length === 0}
            style={{ width: 56 }}
          >
            ×
          </Button>
          <Button onClick={handleUploadClick} disabled={uploading || deletingBulk || deletingId !== null} style={{ width: 120 }}>
            {uploading ? 'Uploading...' : 'Upload'}
          </Button>
          <input ref={fileInputRef} type='file' onChange={handleFileChange} style={{ display: 'none' }} />
        </header>

        <div style={{ padding: 16, display: 'grid', gap: 16 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 12 }}>
            <label style={fieldStyle}>
              <span>Sort</span>
              <select
                value={sort}
                onChange={(e) => {
                  setSort(e.target.value as FileSort);
                  setPage(1);
                }}
                style={selectStyle}
              >
                <option value='date'>date</option>
                <option value='name'>name</option>
                <option value='size'>size</option>
              </select>
            </label>

            <label style={fieldStyle}>
              <span>Type</span>
              <select
                value={typeFilter}
                onChange={(e) => {
                  setTypeFilter(e.target.value as FileTypeFilter);
                  setPage(1);
                }}
                style={selectStyle}
              >
                <option value=''>all</option>
                <option value='video'>video</option>
                <option value='image'>image</option>
                <option value='document'>document</option>
                <option value='audio'>audio</option>
              </select>
            </label>

            <label style={fieldStyle}>
              <span>Tag</span>
              <Input
                type='text'
                value={tagInput}
                onChange={(e) => {
                  setTagInput(e.target.value);
                  setPage(1);
                }}
                placeholder='Filter by tags (comma-separated)'
              />
            </label>

            <div style={{ display: 'grid', alignContent: 'end' }}>
              <Button onClick={() => setPage(1)} disabled={loading || uploading || deletingBulk || deletingId !== null}>
                Reset Page
              </Button>
            </div>
          </div>

          {error ? <div className='text-red-500 mb-2'>{error}</div> : null}
          {uploadError ? <div className='text-red-500'>{uploadError}</div> : null}
          {deleteError ? <div className='text-red-500'>{deleteError}</div> : null}
          {tagError ? <div className='text-red-500'>{tagError}</div> : null}
          {renameError ? <div className='text-red-500'>{renameError}</div> : null}

          {isSearchMode ? (
            <div className='text-sm text-gray-500 mb-2'>
              Filters:
              {hasQuery && ` query="${debouncedQuery}"`}
              {typeFilter && ` type=${typeFilter}`}
              {debouncedTagFilters.length > 0 && ` tag=${debouncedTagFilters.join(',')}`}
            </div>
          ) : null}

          {selectedIds.length > 0 ? (
            <div>
              <Button
                onClick={handleDeleteSelected}
                disabled={deletingBulk || uploading || deletingId !== null}
                style={{ width: 180 }}
              >
                {deletingBulk ? 'Deleting selected...' : `Delete Selected (${selectedIds.length})`}
              </Button>
            </div>
          ) : null}

          {loading ? (
            <p>Loading files...</p>
          ) : (
            <FileTable
              files={files}
              emptyMessage={isSearchMode ? 'No results found' : 'No files found'}
              selectedIds={selectedIds}
              deletingId={deletingId}
              taggingId={taggingId}
              renamingId={renamingId}
              activeTagFilters={tagFilters}
              onSelect={handleSelect}
              onSelectAll={handleSelectAll}
              onDelete={handleDeleteSingle}
              onTagClick={handleTagClick}
              onAddTag={handleAddTag}
              onRemoveTag={handleRemoveTag}
              onRename={handleRename}
            />
          )}

          <div style={{ display: 'flex', gap: 8 }}>
            <Button
              onClick={() => setPage((prev) => Math.max(1, prev - 1))}
              disabled={loading || page === 1 || uploading || deletingBulk || deletingId !== null}
              style={{ width: 140 }}
            >
              Previous page
            </Button>
            <Button
              onClick={() => setPage((prev) => prev + 1)}
              disabled={loading || uploading || deletingBulk || deletingId !== null}
              style={{ width: 140 }}
            >
              Next page
            </Button>
            <div style={{ display: 'flex', alignItems: 'center', fontSize: 14 }}>Page: {page}</div>
          </div>
        </div>
      </section>
    </main>
  );
}

const menuItemStyle: CSSProperties = {
  padding: '8px 10px',
  borderRadius: 6,
  background: '#f9fafb',
};

const fieldStyle: CSSProperties = {
  display: 'grid',
  gap: 6,
  fontSize: 13,
};

const selectStyle: CSSProperties = {
  width: '100%',
  padding: '10px 12px',
  borderRadius: 8,
  border: '1px solid #d1d5db',
  fontSize: 14,
  background: '#fff',
};
