import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import Link from "next/link";
import { api } from "@/services/api";
import type { DeploymentSpecification } from "@/types/deployment";

export default function Requests() {
  const router = useRouter();
  const [requests, setRequests] = useState<DeploymentSpecification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);

  useEffect(() => {
    if (router.query.success === "true") {
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 5000);
    }
  }, [router.query]);

  useEffect(() => {
    const fetchRequests = async () => {
      try {
        const data = await api.listRequests();
        setRequests(data.sort((a, b) => b.request_id.localeCompare(a.request_id)));
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load requests");
        setLoading(false);
      }
    };
    fetchRequests();
  }, []);

  const getEnvironmentColor = (env: string) => {
    const colors = {
      dev: "bg-green-100 text-green-800",
      uat: "bg-yellow-100 text-yellow-800",
      prod: "bg-red-100 text-red-800",
    };
    return colors[env as keyof typeof colors] || "bg-slate-100 text-slate-800";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
          <p className="mt-2 text-sm text-slate-600">Loading requests...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">My Requests</h1>
          <p className="mt-2 text-slate-600">Track your infrastructure deployment requests</p>
        </div>
        <Link
          href="/new-request"
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          + New Request
        </Link>
      </div>

      {showSuccess && (
        <div className="mb-6 rounded-lg border border-green-200 bg-green-50 p-4">
          <p className="text-sm text-green-800">
            ✅ Request created successfully! ID: {router.query.id}
          </p>
        </div>
      )}

      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-800">⚠️ {error}</p>
        </div>
      )}

      {requests.length === 0 ? (
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
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-slate-900">No requests yet</h3>
          <p className="mt-2 text-sm text-slate-600">Create your first infrastructure deployment request</p>
          <Link
            href="/new-request"
            className="mt-4 inline-block rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Create Request
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {requests.map((request) => (
            <div key={request.request_id} className="rounded-lg border border-slate-200 bg-white p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="text-lg font-semibold text-slate-900">{request.request_id}</h3>
                    <span
                      className={`rounded-full px-2 py-1 text-xs font-medium ${getEnvironmentColor(request.environment)}`}
                    >
                      {request.environment.toUpperCase()}
                    </span>
                  </div>
                  <div className="mt-2 flex gap-6 text-sm text-slate-600">
                    <div>
                      <span className="font-medium">Application:</span> {request.application}
                    </div>
                    <div>
                      <span className="font-medium">Region:</span> {request.region}
                    </div>
                    <div>
                      <span className="font-medium">Source:</span> {request.source}
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-4">
                <h4 className="text-sm font-medium text-slate-700">Resources:</h4>
                <div className="mt-2 space-y-2">
                  {request.resources.map((resource, idx) => (
                    <div key={idx} className="flex items-center gap-2 rounded-md bg-slate-50 px-3 py-2 text-sm">
                      <span className="rounded bg-slate-200 px-2 py-0.5 text-xs font-medium text-slate-700">
                        {resource.type}
                      </span>
                      <span className="text-slate-600">
                        {resource.module} v{resource.version}
                      </span>
                      <span className="text-slate-400">•</span>
                      <span className="text-slate-600">{resource.action}</span>
                    </div>
                  ))}
                </div>
              </div>

              {request.ai_analysis && (
                <div className="mt-4 rounded-md border border-blue-100 bg-blue-50 p-3">
                  <div className="text-xs font-medium text-blue-900">AI Analysis</div>
                  <div className="mt-1 text-sm text-blue-700">
                    Risk: {request.ai_analysis.deployment_risk} | Cost: ${request.ai_analysis.estimated_cost}/month
                  </div>
                </div>
              )}

              <div className="mt-4 flex gap-2">
                <button className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50">
                  View Details
                </button>
                <button className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50">
                  View Logs
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
