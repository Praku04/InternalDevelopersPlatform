import { useEffect, useState } from "react";
import { api } from "@/services/api";
import type { ModuleMetadata } from "@/types/deployment";

export default function Modules() {
  const [modules, setModules] = useState<ModuleMetadata[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listModules().then(setModules).catch((e) => setError(String(e)));
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900">Approved Terraform Modules</h1>
      {error && <p className="mt-4 text-red-600">{error}</p>}
      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {modules.map((m) => (
          <div key={m.module_name} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-slate-900">{m.module_name}</h2>
              <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
                {m.status}
              </span>
            </div>
            <p className="mt-1 text-sm text-slate-500">v{m.version} · {m.category}</p>
            <p className="mt-2 text-sm text-slate-600">{m.description}</p>
            <div className="mt-3 flex flex-wrap gap-1">
              {m.capabilities.map((c) => (
                <span key={c} className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-700">
                  {c}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
