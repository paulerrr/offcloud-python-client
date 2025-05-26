# offcloud_api Package Updates - Version 0.3.0

## Issues Found and Fixed

### 1. **Nested Response Structure Bug** 🐛
**Problem**: The `cloud_status()` method sometimes returns nested responses like:
```json
{
  "status": {
    "status": "downloaded",
    "fileName": "...",
    "fileSize": 12099016,
    "isDirectory": true
  }
}
```

**Fix**: Enhanced `cloud_status()` to automatically handle nested responses and return the inner status object.

### 2. **Missing Local Download Functionality** ✨
**Problem**: Original library only handled API calls but didn't provide easy ways to download files to local storage.

**New Features Added**:
- `download_file_to_local()` - Download individual files with progress tracking
- `download_all_files()` - Download all files from a torrent/archive automatically  
- `get_download_urls()` - Extract all download URLs from explore/list responses

### 3. **Better Error Handling and Debugging** 🔧
**Improvements**:
- More informative error messages
- Better handling of API response variations
- Robust parsing of both JSON and string responses from explore/list endpoints

### 4. **Enhanced Archive/Torrent Support** 📁
**Problem**: Original library didn't handle multi-file torrents properly.

**Fixes**:
- Better parsing of `explore_cloud()` responses (handles both dict and string formats)
- Automatic fallback from explore to list method
- Smart filename extraction from URLs
- Safe filename sanitization for local storage

## New Methods Added

### File Download Methods
```python
# Download a single file to local storage
success = client.download_file_to_local(url, "./downloads/file.pdf")

# Download all files from a torrent/archive
results = client.download_all_files(request_id, "./downloads/")

# Get all download URLs for manual processing  
urls = client.get_download_urls(request_id)
```

### Enhanced Helper Methods
```python
# Simplified full download workflow
result = client.download_and_wait(magnet_url, "cloud")
files = client.download_all_files(result["requestId"])
```

## API Improvements

### Better Status Handling
```python
# Now automatically handles nested responses
status = client.cloud_status(request_id)
# Always returns the actual status object, not nested wrapper
```

### Robust Archive Exploration
```python
# Handles multiple response formats automatically
contents = client.explore_cloud(request_id)
# Can return list of dicts, list of URLs, or fallback to list_cloud()
```

## Breaking Changes
None - all changes are backwards compatible.

## Version Bump Recommendation
- Current: `0.2.0`
- Recommended: `0.3.0` (new features added)

## Files to Update

1. **`offcloud_api/client.py`** - Replace with improved version
2. **`offcloud_api/__init__.py`** - Update version to `0.3.0`
3. **`pyproject.toml`** - Update version to `0.3.0`
4. **`README.md`** - Add documentation for new download methods

## Testing Recommendations

Before release, test with:
- ✅ Magnet links (multi-file torrents)
- ✅ Single file downloads
- ✅ ZIP archives
- ✅ Various file types (PDF, video, etc.)
- ✅ Both premium and free accounts
- ✅ Error conditions (invalid URLs, expired downloads, etc.)

## Example Updated Usage

```python
from offcloud_api import OffcloudAPI

client = OffcloudAPI(api_key="your_key")

# Start download and wait for completion
result = client.download_and_wait(
    "magnet:?xt=urn:btih:...", 
    "cloud"
)

# Download all files to local storage
downloaded_files = client.download_all_files(
    result["requestId"], 
    "./downloads/"
)

print(f"Downloaded {sum(downloaded_files.values())} files successfully")
```

This makes the library much more user-friendly for the common use case of "download this magnet/URL and save the files to my computer."
