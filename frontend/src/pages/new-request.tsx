import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import { api } from "@/services/api";
import type { ModuleMetadata } from "@/types/deployment";

export default function NewRequest() {
  const router = useRouter();
  const [modules, setModules] = useState<ModuleMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    application: "",
    environment: "dev",
    region: "ap-south-1",
    selectedModule: "",
    configuration: {} as Record<string, any>,
  });

  const [moduleConfig, setModuleConfig] = useState<Record<string, string>>({});

  useEffect(() => {
    const fetchModules = async () => {
      try {
        const data = await api.listModules();
        setModules(data);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load modules");
        setLoading(false);
      }
    };
    fetchModules();
  }, []);

  const selectedModuleData = modules.find((m) => m.name === formData.selectedModule);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const requestId = `REQ-${Date.now()}`;
      
      const specification = {
        request_id: requestId,
        source: "self_service" as const,
        user_id: "current-user",
        application: formData.application,
        environment: formData.environment as "dev" | "uat" | "prod",
        region: formData.region,
        resources: [
          {
            type: formData.selectedModule,
            module: formData.selectedModule,
            version: selectedModuleData?.version || "1.0.0",
            action: "reuse" as const,
            configuration: moduleConfig,
          },
        ],
      };

      await api.createRequest(specification);
      router.push(`/requests?success=true&id=${requestId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create request");
      setSubmitting(false);
    }
  };

  const getModuleConfigFields = () => {
    if (!selectedModuleData) return [];

    // Define configuration fields for each module type
    const configs: Record<string, { name: string; label: string; type: string; default?: string; required?: boolean }[]> = {
      vpc: [
        { name: "cidr_block", label: "CIDR Block", type: "text", default: "10.0.0.0/16", required: true },
        { name: "availability_zones", label: "Availability Zones (comma-separated)", type: "text", default: "ap-south-1a,ap-south-1b" },
      ],
      ec2: [
        { name: "instance_type", label: "Instance Type", type: "text", default: "t3.micro", required: true },
        { name: "instance_count", label: "Instance Count", type: "number", default: "1", required: true },
        { name: "ami_id", label: "AMI ID", type: "text", default: "ami-0123456789" },
        { name: "subnet_id", label: "Subnet ID", type: "text", required: true },
      ],
      "security-group": [
        { name: "vpc_id", label: "VPC ID", type: "text", required: true },
        { name: "ingress_rules", label: "Ingress Rules (JSON)", type: "textarea", default: "[]" },
        { name: "egress_rules", label: "Egress Rules (JSON)", type: "textarea", default: "[]" },
      ],
      alb: [
        { name: "vpc_id", label: "VPC ID", type: "text", required: true },
        { name: "subnet_ids", label: "Subnet IDs (comma-separated)", type: "text", required: true },
        { name: "certificate_arn", label: "SSL Certificate ARN", type: "text" },
      ],
      s3: [
        { name: "bucket_name", label: "Bucket Name", type: "text", required: true },
        { name: "versioning_enabled", label: "Enable Versioning", type: "checkbox", default: "true" },
        { name: "encryption_enabled", label: "Enable Encryption", type: "checkbox", default: "true" },
      ],
    };

    return configs[formData.selectedModule] || [];
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
    <div className="mx-auto max-w-3xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900">New Infrastructure Request</h1>
        <p className="mt-2 text-slate-600">Create a new infrastructure deployment using approved Terraform modules</p>
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-800">⚠️ {error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <div className="rounded-lg border border-slate-200 bg-white p-6">
          <h2 className="text-lg font-semibold text-slate-900">Basic Information</h2>
          <div className="mt-4 space-y-4">
            <div>
              <label htmlFor="application" className="block text-sm font-medium text-slate-700">
                Application Name *
              </label>
              <input
                type="text"
                id="application"
                required
                value={formData.application}
                onChange={(e) => setFormData({ ...formData, application: e.target.value })}
                className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="e.g., payment-service"
              />
            </div>

            <div>
              <label htmlFor="environment" className="block text-sm font-medium text-slate-700">
                Environment *
              </label>
              <select
                id="environment"
                required
                value={formData.environment}
                onChange={(e) => setFormData({ ...formData, environment: e.target.value })}
                className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="dev">Development</option>
                <option value="uat">UAT</option>
                <option value="prod">Production</option>
              </select>
            </div>

            <div>
              <label htmlFor="region" className="block text-sm font-medium text-slate-700">
                AWS Region *
              </label>
              <select
                id="region"
                required
                value={formData.region}
                onChange={(e) => setFormData({ ...formData, region: e.target.value })}
                className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="ap-south-1">ap-south-1 (Mumbai)</option>
                <option value="ap-southeast-1">ap-southeast-1 (Singapore)</option>
                <option value="us-east-1">us-east-1 (N. Virginia)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Module Selection */}
        <div className="rounded-lg border border-slate-200 bg-white p-6">
          <h2 className="text-lg font-semibold text-slate-900">Select Module</h2>
          <div className="mt-4">
            <label htmlFor="module" className="block text-sm font-medium text-slate-700">
              Infrastructure Module *
            </label>
            <select
              id="module"
              required
              value={formData.selectedModule}
              onChange={(e) => {
                setFormData({ ...formData, selectedModule: e.target.value });
                setModuleConfig({});
              }}
              className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="">-- Select a module --</option>
              {modules.map((module) => (
                <option key={module.name} value={module.name}>
                  {module.name} - {module.description}
                </option>
              ))}
            </select>

            {selectedModuleData && (
              <div className="mt-4 rounded-lg border border-blue-100 bg-blue-50 p-4">
                <h3 className="font-medium text-blue-900">{selectedModuleData.name}</h3>
                <p className="mt-1 text-sm text-blue-700">{selectedModuleData.description}</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {selectedModuleData.capabilities.map((cap) => (
                    <span key={cap} className="rounded-full bg-blue-200 px-2 py-1 text-xs font-medium text-blue-800">
                      {cap}
                    </span>
                  ))}
                </div>
                <div className="mt-2 text-xs text-blue-600">Version: {selectedModuleData.version}</div>
              </div>
            )}
          </div>
        </div>

        {/* Configuration */}
        {formData.selectedModule && (
          <div className="rounded-lg border border-slate-200 bg-white p-6">
            <h2 className="text-lg font-semibold text-slate-900">Configuration</h2>
            <div className="mt-4 space-y-4">
              {getModuleConfigFields().map((field) => (
                <div key={field.name}>
                  <label htmlFor={field.name} className="block text-sm font-medium text-slate-700">
                    {field.label} {field.required && "*"}
                  </label>
                  {field.type === "textarea" ? (
                    <textarea
                      id={field.name}
                      required={field.required}
                      value={moduleConfig[field.name] || field.default || ""}
                      onChange={(e) => setModuleConfig({ ...moduleConfig, [field.name]: e.target.value })}
                      className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      rows={3}
                    />
                  ) : field.type === "checkbox" ? (
                    <input
                      type="checkbox"
                      id={field.name}
                      checked={moduleConfig[field.name] === "true" || field.default === "true"}
                      onChange={(e) => setModuleConfig({ ...moduleConfig, [field.name]: e.target.checked.toString() })}
                      className="mt-1 h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                    />
                  ) : (
                    <input
                      type={field.type}
                      id={field.name}
                      required={field.required}
                      value={moduleConfig[field.name] || field.default || ""}
                      onChange={(e) => setModuleConfig({ ...moduleConfig, [field.name]: e.target.value })}
                      className="mt-1 block w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-4">
          <button
            type="button"
            onClick={() => router.push("/")}
            className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting || !formData.selectedModule}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:bg-slate-300"
          >
            {submitting ? "Creating..." : "Create Request"}
          </button>
        </div>
      </form>
    </div>
  );
}
