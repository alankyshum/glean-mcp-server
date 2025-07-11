# Fix GitHub Container Registry 403 Forbidden Error

The **403 Forbidden** error when pushing to GHCR is typically caused by insufficient permissions. Here's how to fix it:

## 🔧 **Step 1: Repository Settings**

### A. Workflow Permissions
1. Go to your repository: `https://github.com/alankyshum/glean-mcp-server`
2. Click **Settings** tab
3. In the left sidebar, click **Actions** → **General**
4. Scroll down to **Workflow permissions**
5. Select **"Read and write permissions"** (NOT "Read repository contents and packages permissions")
6. Check ✅ **"Allow GitHub Actions to create and approve pull requests"**
7. Click **Save**

### B. Actions Permissions
1. Still in **Settings** → **Actions** → **General**
2. Under **Actions permissions**, ensure:
   - **"Allow all actions and reusable workflows"** is selected
   - OR **"Allow select actions and reusable workflows"** with Docker actions allowed

## 🔧 **Step 2: Package Settings**

### A. Enable Package Creation
1. Go to your **GitHub Profile** (click your avatar)
2. Click **Settings**
3. In left sidebar, click **Developer settings**
4. Click **Personal access tokens** → **Tokens (classic)**
5. OR check if you have package creation restrictions

### B. Repository Package Settings
1. In your repository **Settings**
2. Scroll down to **Features** section
3. Ensure **Packages** is enabled (should be by default)

## 🔧 **Step 3: First-Time Package Creation**

For the **first push** to a new package, you might need to:

### Option A: Manual Package Creation
1. Go to `https://github.com/alankyshum?tab=packages`
2. If no packages exist, the first push will create it automatically
3. After first successful push, subsequent pushes should work

### Option B: Use Personal Access Token (if needed)
1. Go to **GitHub Settings** → **Developer settings** → **Personal access tokens**
2. Click **Generate new token (classic)**
3. Select scopes:
   - ✅ `write:packages`
   - ✅ `read:packages`
   - ✅ `repo` (if private repository)
4. Copy the token
5. In your repository, go to **Settings** → **Secrets and variables** → **Actions**
6. Click **New repository secret**
7. Name: `GHCR_TOKEN`
8. Value: (paste your token)

Then update the workflow to use the personal token:
```yaml
- name: Log in to Container Registry
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GHCR_TOKEN }}  # Use personal token instead
```

## 🔧 **Step 4: Test the Fix**

### Method 1: Push a commit
```bash
git add .
git commit -m "Fix GHCR permissions"
git push origin main
```

### Method 2: Run test workflow manually
1. Go to **Actions** tab
2. Click **Docker Build Test**
3. Click **Run workflow** → **Run workflow**

## 🔧 **Step 5: Verify Success**

After successful push, you should see:
1. **Green checkmark** in Actions tab
2. **Package appears** at `https://github.com/alankyshum?tab=packages`
3. **Image available** at `ghcr.io/alankyshum/glean-mcp-server`

## 🚨 **Common Issues**

### Issue: Still getting 403 after settings change
**Solution:** Wait 5-10 minutes for GitHub to propagate permission changes

### Issue: "Package does not exist" error
**Solution:** The first push creates the package. Ensure workflow permissions are correct.

### Issue: Organization restrictions
**Solution:** If this is under an organization, check organization-level package settings

## ✅ **What I Fixed in the Workflow**

1. **Added lowercase conversion** - GHCR requires lowercase repository names
2. **Added `logout: false`** - Prevents premature logout
3. **Better error handling** - More detailed debug output
4. **Fixed image references** - Uses lowercase repository name consistently

The updated workflow should now work with proper repository permissions! 🎉

## 📋 **Quick Checklist**

- [ ] Repository Settings → Actions → General → "Read and write permissions"
- [ ] Repository Settings → Actions → General → Allow GitHub Actions to create PRs
- [ ] Wait 5-10 minutes for changes to propagate
- [ ] Push a commit or run the test workflow manually
- [ ] Check Actions tab for green checkmark
- [ ] Verify package appears in your GitHub packages
