# TestPyPI Upload Guide

Complete guide for uploading kotakneoapi to TestPyPI.

## Current Status

✅ **Package Built Successfully**
- Source distribution: `kotakneoapi-2.2.0.tar.gz`
- Wheel distribution: `kotakneoapi-2.2.0-py3-none-any.whl`
- Validation: **PASSED**

> Note: bundled CSV scrip-master files were removed from the distribution, so the
> package is now only tens of KB (they are downloaded on demand at runtime instead).

## Steps Completed

- [x] Cleaned previous builds
- [x] Built source distribution (sdist)
- [x] Built wheel distribution
- [x] Validated package with twine
- [ ] Upload to TestPyPI
- [ ] Test installation from TestPyPI
- [ ] Verify package works

---

## Next Steps

### Step 1: Get Your TestPyPI API Token

1. **Go to TestPyPI account settings:**
   ```
   https://test.pypi.org/manage/account/token/
   ```

2. **Create a new API token:**
   - Click "Add API token"
   - **Token name**: `kotakneoapi-upload` (or any descriptive name)
   - **Scope**: "Entire account (all projects)"
   - Click "Add token"

3. **Copy the token immediately!**
   - ⚠️ You won't be able to see it again
   - Format: `pypi-AgEIcHlwaS5vcmc...`
   - Save it securely (password manager recommended)

---

### Step 2: Upload to TestPyPI

#### Option A: Interactive Upload (Easier)

```bash
twine upload --repository testpypi dist/*
```

When prompted:
```
Username: __token__
Password: <paste your token here>
```

**Important:**
- Username is literally `__token__` (two underscores)
- Password is your full API token starting with `pypi-`

#### Option B: One-Line Upload (Recommended)

```bash
twine upload --repository testpypi -u __token__ -p YOUR_TOKEN_HERE dist/*
```

Replace `YOUR_TOKEN_HERE` with your actual token.

#### Option C: Using Environment Variable (Most Secure)

```bash
# Set environment variable
export TWINE_PASSWORD="your-testpypi-token-here"

# Upload
twine upload --repository testpypi -u __token__ dist/*

# Clear the variable after upload
unset TWINE_PASSWORD
```

---

### Step 3: Verify Upload

After successful upload, you'll see:

```
Uploading distributions to https://test.pypi.org/legacy/
Uploading kotakneoapi-2.2.0-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.8/1.8 MB • 0:00:00
Uploading kotakneoapi-2.2.0.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.6/1.6 MB • 0:00:00

View at:
https://test.pypi.org/project/kotakneoapi/2.2.0/
```

**Visit your package page:**
```
https://test.pypi.org/project/kotakneoapi/
```

---

### Step 4: Test Installation from TestPyPI

Create a fresh test environment and install from TestPyPI:

```bash
# Create new virtual environment
python -m venv test_install_env
source test_install_env/bin/activate  # On Windows: test_install_env\Scripts\activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    kotakneoapi

# The --extra-index-url allows installing dependencies from PyPI
# since TestPyPI doesn't have all dependencies
```

---

### Step 5: Verify Installation

Test that the package works:

```python
# Test import
python -c "from neo_api_client import NeoAPI; print('✅ Import successful')"

# Check version
python -c "from neo_api_client import __version__; print(f'Version: {__version__}')"

# Create client instance
python -c "
from neo_api_client import NeoAPI
client = NeoAPI(environment='prod', consumer_key='test')
print('✅ NeoAPI client created successfully')
"
```

---

### Step 6: Cleanup Test Environment

```bash
# Deactivate virtual environment
deactivate

# Remove test environment
rm -rf test_install_env
```

---

## Troubleshooting

### Error: "403 Forbidden"

**Cause:** Invalid or expired token

**Solution:**
1. Generate a new token from TestPyPI
2. Make sure you're using `__token__` as username
3. Verify token scope includes upload permissions

---

### Error: "400 Bad Request: File already exists"

**Cause:** Version 2.2.0 already uploaded

**Solution:**
You cannot overwrite existing versions on PyPI/TestPyPI. Options:

1. **Increment version** (recommended):
   ```bash
   # Edit pyproject.toml
   # Change: version = "2.2.0"
   # To:     version = "2.2.1"
   
   # Rebuild and upload
   rm -rf dist/ build/ *.egg-info
   python -m build
   twine upload --repository testpypi dist/*
   ```

2. **Delete old version** (TestPyPI only):
   - Go to https://test.pypi.org/manage/project/kotakneoapi/releases/
   - Delete the 2.2.0 release
   - Re-upload

---

### Error: "Package name already exists"

**Cause:** Someone else owns the `kotakneoapi` name

**Solution:**
1. Contact TestPyPI support to claim the name (if you own trademark)
2. Or choose a different package name:
   ```toml
   # In pyproject.toml
   [project]
   name = "kotakneoapi-test"  # or another name
   ```

---

### Error: "Invalid distribution"

**Cause:** Build artifacts corrupted

**Solution:**
```bash
# Clean and rebuild
rm -rf build/ dist/ *.egg-info
python -m build
twine check dist/*
twine upload --repository testpypi dist/*
```

---

### Error: Network/SSL Issues

**Solution:**
```bash
# Update pip and twine
pip install --upgrade pip twine

# Try with verbose output
twine upload --repository testpypi --verbose dist/*
```

---

## After Successful Upload

### 1. Update README Badge

Add TestPyPI badge to README.md:

```markdown
[![TestPyPI](https://img.shields.io/badge/TestPyPI-2.2.0-blue.svg)](https://test.pypi.org/project/kotakneoapi/)
```

### 2. Test from Different Machines

Try installing on:
- [ ] Windows
- [ ] macOS  
- [ ] Linux

### 3. Document Installation

Update docs to mention TestPyPI availability:

```bash
# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    kotakneoapi
```

### 4. Announce to Team

Share the TestPyPI link with your team for testing.

---

## Security Best Practices

1. **Never commit tokens** to git
   ```bash
   # Check before committing
   git diff
   ```

2. **Use environment variables** for tokens
   ```bash
   export TWINE_PASSWORD="your-token"
   ```

3. **Rotate tokens** after testing
   - Delete test tokens after upload
   - Create new tokens for production

4. **Limit token scope** to specific projects (when available)

5. **Store tokens securely**
   - Use password manager
   - Or use keyring:
     ```bash
     pip install keyring
     keyring set https://test.pypi.org/legacy/ __token__
     ```

---

## Configuration File (Optional)

Create `~/.pypirc` for easier uploads:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-testpypi-token-here

[pypi]
username = __token__
password = pypi-your-production-token-here
```

**⚠️ Security Warning:** Keep this file secure!
```bash
chmod 600 ~/.pypirc
```

Then upload with just:
```bash
twine upload --repository testpypi dist/*
```

---

## When Ready for Production PyPI

After testing on TestPyPI:

1. **Get production PyPI token:**
   ```
   https://pypi.org/manage/account/token/
   ```

2. **Upload to production:**
   ```bash
   twine upload dist/*
   ```

3. **Verify:**
   ```bash
   pip install kotakneoapi
   ```

4. **Update documentation** to use production PyPI

---

## Quick Reference Commands

```bash
# Build package
python -m build

# Check package
twine check dist/*

# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    kotakneoapi

# Upload to production PyPI
twine upload dist/*

# Install from production PyPI
pip install kotakneoapi
```

---

## Resources

- **TestPyPI:** https://test.pypi.org/
- **Your Package (after upload):** https://test.pypi.org/project/kotakneoapi/
- **Account Tokens:** https://test.pypi.org/manage/account/token/
- **Python Packaging Guide:** https://packaging.python.org/
- **Twine Documentation:** https://twine.readthedocs.io/

---

## Summary Checklist

Before uploading:
- [x] Package built successfully
- [x] Package validated with twine
- [ ] TestPyPI token obtained
- [ ] Token stored securely

During upload:
- [ ] Upload to TestPyPI
- [ ] Verify package page loads
- [ ] Check package metadata

After upload:
- [ ] Test installation in clean environment
- [ ] Verify imports work
- [ ] Test basic functionality
- [ ] Document installation method
- [ ] Share with team for testing

---

**Ready to upload?** Run:
```bash
twine upload --repository testpypi dist/*
```

Good luck! 🚀
