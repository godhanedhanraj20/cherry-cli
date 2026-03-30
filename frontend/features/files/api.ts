import { API_ROUTES } from '@/constants/api-routes';
import api from '@/services/api';
import type { GetFilesParams, GetFilesResponse } from '@/types/file';

export const getFiles = async (params: GetFilesParams) => {
  const response = await api.get<GetFilesResponse>(API_ROUTES.FILES, { params });
  return response.data;
};
