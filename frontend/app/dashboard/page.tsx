'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import type { CSSProperties } from 'react';

import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { deleteFiles, getFiles, searchFiles, uploadFile } from '@/features/files/api';
import { FileTable } from '@/features/files/components/FileTable';
import { useAuthGuard } from '@/hooks/useAuthGuard';
import { handleApiError } from '@/services/error-handler';
import type { FileItem, FileSort, FileTypeFilter } from '@/types/file';

const DEFAULT_LIMIT = 20;
const MIN_LOADING_TIME = 300;

export default function DashboardPage() {
  const { isCheckingAuth, isAuthorized } = useAuthGuard();
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [page, setPage] = useState(1);
  const [sort, setSort] = useState<FileSort>('date');
  const [typeFilter, setTypeFilter] = useState<FileTypeFilter>('');
  const [tagFilter, setTagFilter] = useState('');
  const [debouncedTag, setDebouncedTag] = useState('');
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');

  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [deletingBulk, setDeletingBulk] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const delay = setTimeout(() => {
      setDebouncedTag(tagFilter.trim());
    }, 500);

    return () => clearTimeout(delay);
  }, [tagFilter]);

  useEffect(() => {
    const delay = setTimeout(() => {
      setDebouncedQuery(query.trim());
    }, 500);

    return () => clearTimeout(delay);
  }, [query]);

  const hasQuery = useMemo(() => debouncedQuery.trim().length > 0, [debouncedQuery]);

  const isSearchMode = useMemo(() => {
    return Boolean(hasQuery || typeFilter || debouncedTag);
  }, [debouncedTag, hasQuery, typeFilter]);

  useEffect(() => {
    setPage(1);
  }, [debouncedQuery]);

  useEffect(() => {
    setSelectedIds([]);
  }, [page, sort, typeFilter, debouncedTag, debouncedQuery, reloadKey]);

  useEffect(() => {
    if (!isAuthorized) {
      return;
    }

    let isMounted = true;

    const fetchFiles = async () => {
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
          ...(debouncedTag && { tag: debouncedTag }),
        };

        const shouldUseSearch = isSearchMode && Boolean(hasQuery || typeFilter || debouncedTag);
        const response = shouldUseSearch ? await searchFiles(params) : await getFiles(params);
        const normalizedFiles = 'files' in response ? response.files ?? [] : response.results ?? [];

        if (!isMounted) return;
        setFiles(normalizedFiles);
      } catch (err) {
        if (!isMounted) return;
        setError(handleApiError(err));
      } finally {
        const elapsed = Date.now() - start;
        if (elapsed < MIN_LOADING_TIME) {
          await new Promise((resolve) => setTimeout(resolve, MIN_LOADING_TIME - elapsed));
        }
        if (!isMounted) return;
        setLoading(false);
      }
    };

    fetchFiles();

    return () => {
      isMounted = false;
    };
  }, [debouncedQuery, debouncedTag, hasQuery, isAuthorized, isSearchMode, page, reloadKey, sort, typeFilter]);

  const triggerRefetch = () => setReloadKey((prev) => prev + 1);

  const handleUploadClick = () => {
    if (uploading) return;
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (!selectedFile || uploading) {
      return;
    }

    setUploadError(null);
    setActionError(null);
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

    setActionError(null);
    setDeletingId(fileId);
    try {
      const result = await deleteFiles({ file_ids: [fileId] });
      if (result.failed > 0) {
        const firstError = result.errors?.[0]?.error ?? 'Delete failed for one or more files.';
        setActionError(firstError);
      }
      triggerRefetch();
    } catch (err) {
      setActionError(handleApiError(err));
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

    setActionError(null);
    setDeletingBulk(true);
    try {
      const result = await deleteFiles({ file_ids: selectedIds });
      if (result.failed > 0) {
        const firstError = result.errors?.[0]?.error ?? `Deleted ${result.deleted}, failed ${result.failed}.`;
        setActionError(firstError);
      }
      setSelectedIds([]);
      triggerRefetch();
    } catch (err) {
      setActionError(handleApiError(err));
    } finally {
      setDeletingBulk(false);
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
                value={tagFilter}
                onChange={(e) => {
                  setTagFilter(e.target.value);
                  setPage(1);
                }}
                placeholder='Filter by tag'
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
          {actionError ? <div className='text-red-500'>{actionError}</div> : null}

          {isSearchMode ? (
            <div className='text-sm text-gray-500 mb-2'>
              Filters:
              {hasQuery && ` query="${debouncedQuery}"`}
              {typeFilter && ` type=${typeFilter}`}
              {debouncedTag && ` tag=${debouncedTag}`}
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
              onSelect={handleSelect}
              onSelectAll={handleSelectAll}
              onDelete={handleDeleteSingle}
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
