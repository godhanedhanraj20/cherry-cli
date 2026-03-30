'use client';

import { useEffect, useState } from 'react';
import type { CSSProperties } from 'react';

import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { getFiles } from '@/features/files/api';
import { FileTable } from '@/features/files/components/FileTable';
import { useAuthGuard } from '@/hooks/useAuthGuard';
import { handleApiError } from '@/services/error-handler';
import type { FileItem, FileSort, FileTypeFilter } from '@/types/file';

const DEFAULT_LIMIT = 20;

export default function DashboardPage() {
  const { isCheckingAuth, isAuthorized } = useAuthGuard();

  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [page, setPage] = useState(1);
  const [limit] = useState(DEFAULT_LIMIT);
  const [sort, setSort] = useState<FileSort>('date');
  const [typeFilter, setTypeFilter] = useState<FileTypeFilter>('');
  const [tagFilter, setTagFilter] = useState('');
  const [debouncedTag, setDebouncedTag] = useState('');

  useEffect(() => {
    const delay = setTimeout(() => {
      setDebouncedTag(tagFilter.trim());
    }, 500);

    return () => clearTimeout(delay);
  }, [tagFilter]);

  useEffect(() => {
    if (!isAuthorized) {
      return;
    }

    let isMounted = true;

    const fetchFiles = async () => {
      setLoading(true);
      setError(null);
      try {
        const params = {
          page,
          limit,
          sort,
          ...(typeFilter && { type: typeFilter }),
          ...(debouncedTag && { tag: debouncedTag }),
        };

        const response = await getFiles(params);

        if (!isMounted) return;
        setFiles(response.files);
      } catch (err) {
        if (!isMounted) return;
        setError(handleApiError(err));
      } finally {
        if (!isMounted) return;
        setLoading(false);
      }
    };

    fetchFiles();

    return () => {
      isMounted = false;
    };
  }, [debouncedTag, isAuthorized, limit, page, sort, typeFilter]);

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
        <header style={{ borderBottom: '1px solid #e5e7eb', display: 'flex', alignItems: 'center', padding: '0 16px' }}>
          <h1 style={{ margin: 0, fontSize: 20 }}>Dashboard</h1>
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
              <Button onClick={() => setPage(1)} disabled={loading}>
                Reset Page
              </Button>
            </div>
          </div>

          {error ? <div className='text-red-500 mb-2'>{error}</div> : null}

          {loading ? <p>Loading files...</p> : <FileTable files={files} />}

          <div style={{ display: 'flex', gap: 8 }}>
            <Button
              onClick={() => setPage((prev) => Math.max(1, prev - 1))}
              disabled={loading || page === 1}
              style={{ width: 140 }}
            >
              Previous page
            </Button>
            <Button onClick={() => setPage((prev) => prev + 1)} disabled={loading} style={{ width: 140 }}>
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
