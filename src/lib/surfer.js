import axios from 'axios';

const service = axios.create({
    baseURL: process.env.VUE_APP_API_BASE_URL || 'http://localhost:5000/api'
});

export function generateSurferMap(file) {
    const formData = new FormData();
    formData.append('file', file);
    return service.post('/generate-surfer', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    }).then((res) => res.data);
}