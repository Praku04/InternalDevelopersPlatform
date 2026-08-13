import { useState, useEffect } from "react";
import Link from "next/link";
import { api } from "@/services/api";

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalModules: 0,
    totalRequests: 0,
    loading: true,
    error: null as string | null,
  });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [modules, requests] = await Promise.all([
          api.listModules(),
          api.listRequests().catch(() => []), // Graceful fallback
        ]);
        setStats({
          totalModules: modules.length,
          totalRequests: requests.length,
          loading: false,
          error: null,
        });
      } catch (error) {
        setStats((prev) => ({
          ...prev,
          loading: false,
          error: error instanceof Error ? error.message : "Failed to load dashboard data",
        }));
      }
    };
    fetchStats();
  }, []);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Infrastructure Self-Service Portal</h1>
        <p className="mt-2 text-lg text-slate-600">
          Deploy AWS infrastructure using AI-powered recommendations and approved Terraform modules
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-3">
        <Link
          href="/new-request"
          className="group rounded-lg border-2 border-blue-600 bg-blue-50 p-6 transition hover:bg-blue-100"
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-blue-900">New Request</h3>
              <p className="mt-1 text-sm text-blue-700">Create infrastructure deployment</p>
            </div>
            <svg
              className="h-8 w-8 text-blue-600 transition group-hover:translate-x-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </div>
        </Link>

        <Link
          href="/requests"
          className="group rounded-lg border border-slate-200 bg-white p-6 transition hover:border-slate-300 hover:bg-slate-50"
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-slate-900">My Requests</h3>
              <p className="mt-1 text-sm text-slate-600">Track deployment status</p>
            </div>
            <svg
              className="h-8 w-8 text-slate-400 transition group-hover:translate-x-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
          </div>
        </Link>

        <Link
          href="/modules"
          className="group rounded-lg border border-slate-200 bg-white p-6 transition hover:border-slate-300 hover:bg-slate-50"
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-slate-900">Module Catalog</h3>
              <p className="mt-1 text-sm text-slate-600">Browse approved modules</p>
            </div>
            <svg
              className="h-8 w-8 text-slate-400 transition group-hover:translate-x-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
              />
            </svg>
          </div>
        </Link>
      </div>

      {/* Stats Cards */}
      {stats.error ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-800">⚠️ {stats.error}</p>
          <p className="mt-1 text-xs text-red-600">Make sure the backend is running on port 8100</p>
        </div>
      ) : stats.loading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {[1, 2].map((i) => (
            <div key={i} className="animate-pulse rounded-lg border border-slate-200 bg-white p-6">
              <div className="h-4 w-24 rounded bg-slate-200"></div>
              <div className="mt-2 h-8 w-16 rounded bg-slate-200"></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border border-slate-200 bg-white p-6">
            <div className="text-sm font-medium text-slate-600">Approved Modules</div>
            <div className="mt-2 text-3xl font-bold text-slate-900">{stats.totalModules}</div>
            <div className="mt-1 text-xs text-slate-500">Ready to deploy</div>
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-6">
            <div className="text-sm font-medium text-slate-600">Total Requests</div>
            <div className="mt-2 text-3xl font-bold text-slate-900">{stats.totalRequests}</div>
            <div className="mt-1 text-xs text-slate-500">All time</div>
          </div>
        </div>
      )}

      {/* Features */}
      <div className="rounded-lg border border-slate-200 bg-white p-6">
        <h2 className="text-xl font-semibold text-slate-900">Platform Features</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div className="flex gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-green-100">
              <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div>
              <h3 className="font-medium text-slate-900">AI-Powered</h3>
              <p className="text-sm text-slate-600">Natural language infrastructure requests with Amazon Bedrock</p>
            </div>
          </div>

          <div className="flex gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-100">
              <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                />
              </svg>
            </div>
            <div>
              <h3 className="font-medium text-slate-900">Security First</h3>
              <p className="text-sm text-slate-600">6 layers of security validation with Checkov and Trivy</p>
            </div>
          </div>

          <div className="flex gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-purple-100">
              <svg className="h-6 w-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <div>
              <h3 className="font-medium text-slate-900">Approval Workflows</h3>
              <p className="text-sm text-slate-600">Risk-based approvals for DEV, UAT, and PROD environments</p>
            </div>
          </div>

          <div className="flex gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-orange-100">
              <svg className="h-6 w-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"
                />
              </svg>
            </div>
            <div>
              <h3 className="font-medium text-slate-900">Module Reuse</h3>
              <p className="text-sm text-slate-600">Intelligent discovery prevents code duplication</p>
            </div>
          </div>
        </div>
      </div>

      {/* Getting Started */}
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-6">
        <h2 className="text-lg font-semibold text-blue-900">🚀 Getting Started</h2>
        <ol className="mt-3 space-y-2 text-sm text-blue-800">
          <li>1. Browse the <Link href="/modules" className="font-medium underline">Module Catalog</Link> to see available infrastructure</li>
          <li>2. Create a <Link href="/new-request" className="font-medium underline">New Request</Link> by selecting modules and configuring parameters</li>
          <li>3. Track your deployment progress in <Link href="/requests" className="font-medium underline">My Requests</Link></li>
          <li>4. Review security scans and approvals in the deployment pipeline</li>
        </ol>
      </div>
    </div>
  );
}
