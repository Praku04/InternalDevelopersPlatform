// Thin fetch wrapper for the backend API. Base URL is injected at build/run
// time via NEXT_PUBLIC_API_BASE_URL (see next.config.js / .env.example).
import type { DeploymentSpecification, ModuleMetadata, TerraformPlanResult } from "@/types/deployment";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listModules: () => apiFetch<ModuleMetadata[]>("/api/v1/modules"),
  getModule: (name: string) => apiFetch<ModuleMetadata>(`/api/v1/modules/${name}`),
  searchModules: (capabilities: string[]) =>
    apiFetch<ModuleMetadata[]>("/api/v1/modules/search", {
      method: "POST",
      body: JSON.stringify({ capabilities }),
    }),
  createRequest: (spec: DeploymentSpecification) =>
    apiFetch<DeploymentSpecification>("/api/v1/requests", {
      method: "POST",
      body: JSON.stringify(spec),
    }),
  listRequests: () => apiFetch<DeploymentSpecification[]>("/api/v1/requests"),
  getRequest: (id: string) => apiFetch<DeploymentSpecification>(`/api/v1/requests/${id}`),
  getRequestStatus: (id: string) => apiFetch<{ request_id: string; status: string }>(`/api/v1/requests/${id}/status`),
  runTerraformPlan: (requestId: string) =>
    apiFetch<TerraformPlanResult>("/api/v1/terraform/plan", {
      method: "POST",
      body: JSON.stringify({ request_id: requestId }),
    }),
  getTerraformPlan: (requestId: string) =>
    apiFetch<TerraformPlanResult>(`/api/v1/terraform/plan/${requestId}`),
};
