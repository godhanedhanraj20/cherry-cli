import axios from 'axios';

export const handleApiError = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const apiMessage = error.response?.data?.error;
    if (typeof apiMessage === 'string' && apiMessage.trim()) {
      return apiMessage;
    }

    if (typeof error.message === 'string' && error.message.trim()) {
      return error.message;
    }
  }

  return 'Something went wrong';
};
