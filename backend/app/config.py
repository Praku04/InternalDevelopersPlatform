"""
Centralized application configuration.

All values are sourced from environment variables (see .env.example at the
repo root). Nothing here is a secret — actual credentials are resolved at
runtime via IAM roles / AWS Secrets Manager / Parameter Store, never via
values baked into this file or committed to source control.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "local"
    log_level: str = "INFO"

    aws_region: str = "ap-south-1"

    # Bedrock is configurable so the model can be swapped without code changes.
    bedrock_model_id: str = "anthropic.claude-sonnet-4-6"

    dynamodb_table_prefix: str = "ai-cloud-self-service"
    dynamodb_endpoint_url: str | None = None  # set for DynamoDB Local in dev

    s3_bucket: str | None = None
    s3_tfstate_bucket: str | None = None
    dynamodb_lock_table: str | None = None

    # Azure DevOps configuration
    azdo_organization: str | None = None
    azdo_project: str | None = None
    azdo_repository_id: str | None = None
    azdo_pipeline_id: int | None = None
    azdo_pat: str | None = None  # Personal Access Token (load from Secrets Manager in prod)

    git_repository: str | None = None
    git_branch: str = "main"
    
    # Backend API URL for pipeline callbacks
    backend_api_url: str = "http://localhost:8000"

    # Path to the Terraform module registry root, used by ModuleRegistryRepository.
    terraform_modules_path: str = "../terraform/modules"

    # Demo/mock mode must be explicit — the platform never silently fakes
    # a deployment result in production code paths.
    demo_mode: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
