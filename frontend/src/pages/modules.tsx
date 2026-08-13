import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/services/api";
import type { ModuleMetadata } from "@/types/deployment";

export default function Modules() {
  const [modules, setModules] = useState<ModuleMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");

  useEffect(() => {
    const fetchModules = async () => {
      try {
        const data = await api.listModules();
        setModules(data);
        setLoading(false);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
        setLoading(false);
      }
    };
    fetchModules();
  }, []);

  const categories = ["all", ...new Set(modules.map((m) => m.category))];

  const filteredModules = modules.filter((m) => {
    const matchesSearch =
      m.module_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.capabilities.some((c) => c.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesCategory = selectedCategory === "all" || m.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const getModuleIcon = (category: string) => {
    const icons: Record<string, string> = {
      networking: "M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9",
      compute: "M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z",
      storage: "M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4",
      security: "M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z",
      loadbalancer: "M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4",
    };
    return icons[category] || icons.compute;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
          <p className="mt-2 text-sm text-slate-600">Loading modules...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900">Module Catalog</h1>
        <p className="mt-2 text-slate-600">
          Browse {modules.length} approved Terraform modules ready for deployment
        </p>
      </div>

      {/* Filters */}
      <div className="mb-6 space-y-4 rounded-lg border border-slate-200 bg-white p-4">
        <div className="flex gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search modules, capabilities..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="rounded-md border border-slate-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat === "all" ? "All Categories" : cat.charAt(0).toUpperCase() + cat.slice(1)}
              </option>
            ))}
          </select>
        </div>
        {searchTerm && (
          <p className="text-sm text-slate-600">
            Found {filteredModules.length} module{filteredModules.length !== 1 ? "s" : ""}
          </p>
        )}
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-800">⚠️ {error}</p>
        </div>
      )}

      {/* Modules Grid */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {filteredModules.map((m) => (
          <div key={m.module_name} className="group rounded-lg border border-slate-200 bg-white p-6 shadow-sm transition hover:border-blue-300 hover:shadow-md">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-blue-100 p-2">
                  <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={getModuleIcon(m.category)} />
                  </svg>
                </div>
                <div>
                  <h2 className="font-semibold text-slate-900">{m.module_name}</h2>
                  <p className="text-xs text-slate-500">v{m.version}</p>
                </div>
              </div>
              <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
                {m.status}
              </span>
            </div>

            <p className="mt-3 text-sm text-slate-600">{m.description}</p>

            <div className="mt-4">
              <div className="text-xs font-medium text-slate-700">Capabilities:</div>
              <div className="mt-1 flex flex-wrap gap-1">
                {m.capabilities.map((c) => (
                  <span key={c} className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-700">
                    {c}
                  </span>
                ))}
              </div>
            </div>

            <div className="mt-4 flex items-center justify-between text-xs text-slate-500">
              <span className="rounded bg-slate-100 px-2 py-0.5">{m.category}</span>
              <span>Provider: {m.provider}</span>
            </div>

            <div className="mt-4 pt-4 border-t border-slate-100">
              <Link
                href={`/new-request?module=${m.module_name}`}
                className="block w-full rounded-md bg-blue-600 px-4 py-2 text-center text-sm font-medium text-white transition hover:bg-blue-700"
              >
                Use This Module
              </Link>
            </div>
          </div>
        ))}
      </div>

      {filteredModules.length === 0 && (
        <div className="rounded-lg border border-slate-200 bg-white p-12 text-center">
          <svg
            className="mx-auto h-12 w-12 text-slate-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-slate-900">No modules found</h3>
          <p className="mt-2 text-sm text-slate-600">Try adjusting your search or filters</p>
        </div>
      )}
    </div>
  );
}
