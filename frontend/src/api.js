const API_BASE = 'http://localhost:8000';

export async function fetchURLs() {
  const res = await fetch(`${API_BASE}/urls`);
  if (!res.ok) throw new Error('Failed to fetch URLs');
  return res.json();
}

export async function addURL(url, name) {
  const res = await fetch(`${API_BASE}/urls`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, name }),
  });
  if (!res.ok) throw new Error('Failed to add URL');
  return res.json();
}

export async function deleteURL(id) {
  const res = await fetch(`${API_BASE}/urls/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete URL');
  return res.json();
}
