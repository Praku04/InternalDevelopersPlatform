import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { api } from "@/services/api";
import type { DeploymentSpecification, TerraformPlanResult } from "@/types/deployment";

const statusColor: Record<string, string> = {
  PASS: "bg-green-100 text-green-800",
  FAIL: "bg-red-100 text-red-800",
  SKIPPED: "bg-slate-100 text-slate-700",
};

export default function RequestDetail() {
  const router = useRouter();
  const { id } = router.query;
  const requestId = typeof id === "string" ? id : undefined;

  const [spec, setSpec] = useState<DeploymentSpecification | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [plan, setPlan] = useState<TerraformPlanResult | null>(null);
  const [planning, setPlanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!requestId) return;
    api.getRequest(requestId).then(setSpec).catch((e) => setError(String(e)));
    api.getRequestStatus(requestId).then((s) => setStatus(s.status)).catch(() => {});
  }, [requestId]);

  async function handlePlan() {
    if (!requestId) return;
    setPlanning(true);
    setError(null);
    try {
      const result = await api.runTerraformPlan(requestId);
      setPlan(result);
      const s = await api.getRequestStatus(requestId);
      setStatus(s.status);
    } catch (err) {
      setError(String(err));
    } finally {
      setPlanning(false);
    }
  }

  if (!spec) {
    return <p className="text-slate-600">{error ?? "Loading..."}</p>;
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-slate-900">{spec.request_id}</h1>
      <p className="mt-1 text-sm text-slate-600">
        {spec.application} · {spec.environment.toUpperCase()} · {spec.region} · {spec.source}
      </p>
      {status && (
        <span className="mt-2 inline-block rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
          {status}
        </span>
      )}

      <div className="mt-6 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="font-semibold text-slate-900">Resources</h2>
        <ul className="mt-2 space-y-1 text-sm text-slate-700">
          {spec.resources.map((r, i) => (
            <li key={i}>
              {r.type} — module <code>{r.module}</code> v{r.version} ({r.action})
            </li>
          ))}
        </ul>
      </div>

      <button
        onClick={handlePlan}
        disabled={planning}
        className="mt-6 rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
      >
        {planning ? "Running Terraform Plan..." : "Generate & Validate Terraform"}
      </button>

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

      {plan && (
        <div className="mt-6 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-slate-900">Terraform Plan Result</h2>
            <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusColor[plan.overall_status]}`}>
              {plan.overall_status}
            </span>
          </div>
          <ul className="mt-3 space-y-2 text-sm">
            {plan.steps.map((step, i) => (
              <li key={i} className="rounded border border-slate-100 p-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs text-slate-600">terraform {step.step}</span>
                  <span className={`rounded px-2 py-0.5 text-xs ${statusColor[step.status]}`}>{step.status}</span>
                </div>
                {step.detail && (
                  <pre className="mt-1 max-h-32 overflow-auto whitespace-pre-wrap text-xs text-slate-500">
                    {step.detail}
                  </pre>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
