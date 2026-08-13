// Mirrors backend/app/models/deployment.py and ai/schemas/deployment_specification.schema.json.
// Keep these in sync manually until an OpenAPI-generated client replaces this file.

export type RequestSource = "self_service" | "ai_assistant";
export type Environment = "dev" | "uat" | "prod";
export type ResourceType = "vpc" | "ec2" | "security-group" | "alb" | "s3" | "rds";
export type ResourceAction = "reuse" | "generate";

export interface ResourceSpec {
  type: ResourceType;
  module: string;
  version: string;
  action: ResourceAction;
  configuration: Record<string, unknown>;
}

export interface DeploymentSpecification {
  request_id: string;
  source: RequestSource;
  user_id: string;
  application: string;
  environment: Environment;
  region: string;
  resources: ResourceSpec[];
  missing_modules: string[];
  security_requirements: string[];
  approval_required: boolean;
}

export type TerraformStepStatus = "PASS" | "FAIL" | "SKIPPED";

export interface TerraformStepResult {
  step: string;
  status: TerraformStepStatus;
  detail: string;
}

export interface TerraformPlanResult {
  request_id: string;
  working_dir: string;
  steps: TerraformStepResult[];
  overall_status: TerraformStepStatus;
  generated_files: string[];
}

export interface ModuleMetadata {
  module_name: string;
  version: string;
  category: string;
  description: string;
  path: string;
  status: "approved" | "pending_review" | "deprecated" | "rejected";
  supported_environments: Environment[];
  capabilities: string[];
  security_status: "approved" | "pending_review" | "failed";
  inputs: string[];
  outputs: string[];
}
