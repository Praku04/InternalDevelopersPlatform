import { useState } from "react";
import { useRouter } from "next/router";
import { api } from "@/services/api";
import type { DeploymentSpecification, Environment } from "@/types/deployment";

// Self-service EC2 form (Section 6, Flow A). Submits a DeploymentSpecification
// that reuses the approved vpc + security-group + ec2 modules (Section 46
// first MVP). Actual Terraform plan/security-scan/approval/deploy stages
// are triggered from the request detail page once a request exists.

function makeRequestId(): string {
  return `REQ-${Date.now().toString(36).toUpperCase()}`;
}

export default function Ec2Catalog() {
  const router = useRouter();
  const [application, setApplication] = useState("payment");
  const [environment, setEnvironment] = useState<Environment>("dev");
  const [instanceType, setInstanceType] = useState("t3.medium");
  const [instanceCount, setInstanceCount] = useState(2);
  const [encryptedEbs, setEncryptedEbs] = useState(true);
  const [monitoring, setMonitoring] = useState(true);
  const [privateSubnet, setPrivateSubnet] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    const spec: DeploymentSpecification = {
      request_id: makeRequestId(),
      source: "self_service",
      user_id: "user123", // Replaced by the authenticated user once auth lands.
      application,
      environment,
      region: "ap-south-1",
      resources: [
        {
          type: "vpc",
          module: "vpc",
          version: "1.0.0",
          action: "reuse",
          configuration: {},
        },
        {
          type: "security-group",
          module: "security-group",
          version: "1.0.0",
          action: "reuse",
          configuration: { name_suffix: "ec2", ingress_rules: [] },
        },
        {
          type: "ec2",
          module: "ec2",
          version: "1.0.0",
          action: "reuse",
          configuration: {
            instance_type: instanceType,
            instance_count: instanceCount,
            encrypted_ebs: encryptedEbs,
            monitoring,
            associate_public_ip: !privateSubnet,
          },
        },
      ],
      missing_modules: [],
      security_requirements: [
        ...(encryptedEbs ? ["encrypted_ebs"] : []),
        ...(privateSubnet ? ["private_subnet"] : []),
        ...(monitoring ? ["monitoring"] : []),
      ],
      approval_required: environment !== "dev",
    };

    try {
      const created = await api.createRequest(spec);
      router.push(`/requests/${created.request_id}`);
    } catch (err) {
      setError(String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-xl">
      <h1 className="text-2xl font-bold text-slate-900">Create EC2 Infrastructure</h1>
      <p className="mt-1 text-sm text-slate-600">
        Reuses the approved <code>vpc</code>, <code>security-group</code>, and <code>ec2</code> modules.
      </p>

      <form onSubmit={handleSubmit} className="mt-6 space-y-5 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div>
          <label className="block text-sm font-medium text-slate-700">Application Name</label>
          <input
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
            value={application}
            onChange={(e) => setApplication(e.target.value)}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700">Environment</label>
          <select
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
            value={environment}
            onChange={(e) => setEnvironment(e.target.value as Environment)}
          >
            <option value="dev">DEV</option>
            <option value="uat">UAT</option>
            <option value="prod">PROD</option>
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700">Instance Type</label>
            <input
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
              value={instanceType}
              onChange={(e) => setInstanceType(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Instance Count</label>
            <input
              type="number"
              min={1}
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
              value={instanceCount}
              onChange={(e) => setInstanceCount(Number(e.target.value))}
            />
          </div>
        </div>

        <div className="space-y-2">
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input type="checkbox" checked={encryptedEbs} onChange={(e) => setEncryptedEbs(e.target.checked)} />
            Encrypted EBS
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input type="checkbox" checked={monitoring} onChange={(e) => setMonitoring(e.target.checked)} />
            Detailed Monitoring
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input type="checkbox" checked={privateSubnet} onChange={(e) => setPrivateSubnet(e.target.checked)} />
            Private Subnet Only
          </label>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
        >
          {submitting ? "Submitting..." : "Create Request"}
        </button>
      </form>
    </div>
  );
}
