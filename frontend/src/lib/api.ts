import axios from 'axios';

const API_URL = 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
});

export const uploadResume = async (file: File, userId: string) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('user_id', userId); // <--- Send User ID

  const response = await api.post('/upload-resume', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const generateResume = async (jobDescription: string, userId: string) => {
  const response = await api.post('/generate-resume', {
    job_description: jobDescription,
    user_id: userId // <--- Send User ID
  });
  return response.data;
};