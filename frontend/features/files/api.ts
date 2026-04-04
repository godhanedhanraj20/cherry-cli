import { API_ROUTES } from '@/constants/api-routes';
import api from '@/services/api';
import type {
  DeleteFilesRequest,
  DeleteFilesResponse,
  GetFilesParams,
  GetFilesResponse,
  RenameFileRequest,
  SearchFilesResponse,
  UpdateTagRequest,
  UploadFileResponse,
} from '@/types/file';

export const getFiles = async (params: GetFilesParams) => {
  const response = await api.get<GetFilesResponse>(API_ROUTES.FILES, { params });
  return response.data;
};

export const searchFiles = async (params: GetFilesParams) => {
  const response = await api.get<SearchFilesResponse>(API_ROUTES.FILES_SEARCH, { params });
  return response.data;
};

export const uploadFile = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post<UploadFileResponse>(`${API_ROUTES.FILES}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

export const deleteFiles = async (payload: DeleteFilesRequest) => {
  const response = await api.delete<DeleteFilesResponse>(API_ROUTES.FILES, { data: payload });
  return response.data;
};

export const updateFileTag = async (payload: UpdateTagRequest) => {
  const response = await api.post(`${API_ROUTES.FILES}/tag`, payload);
  return response.data;
};

export const renameFile = async (payload: RenameFileRequest) => {
  const response = await api.post(`${API_ROUTES.FILES}/rename`, payload);
  return response.data;
};
