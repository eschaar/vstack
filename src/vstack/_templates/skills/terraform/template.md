{{SKILL_CONTEXT}}

# terraform — Infrastructure as Code with Terraform

Write, review, and refactor Terraform configurations for any provider.

## Out of scope

- Terragrunt DRY wrappers (use `terragrunt`)
- AWS-specific CLI workflows (use `aws-cli`)
- CloudFormation templates (use `cloudformation`)

## Step 0: Detect Context

```bash
terraform version 2>/dev/null || echo "terraform not installed"

# Find all Terraform roots
find . -name "*.tf" -not -path "*/.terraform/*" | sed 's|/[^/]*\.tf$||' | sort -u

# Check backend and provider constraints
grep -rl "backend" . --include="*.tf" 2>/dev/null
grep -A5 'required_providers' -r . --include="*.tf" 2>/dev/null | head -20
```

## Step 1: Repository Structure

### Single service

```
infra/
├── main.tf           ← root module: resource definitions
├── variables.tf      ← input variables with types and defaults
├── outputs.tf        ← outputs consumed by other modules or CI
├── providers.tf      ← provider configuration and version constraints
├── versions.tf       ← terraform {} block with required_version
├── locals.tf         ← computed values and name construction
└── modules/
    └── <name>/       ← reusable submodule
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

### Monorepo / multi-environment

```
infra/
├── modules/          ← shared reusable modules
│   └── <name>/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   └── terraform.tfvars
│   ├── staging/
│   └── prod/
```

## Step 2: Provider and Version Pinning

Always pin provider versions and the Terraform binary. Never use unbounded ranges in production.

```hcl
# versions.tf
terraform {
  required_version = "~> 1.9"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

**Version constraint operators:**

- `~> 1.9` — allows patch and minor updates within 1.x (recommended)
- `>= 1.9, < 2.0` — explicit range
- `= 1.9.2` — exact pin (lockfile preferred over this)

Always commit `.terraform.lock.hcl` to source control.

## Step 3: Remote Backend

Never use local state in production. Configure a remote backend with state locking.

```hcl
# AWS S3 + DynamoDB locking
terraform {
  backend "s3" {
    bucket         = "myorg-terraform-state"
    key            = "services/myservice/terraform.tfstate"
    region         = "eu-west-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}
```

**State bucket requirements:**

- Enable versioning on the S3 bucket (enables rollback)
- Enable server-side encryption (SSE-S3 minimum, SSE-KMS preferred)
- Block all public access
- Restrict bucket policy to Terraform IAM role + approved team roles

## Step 4: Variables and Outputs

```hcl
# variables.tf — always include type, description, and sensible defaults
variable "environment" {
  type        = string
  description = "Deployment environment: dev | staging | prod"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging, or prod."
  }
}

variable "db_password" {
  type        = string
  description = "Database master password — supply via TF_VAR_db_password or tfvars."
  sensitive   = true
}
```

```hcl
# outputs.tf — mark sensitive outputs accordingly
output "api_endpoint" {
  description = "Base URL of the deployed API."
  value       = aws_lb.main.dns_name
}

output "db_connection_string" {
  description = "Database connection string."
  value       = "postgres://${aws_db_instance.main.endpoint}/${var.db_name}"
  sensitive   = true
}
```

**Rules:**

- Mark all secrets as `sensitive = true` — prevents them appearing in plan output and logs
- Never hardcode secrets in `.tf` files or `.tfvars` committed to source control
- Use `TF_VAR_*` env vars or a secrets manager data source for secrets

## Step 5: Naming and Tagging

```hcl
# locals.tf — centralize name construction
locals {
  name_prefix = "${var.project}-${var.environment}"

  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
    Owner       = var.team
  }
}

resource "aws_s3_bucket" "uploads" {
  bucket = "${local.name_prefix}-uploads"
  tags   = local.common_tags
}
```

## Step 6: Module Design

```hcl
# Good: module exposes what callers need
module "rds" {
  source = "./modules/rds"

  name        = "${local.name_prefix}-db"
  subnet_ids  = module.vpc.private_subnet_ids
  vpc_id      = module.vpc.vpc_id
  environment = var.environment
}
```

**Module rules:**

- One purpose per module — avoid "kitchen sink" modules
- Accept subnet IDs and VPC IDs as inputs rather than looking them up inside the module (reduces coupling)
- Expose only what callers need as outputs
- Pin module versions when sourcing from a registry: `version = "~> 3.0"`

## Step 7: Security Hardening

```bash
# Run tfsec for security misconfigurations
tfsec . --minimum-severity HIGH

# Run checkov for CIS benchmark checks
checkov -d . --framework terraform --compact --quiet

# Run trivy for misconfigurations
trivy config . --severity HIGH,CRITICAL
```

**Common misconfigurations to check:**

- S3 buckets: `block_public_acls = true`, `block_public_policy = true`, encryption enabled
- RDS: `storage_encrypted = true`, `deletion_protection = true`, no public access
- Security groups: no `0.0.0.0/0` on SSH/RDP; restrict to known CIDR ranges
- IAM: least-privilege policies; no `*` actions on `*` resources
- KMS: key rotation enabled (`enable_key_rotation = true`)
- VPC: flow logs enabled; no internet gateway on private subnets

## Step 8: Plan and Apply Workflow

```bash
# Initialize (after adding/changing providers or backends)
terraform init

# Format check (enforce in CI)
terraform fmt -check -recursive

# Validate syntax and references
terraform validate

# Plan — always review before applying
terraform plan -out=tfplan

# Apply from saved plan (ensures what was reviewed is what runs)
terraform apply tfplan

# Targeted apply (use sparingly — prefer full applies)
terraform apply -target=aws_s3_bucket.uploads

# Destroy (requires explicit confirmation — destructive)
terraform destroy -target=aws_s3_bucket.uploads
```

## Step 9: Drift Detection

```bash
# Detect drift between state and real infrastructure
terraform plan -detailed-exitcode
# Exit code 0: no changes; 1: error; 2: changes present

# Refresh state to pick up out-of-band changes (read-only)
terraform refresh
```

Set up drift detection in CI:

```yaml
- name: Terraform plan (drift check)
  run: terraform plan -detailed-exitcode -no-color
  continue-on-error: false  # fail CI on drift
```

## Step 10: State Operations (high risk)

Always back up state before state manipulations.

```bash
# List state resources
terraform state list

# Show a specific resource
terraform state show aws_s3_bucket.uploads

# Move resource to new address (after refactor)
terraform state mv aws_s3_bucket.uploads aws_s3_bucket.media

# Import existing resource into state
terraform import aws_s3_bucket.uploads my-existing-bucket-name

# Remove resource from state without destroying it
terraform state rm aws_s3_bucket.old_name
```

Run `terraform plan` after every state operation to verify the outcome.

## Review Checklist

- [ ] `required_version` and all providers pinned with `~>` constraints
- [ ] `.terraform.lock.hcl` committed to source control
- [ ] Remote backend configured with encryption and state locking
- [ ] No secrets hardcoded in `.tf` files; sensitive variables marked `sensitive = true`
- [ ] All resources tagged via `locals.common_tags`
- [ ] S3 buckets: public access blocked, encryption enabled
- [ ] RDS: `storage_encrypted`, `deletion_protection`, no public access
- [ ] Security groups: no `0.0.0.0/0` on management ports
- [ ] IAM policies: least privilege, no `*:*` wildcards
- [ ] `tfsec` or `checkov` passes with no HIGH/CRITICAL findings
- [ ] `terraform fmt -check` passes in CI
- [ ] `terraform validate` passes in CI
