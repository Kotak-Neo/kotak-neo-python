# Publishing to PyPI

This guide explains how to build and publish the `kotakneoapi` package to PyPI.

## Prerequisites

### 1. PyPI Account
- Create account at https://pypi.org/account/register/
- Verify your email
- Enable 2FA (recommended)

### 2. API Token
- Go to https://pypi.org/manage/account/token/
- Create a new API token
- Scope: "Entire account" or specific to this project
- Save the token securely (you won't see it again)

### 3. Install Build Tools

```bash
pip install build twine
```

## Pre-Publication Checklist

Before publishing, ensure:

- [ ] Version number updated in `pyproject.toml`
- [ ] CHANGELOG.md updated with release notes
- [ ] All tests passing (`pytest`)
- [ ] Code quality checks passing (`ruff check .`)
- [ ] Security scans clean (`bandit -r neo_api_client`)
- [ ] Documentation up to date
- [ ] No sensitive data in repository
- [ ] Git tag created for release

## Building the Package

### 1. Clean Previous Builds

```bash
# Remove old build artifacts
rm -rf build/ dist/ *.egg-info

# Verify clean state
ls -la
```

### 2. Build Distribution Files

```bash
# Build both wheel and source distribution
python -m build

# This creates:
# - dist/kotakneoapi-2.1.1-py3-none-any.whl (wheel)
# - dist/kotakneoapi-2.1.1.tar.gz (source)
```

### 3. Verify Build

```bash
# Check generated files
ls -lh dist/

# Inspect package contents
tar -tzf dist/kotakneoapi-2.1.1.tar.gz | head -20

# Check wheel contents
unzip -l dist/kotakneoapi-2.1.1-py3-none-any.whl | head -20
```

## Testing the Build

### Test Locally

```bash
# Create a fresh virtual environment
python -m venv test_env
source test_env/bin/activate

# Install from wheel
pip install dist/kotakneoapi-2.1.1-py3-none-any.whl

# Test import
python -c "from neo_api_client import NeoAPI; print('Success!')"

# Deactivate and remove test environment
deactivate
rm -rf test_env
```

## Publishing

### Option 1: Publish to TestPyPI First (Recommended)

TestPyPI is a separate instance for testing package uploads.

#### 1. Configure TestPyPI

Create/edit `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-test-api-token-here

[pypi]
username = __token__
password = pypi-your-production-api-token-here
```

**Security Note:** Keep this file secure! Consider using `keyring` instead:

```bash
# Store token in keyring
pip install keyring
keyring set https://test.pypi.org/legacy/ __token__
keyring set https://upload.pypi.org/legacy/ __token__
```

#### 2. Upload to TestPyPI

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# You'll be prompted for username and password
# Username: __token__
# Password: pypi-... (your TestPyPI token)
```

#### 3. Test Installation from TestPyPI

```bash
# Create test environment
python -m venv test_pypi_env
source test_pypi_env/bin/activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    kotakneoapi

# Test the package
python -c "from neo_api_client import NeoAPI; print('TestPyPI install successful!')"

# Clean up
deactivate
rm -rf test_pypi_env
```

### Option 2: Publish to Production PyPI

**⚠️ WARNING: This is permanent! Double-check everything before proceeding.**

```bash
# Upload to PyPI
python -m twine upload dist/*

# Or using API token directly
python -m twine upload -u __token__ -p pypi-your-token-here dist/*
```

#### Verify Upload

1. Check package page: https://pypi.org/project/kotakneoapi/
2. Install and test:

```bash
# Create fresh environment
python -m venv verify_env
source verify_env/bin/activate

# Install from PyPI
pip install kotakneoapi

# Verify installation
python -c "from neo_api_client import NeoAPI; print('PyPI install successful!')"

# Check version
pip show kotakneoapi

# Deactivate
deactivate
rm -rf verify_env
```

## Post-Publication

### 1. Create Git Tag

```bash
# Create annotated tag
git tag -a v2.1.1 -m "Release version 2.1.1"

# Push tag to GitHub
git push origin v2.1.1
```

### 2. Create GitHub Release

1. Go to https://github.com/Kotak-Neo/kotak-neo-python/releases
2. Click "Draft a new release"
3. Select the tag (v2.1.1)
4. Add release title: "v2.1.1"
5. Add release notes from CHANGELOG.md
6. Attach distribution files (optional)
7. Publish release

### 3. Update README Badge

Add PyPI badge to README.md:

```markdown
[![PyPI version](https://badge.fury.io/py/kotakneoapi.svg)](https://badge.fury.io/py/kotakneoapi)
```

### 4. Announce Release

- Update project website/documentation
- Post on social media (if applicable)
- Notify users via email/Slack

## Version Management

### Semantic Versioning

Follow [SemVer](https://semver.org/): `MAJOR.MINOR.PATCH`

- **MAJOR**: Incompatible API changes
- **MINOR**: Add functionality (backward-compatible)
- **PATCH**: Bug fixes (backward-compatible)

### Updating Version

Edit `pyproject.toml`:

```toml
[project]
name = "kotakneoapi"
version = "2.1.1"  # Update this
```

## Troubleshooting

### Error: "File already exists"

You cannot overwrite existing versions on PyPI.

**Solution:** Increment version number and rebuild.

### Error: "Invalid credentials"

**Solutions:**
1. Verify API token is correct
2. Check token hasn't expired
3. Ensure using `__token__` as username
4. Verify token scope includes upload permissions

### Error: "Package name already taken"

If `kotakneoapi` is already taken by someone else:

**Solutions:**
1. Contact PyPI support to claim the name (if you own the trademark)
2. Choose a different package name
3. Update `pyproject.toml` and rebuild

### Build Errors

```bash
# Clear cache and rebuild
rm -rf build/ dist/ *.egg-info
pip cache purge
python -m build
```

## Security Best Practices

1. **Never commit tokens** to git
2. **Use API tokens** instead of passwords
3. **Enable 2FA** on PyPI account
4. **Limit token scope** to specific projects
5. **Rotate tokens** regularly
6. **Use keyring** for storing tokens
7. **Scan for secrets** before committing:
   ```bash
   git-secrets --scan
   ```

## CI/CD Automation

### GitHub Actions Example

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install build twine
      
      - name: Build package
        run: python -m build
      
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

Add `PYPI_API_TOKEN` to GitHub repository secrets.

## Quick Reference

```bash
# Complete publication workflow
rm -rf build/ dist/ *.egg-info  # Clean
python -m build                  # Build
twine check dist/*              # Validate
twine upload --repository testpypi dist/*  # Test
twine upload dist/*             # Publish
git tag -a v2.1.1 -m "Release" # Tag
git push origin v2.1.1         # Push tag
```

## Resources

- [PyPI Documentation](https://packaging.python.org/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Semantic Versioning](https://semver.org/)
- [Python Packaging User Guide](https://packaging.python.org/tutorials/packaging-projects/)

---

[[Back to Main README]](../README.md)
