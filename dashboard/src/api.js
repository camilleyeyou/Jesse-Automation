const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001';
const API_KEY = import.meta.env.VITE_API_KEY || '';

function authHeaders(extra = {}) {
  const headers = { ...extra };
  if (API_KEY) {
    headers['X-API-Key'] = API_KEY;
  }
  return headers;
}

const api = {
  async get(endpoint) {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      headers: authHeaders(),
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
  },
  async post(endpoint, data = {}) {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
  },
  async patch(endpoint, data = {}) {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: 'PATCH',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
  },
  async delete(endpoint) {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: 'DELETE',
      headers: authHeaders(),
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
  },
};

export { API_BASE, api };
