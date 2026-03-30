export type FileSort = 'date' | 'name' | 'size';
export type FileTypeFilter = 'video' | 'image' | 'document' | 'audio' | '';

export interface FileItem {
  id: number;
  name: string;
  size: string;
  date: string;
  tags: string;
  raw_size?: number;
  caption?: string;
}

export interface GetFilesParams {
  page?: number;
  limit?: number;
  sort?: FileSort;
  query?: string;
  type?: Exclude<FileTypeFilter, ''>;
  tag?: string;
}

export interface GetFilesResponse {
  files: FileItem[];
}

export interface SearchFilesResponse {
  results: FileItem[];
}
