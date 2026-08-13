import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/services/api";
import type { DeploymentSpecification } from "@/types/deployment";

export default function RequestsList() {
  const [requests, setRequests] = useState<DeploymentSpecification[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listRequests().then(setRequests).catch((e) => setError(String(e)));
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900">Requests</h1>
      {error && <p className="mt-4 text-red-600">{error}</p>}
      <div className="mt-4 divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
        {requests.map((r) => (
          <Link
            key={r.request_id}
            href={`/requests/${r.request_id}`}
            className="flex items-center justify-between px-4 py-3 text-sm hover:bg-slate-50"
          >
            <span className="font-medium text-slate-900">{r.request_id}</span>
            <span className="text-slate-500">
              {r.application} · {r.environment.toUpperCase()}
            </span>
          </Link>
        ))}
        {requests.length === 0 && <p className="px-4 py-6 text-sm text-slate-500">No requests yet.</p>}
      </div>
    </div>
  );
}
