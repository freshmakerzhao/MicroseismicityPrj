import axios from 'axios';

const service = axios.create({
    baseURL: process.env.VUE_APP_API_BASE_URL || 'http://localhost:5000/api'
});

export function getGlobalConfig() {
    return service.get('/config').then((res) => res.data);
}

export function updateGlobalConfig(payload) {
    return service.put('/config', payload).then((res) => res.data);
}

export function pickDirectory(title, initialPath = '') {
    return service.post('/config/pick-directory', {
        title,
        initial_path: initialPath,
    }).then((res) => res.data);
}

export function pickFile(title, initialPath = '', fileTypes = [['All Files', '*.*']]) {
    return service.post('/config/pick-file', {
        title,
        initial_path: initialPath,
        file_types: fileTypes,
    }).then((res) => res.data);
}
