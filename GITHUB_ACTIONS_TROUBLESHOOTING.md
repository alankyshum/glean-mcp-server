# GitHub Actions Container Registry Troubleshooting

This document helps troubleshoot issues with pushing Docker images to GitHub Container Registry (GHCR).

## Common Issues and Solutions

### 1. Permission Denied Errors

**Symptoms:**
- `denied: permission_denied` errors
- `unauthorized: authentication required` errors

**Solutions:**

#### A. Check Repository Settings
1. Go to your repository on GitHub
2. Navigate to **Settings** → **Actions** → **General**
3. Under **Workflow permissions**, ensure:
   - ✅ **Read and write permissions** is selected
   - ✅ **Allow GitHub Actions to create and approve pull requests** is checked

#### B. Check Package Permissions
1. Go to your repository on GitHub
2. Navigate to **Settings** → **Actions** → **General**
3. Scroll down to **Fork pull request workflows from outside collaborators**
4. Select **Require approval for first-time contributors**

#### C. Enable Package Creation
1. Go to your **GitHub Profile** → **Settings**
2. Navigate to **Developer settings** → **Personal access tokens** → **Tokens (classic)**
3. Or check **Settings** → **Packages** for package visibility settings

### 2. Image Name Issues

**Symptoms:**
- `invalid reference format` errors
- `repository name must be lowercase` errors

**Current Configuration:**
```yaml
env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}  # This becomes: alankyshum/glean-mcp-server
```

**Verification:**
The image will be pushed to: `ghcr.io/alankyshum/glean-mcp-server`

### 3. Authentication Issues

**Symptoms:**
- Login failures
- Token authentication errors

**Solutions:**

#### A. Verify GITHUB_TOKEN Permissions
The workflow uses `${{ secrets.GITHUB_TOKEN }}` which should automatically have the right permissions if the repository settings are correct.

#### B. Manual Token (Alternative)
If automatic token fails, create a Personal Access Token:
1. Go to **GitHub Settings** → **Developer settings** → **Personal access tokens**
2. Create token with `write:packages` permission
3. Add as repository secret named `GHCR_TOKEN`
4. Update workflow to use `${{ secrets.GHCR_TOKEN }}`

### 4. Build Context Issues

**Symptoms:**
- `no such file or directory` errors during build
- Missing files in build context

**Current Dockerfile Context:**
```dockerfile
COPY requirements.txt .
COPY src/ ./src/
```

**Verification Steps:**
1. Ensure `requirements.txt` exists in repository root
2. Ensure `src/` directory exists with Python files
3. Check `.dockerignore` file doesn't exclude necessary files

### 5. Multi-Architecture Build Issues

**Current Configuration:**
```yaml
platforms: linux/amd64,linux/arm64
```

**If ARM64 builds fail:**
- Temporarily use only `linux/amd64`
- Some Python packages may not have ARM64 wheels

## Testing the Fixes

### Method 1: Use the Test Workflow
I've created `.github/workflows/docker-test.yml` that:
- Runs on manual trigger (`workflow_dispatch`)
- Has simplified configuration
- Provides better error messages

To run it:
1. Go to **Actions** tab in your repository
2. Select **Docker Build Test** workflow
3. Click **Run workflow**

### Method 2: Local Testing
```bash
# Test Docker build locally
docker build -t test-glean-mcp .

# Test with GitHub Container Registry format
docker tag test-glean-mcp ghcr.io/alankyshum/glean-mcp-server:test
```

### Method 3: Check Workflow Logs
1. Go to **Actions** tab
2. Click on the failed workflow run
3. Expand the failing step
4. Look for specific error messages

## Updated Workflow Features

The updated `.github/workflows/docker-publish.yml` includes:

1. **✅ Updated Action Versions**
   - `docker/build-push-action@v6` (latest)
   - `actions/setup-python@v5` (latest)

2. **✅ Better Conditional Logic**
   - Only login/push on non-PR events
   - Separate test job that doesn't depend on push

3. **✅ Multi-Architecture Support**
   - `linux/amd64,linux/arm64`

4. **✅ Debug Information**
   - Prints registry and image information

5. **✅ Improved Caching**
   - GitHub Actions cache for faster builds

## Next Steps

1. **Check Repository Settings** (most common issue)
2. **Run the test workflow** to isolate the problem
3. **Check the debug output** in the workflow logs
4. **Verify package permissions** in your GitHub settings

If issues persist, the problem is likely in repository permissions or GitHub package settings.
