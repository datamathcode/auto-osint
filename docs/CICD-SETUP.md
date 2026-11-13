# CI/CD Setup Guide

## Prerequisites

### GitHub Token with Required Scopes

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes:
   - `repo` - Full control of private repositories
   - `workflow` - Update GitHub Action workflows (REQUIRED)
4. Generate token and save it securely

### GitHub Actions Secrets

Configure these secrets in GitHub repository Settings → Secrets and variables → Actions:

**Production Secrets:**
```
PROD_HOST=production-server.example.com
PROD_USER=deploy_user
PROD_SSH_KEY=<private SSH key for deployment>
```

**Staging Secrets:**
```
STAGING_HOST=staging-server.example.com
STAGING_USER=deploy_user
STAGING_SSH_KEY=<private SSH key for staging>
```

**GitHub Secrets (auto-managed):**
```
GITHUB_TOKEN - Auto-provided by GitHub Actions
```

## Branch Protection Rules

### Main Branch Protection

1. Go to GitHub → Settings → Branches
2. Click "Add rule for main"
3. Configure:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - Require conversation resolution before merging
   - Require approval from 1 reviewer
   - Require status checks:
     - Code Quality
     - Tests
     - Security Scan
     - Review

### Develop Branch Protection

1. Create similar rule for develop branch
2. Same requirements but can use status checks
3. Allow force pushes (optional, for maintainers only)

## CI/CD Workflow Details

### lint.yml
Runs on push to develop and PR to develop
- Python: ruff, mypy
- Markdown: mdformat

### test.yml
Runs on push and PR
- pytest with coverage
- Multiple Python versions (3.10, 3.11)
- Upload coverage to Codecov

### security.yml
Runs on push and PR
- bandit security linter
- safety dependency scanner
- Secret detection in code

### review.yml
Runs on PR creation/update
- Self-review checklist
- Branch naming validation
- Debug statement detection

### build.yml
Runs on push and PR
- Build Python package
- Build frontend
- Upload artifacts

### deploy.yml
Runs on push to main or develop
- Build and push Docker images
- Deploy via SSH to staging/production
- Health check verification

## Manual Deployment

### Staging Deployment

```bash
# Build Docker image locally
docker build -t ghcr.io/datamathcode/auto-osint:latest .

# SSH to staging server
ssh staging@example.com

# Pull and deploy
cd /opt/auto-osint
docker-compose pull
docker-compose up -d
docker system prune -f
```

### Production Deployment

```bash
# Same as staging but on production server
ssh prod@example.com
cd /opt/auto-osint
docker-compose pull
docker-compose up -d
docker system prune -f
docker image prune -a -f
```

## Troubleshooting

### Workflow Permission Issues

If you see "refusing to allow an OAuth App to create or update workflow", you need:
- GitHub token with `workflow` scope
- Or manually create workflows in GitHub UI

### Secrets Not Working

1. Check if secrets exist in Settings → Secrets
2. Verify secret names match exactly (case-sensitive)
3. Restart workflow if changed

### Deployment Fails

1. Check GitHub Actions logs for errors
2. Verify SSH keys are correct
3. Check server permissions
4. Verify docker-compose.yml exists on server

## Next Steps

1. Set up GitHub token with workflow scope
2. Configure secrets in GitHub repository
3. Enable branch protection rules
4. Push workflows to repository
5. Test CI/CD pipeline
