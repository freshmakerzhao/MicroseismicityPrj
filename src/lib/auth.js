import axios from 'axios';

const TOKEN_KEY = 'rockburst_auth_token';
const USER_KEY = 'rockburst_auth_user';

const service = axios.create({
    baseURL: process.env.VUE_APP_API_BASE_URL || 'http://localhost:5000/api'
});

function authHeaders() {
    const token = getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
}

export function getToken() {
    return localStorage.getItem(TOKEN_KEY) || '';
}

export function getCurrentUser() {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    try {
        return JSON.parse(raw);
    } catch (e) {
        return null;
    }
}

export function isLoggedIn() {
    return !!getToken() && !!getCurrentUser();
}

export function isAdmin() {
    const user = getCurrentUser();
    return user && user.role === 'admin';
}

export function saveSession(token, user) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
}

export function login(payload) {
    return service.post('/auth/login', payload).then((res) => {
        saveSession(res.data.token, res.data.user);
        return res.data;
    });
}

export function register(payload) {
    return service.post('/auth/register', payload).then((res) => res.data);
}

export function logout() {
    return service.post('/auth/logout', {}, { headers: authHeaders() })
        .catch(() => null)
        .finally(() => clearSession());
}

export function fetchMe() {
    return service.get('/auth/me', { headers: authHeaders() }).then((res) => {
        localStorage.setItem(USER_KEY, JSON.stringify(res.data.user));
        return res.data;
    });
}

export function fetchUsers() {
    return service.get('/users', { headers: authHeaders() }).then((res) => res.data);
}

export function updateUser(id, payload) {
    return service.put(`/users/${id}`, payload, { headers: authHeaders() }).then((res) => res.data);
}

export function deleteUser(id) {
    return service.delete(`/users/${id}`, { headers: authHeaders() }).then((res) => res.data);
}
