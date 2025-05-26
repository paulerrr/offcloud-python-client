# New in v0.3.0 - Local File Downloads

## Complete Download Workflow

The easiest way to download and save files locally:

```python
from offcloud_api import OffcloudAPI

client = OffcloudAPI(api_key="your_api_key_here")

# Download a magnet link and save all files locally
result = client.download_and_wait(
    "magnet:?xt=urn:btih:C6A5F797B392B0C4CE50C3A274E4FD5573FFE92D&dn=...",
    "cloud"
)

# Download all files to ./downloads/ folder
downloaded_files = client.download_all_files(result["requestId"])

# Check results
successful = sum(downloaded_files.values())
total = len(downloaded_files)
print(f"Successfully downloaded {successful}/{total} files")
```

## Individual File Downloads

For more control over the download process:

```python
# Start cloud download
job = client.cloud("https://example.com/file.zip")
request_id = job["requestId"]

# Wait for completion
client.wait_for_download(request_id, "cloud")

# Get all download URLs
urls = client.get_download_urls(request_id)

# Download specific files
for url in urls:
    if "important.pdf" in url:
        client.download_file_to_local(url, "./downloads/important.pdf")
```

## Progress Tracking

All download methods include built-in progress tracking:

```python
# Enable progress display (default)
client.download_all_files(request_id, show_progress=True)

# Output:
# 📁 [1/3] ChatGPT.pdf (8,245,123 bytes)
#    📊 Progress: 100.0% (8,245,123/8,245,123 bytes)
#    ✅ Downloaded: ./downloads/ChatGPT.pdf
```

## Working with Torrents

Multi-file torrents are automatically handled:

```python
# Download a torrent
job = client.cloud("magnet:?xt=urn:btih:...")
request_id = job["requestId"]

# Wait and download all files
client.wait_for_download(request_id)
results = client.download_all_files(request_id, "./my_downloads/")

# Results dict shows success/failure for each file
for filename, success in results.items():
    if success:
        print(f"✅ {filename}")
    else:
        print(f"❌ {filename}")
```

## Error Handling

Enhanced error handling for download operations:

```python
try:
    urls = client.get_download_urls(request_id)
    results = client.download_all_files(request_id)
except OffcloudError as e:
    print(f"Download failed: {e}")
    # Handle specific error conditions
```

## Migration from v0.2.x

All existing code continues to work unchanged. New methods are additions only:

```python
# v0.2.x code still works
job = client.cloud("https://example.com/file.zip")
status = client.cloud_status(job["requestId"])

# v0.3.0 adds convenience methods
files = client.download_all_files(job["requestId"])  # New!
```
