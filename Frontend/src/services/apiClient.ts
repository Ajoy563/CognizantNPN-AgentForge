import { getAuth } from 'firebase/auth';

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api').replace(/\/$/, '');

async function authenticatedFetch(path: string, init: RequestInit = {}) {
  const user = getAuth().currentUser;
  if (!user) throw new Error('Please sign in again.');
  const token = await user.getIdToken();
  const headers = new Headers(init.headers);
  headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch(`${BASE_URL}${path}`, { ...init, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.error?.message || body?.detail || `Request failed (${response.status})`);
  }
  return response;
}

export type GenerateRequest = {
  business_idea: string; tech_preference: 'opensource' | 'enterprise';
  cloud_preference: 'aws' | 'azure' | 'gcp' | 'none'; expected_daily_traffic: number;
  delivery_timeline_months: number; country: string;
};

export async function generateBlueprintAPI(requestData: GenerateRequest) {
  return (await authenticatedFetch('/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(requestData) })).json();
}
export async function getProjectsAPI() { return (await authenticatedFetch('/projects')).json(); }
export async function getProjectDetailAPI(projectId: string) { return (await authenticatedFetch(`/projects/${projectId}`)).json(); }
export async function getGenerationDetailAPI(generationId: string) { return (await authenticatedFetch(`/generations/${generationId}`)).json(); }
export async function getUserProfileAPI() { return (await authenticatedFetch('/users/me')).json(); }
export async function updateUserProfileAPI(name: string, photo_url = '') {
  return (await authenticatedFetch('/users/me', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, photo_url }) })).json();
}
export async function downloadReport(generationId: string, kind: 'report' | 'pdf') {
  const response = await authenticatedFetch(`/generations/${generationId}/${kind}`);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url; link.download = `solutionforge-${generationId}.${kind === 'pdf' ? 'pdf' : 'html'}`;
  document.body.appendChild(link); link.click(); link.remove(); URL.revokeObjectURL(url);
}
