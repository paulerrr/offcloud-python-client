# offcloud_api

`offcloud_api` is a comprehensive Python client for the Offcloud API, providing easy programmatic access to Offcloud's download, proxy, and cloud storage endpoints with enhanced local file download capabilities.

## Features

### Core API Features
- Complete API coverage including account stats, history, and remote storage
- Support for instant, cloud, and remote downloads
- BitTorrent cache checking and magnet link support
- Archive exploration for ZIP files and torrents
- Automatic retry with exponential backoff for temporary errors
- Proper JSON request handling for POST endpoints
- Typed exceptions for different error scenarios

### Enhanced Local Download Features
- **Local file downloads** with progress tracking
- **Batch download** all files from torrents/archives automatically
- **Smart filename handling** and sanitization
- **Robust archive parsing** (handles multiple response formats)
- **Nested response handling** for improved reliability

## Installation

```bash
pip install offcloud_api
# or editable during development
pip install -e .
```

## Quickstart

### Basic Usage
```python
from offcloud_api import OffcloudAPI
from offcloud_api.exceptions import OffcloudError

# Initialize with API key
client = OffcloudAPI(api_key="your_api_key_here")

try:
    # Check account status
    stats = client.get_account_stats()
    print(f"Premium: {stats['isPremium']}")
    print(f"Cloud storage: {stats['limits']['cloud']} bytes")

    # Download a file to cloud storage and wait for completion
    result = client.download_and_wait(
        url="https://example.com/file.zip",
        download_type="cloud"
    )
    print(f"Download complete: {result['url']}")

except OffcloudError as e:
    print(f"Error: {e}")
```

### Complete Download Workflow
```python
from offcloud_api import OffcloudAPI

client = OffcloudAPI(api_key="your_key")

# Download magnet link and save all files locally
magnet_url = "magnet:?xt=urn:btih:..."

# Start download and wait for completion
result = client.download_and_wait(magnet_url, "cloud")

# Download all files to local storage
downloaded_files = client.download_all_files(
    result["requestId"], 
    "./downloads/"
)

print(f"Downloaded {sum(downloaded_files.values())} files successfully")
```

## Authentication

### Using API Key (Recommended)
```python
client = OffcloudAPI(api_key="your_api_key_here")
```

### Using Username/Password
```python
client = OffcloudAPI()
client.login("username", "password")
key_data = client.get_api_key()
client.api_key = key_data["key"]
```

## Download Types

### Instant Download
Downloads through Offcloud proxy with immediate URL:
```python
# Simple instant download
job = client.instant("https://example.com/file.zip")
download_url = job["url"]

# With specific proxy
proxies = client.get_proxies()
proxy_id = proxies["list"][0]["id"]
job = client.instant("https://example.com/file.zip", proxy_id=proxy_id)
```

### Cloud Download
Downloads to Offcloud storage for later access:
```python
# Start cloud download
job = client.cloud("https://example.com/file.zip")
request_id = job["requestId"]

# Check status (automatically handles nested responses)
status = client.cloud_status(request_id)
if status["status"] == "downloaded":
    print(f"Ready: {status['url']}")

# Or use the helper method
result = client.download_and_wait("https://example.com/file.zip", "cloud")
```

### Remote Download
Transfers to your connected storage (Google Drive, Dropbox, WebDAV):
```python
# List remote accounts
accounts = client.get_remote_accounts()
remote_id = accounts["data"][0]["remoteOptionId"]

# Start remote transfer
job = client.remote(
    url="https://example.com/file.zip",
    remote_option_id=remote_id,
    folder_id="/"
)
```

## Local File Downloads

### Download Individual Files
```python
# Download a single file with progress tracking
success = client.download_file_to_local(
    url="https://offcloud.com/download/xyz/file.pdf",
    local_path="./downloads/file.pdf"
)

if success:
    print("File downloaded successfully!")
```

### Download All Files from Archive/Torrent
```python
# Download all files from a request ID
request_id = "682fec68087e0a20ce1e7f95"
results = client.download_all_files(request_id, "./downloads/")

print(f"Success: {sum(results.values())} files")
print(f"Failed: {len(results) - sum(results.values())} files")
```

### Extract Download URLs
```python
# Get all download URLs for manual processing
urls = client.get_download_urls(request_id)
for url in urls:
    print(f"Available: {url}")
```

## Monitoring Downloads

### Manual Polling
```python
import time

request_id = "682fec68087e0a20ce1e7f95"
while True:
    status = client.cloud_status(request_id)  # Handles nested responses automatically
    
    if status["status"] == "downloaded":
        print("Complete!")
        break
    elif status["status"] == "error":
        print("Failed!")
        break
    
    print(f"Progress: {status.get('amount', 0)} bytes")
    time.sleep(5)
```

### Using Helper Method
```python
# Automatically polls until completion
final_status = client.wait_for_download(
    request_id="682fec68087e0a20ce1e7f95",
    download_type="cloud",
    poll_interval=5,  # seconds
    timeout=3600      # 1 hour max
)
```

## Working with Archives and Torrents

```python
# Download a ZIP file or torrent
job = client.cloud("https://example.com/archive.zip")
request_id = job["requestId"]

# Wait for completion
client.wait_for_download(request_id)

# Explore contents (enhanced parsing included)
contents = client.explore_cloud(request_id)
for file in contents:
    if isinstance(file, dict):
        print(f"{file['fileName']}: {file['fileSize']} bytes")
        print(f"  URL: {file['downloadUrl']}")
    else:
        print(f"File URL: {file}")

# Get all URLs as text
urls = client.list_cloud(request_id)
print(urls)  # One URL per line

# Download everything locally
downloaded_files = client.download_all_files(request_id, "./downloads/")
```

## BitTorrent Support

```python
# Check if torrents are cached
hashes = [
    "08ada5a7a6183aae1e09d831df6748d566095a10",
    "d84b7c56e1b7d38de18ad5a899f354c2b351e697"
]

cache_info = client.cache_info(hashes)
for item in cache_info.get("cachedItems", []):
    print(f"{item['name']} ({item['size']} bytes) - Cached!")

# Download cached torrent
magnet_url = "magnet:?xt=urn:btih:08ada5a7a6183aae1e09d831df6748d566095a10"
result = client.download_and_wait(magnet_url, "cloud")
files = client.download_all_files(result["requestId"], "./torrents/")
```

## Account Management

```python
# Get account statistics
stats = client.get_account_stats()
print(f"Email: {stats['email']}")
print(f"Premium: {stats['isPremium']}")
print(f"Expires: {stats['expirationDate']}")
print(f"Cloud storage: {stats['limits']['cloud']} bytes")
print(f"Proxy bandwidth: {stats['limits']['proxy']} bytes")

# Get download history
history = client.get_history(limit=50, order="desc")
for item in history["history"]:
    print(f"{item['fileName']} - {item['status']}")
    print(f"  Type: {item['downloadType']}")
    print(f"  Date: {item['createdOn']}")
```

## Error Handling

```python
from offcloud_api.exceptions import (
    AuthError, 
    NotFoundError, 
    RateLimitError,
    TemporaryError,
    FeatureNotAvailableError,
    OffcloudError
)

try:
    client.cloud("https://example.com/file.zip")
except AuthError:
    print("Invalid API key or not logged in")
except RateLimitError:
    print("Too many requests - slow down")
except FeatureNotAvailableError as e:
    print(f"Premium required for: {e.feature}")
except OffcloudError as e:
    # Catches all other Offcloud-specific errors
    print(f"Offcloud error: {e}")
```

## Handling Temporary Errors

The client automatically retries temporary errors with exponential backoff:
```python
# This will retry up to 3 times with increasing delays
client._request_with_retry("get", url, max_retries=3)
```

## Advanced Usage

### Custom Session Configuration
```python
client = OffcloudAPI(api_key="your_key")
# Add custom headers
client.session.headers.update({"User-Agent": "MyApp/1.0"})
# Configure timeouts
client.session.timeout = 30
```

### Webhook Emulation
Since Offcloud doesn't support webhooks, you can build your own:
```python
import requests
import time

def monitor_with_callback(client, request_id, callback_url):
    """Poll Offcloud and trigger webhook on completion"""
    while True:
        status = client.cloud_status(request_id)
        
        if status["status"] in ["downloaded", "error"]:
            # Trigger webhook
            requests.post(callback_url, json={
                "request_id": request_id,
                "status": status
            })
            break
        
        time.sleep(5)
```

### Batch Processing
```python
# Process multiple downloads concurrently
import concurrent.futures
import threading

def download_url(client, url, local_dir):
    """Download a single URL to local directory"""
    try:
        result = client.download_and_wait(url, "cloud")
        files = client.download_all_files(result["requestId"], local_dir)
        return sum(files.values())
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return 0

# Download multiple URLs
urls = [
    "https://example.com/file1.zip",
    "magnet:?xt=urn:btih:...",
    "https://example.com/file2.pdf"
]

# Create separate client instances for threading
clients = [OffcloudAPI(api_key="your_key") for _ in urls]

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    futures = [
        executor.submit(download_url, client, url, f"./downloads/{i}/")
        for i, (client, url) in enumerate(zip(clients, urls))
    ]
    
    for future in concurrent.futures.as_completed(futures):
        files_downloaded = future.result()
        print(f"Completed: {files_downloaded} files")
```

## API Reference

### Core Methods
- `login(username, password)` - Authenticate with username/password
- `get_api_key()` - Retrieve API key after login
- `instant(url, proxy_id=None)` - Start instant download
- `cloud(url)` - Start cloud download
- `remote(url, remote_option_id, folder_id)` - Start remote download
- `cloud_status(request_id)` - Check download status
- `wait_for_download(request_id, download_type, poll_interval=5, timeout=3600)` - Wait for completion

### Local Download Methods
- `download_file_to_local(url, local_path)` - Download single file
- `download_all_files(request_id, local_dir)` - Download all files from request
- `get_download_urls(request_id)` - Extract all download URLs
- `download_and_wait(url, download_type)` - Complete download workflow

### Archive/Torrent Methods
- `explore_cloud(request_id)` - Explore archive contents
- `list_cloud(request_id)` - List download URLs as text
- `cache_info(hashes)` - Check BitTorrent cache status

### Account Methods
- `get_account_stats()` - Account information and limits
- `get_history(limit=50, order='desc')` - Download history
- `get_proxies()` - Available proxy servers
- `get_remote_accounts()` - Connected remote storage accounts

## Notes and Best Practices

- **Request IDs** are MongoDB ObjectIds (24 character hex strings)
- **POST endpoints** require JSON bodies, not URL parameters
- **Temporary errors** may occur on cloud download URLs - these are automatically retried
- **No webhook support** - use polling to monitor download progress
- **Rate limiting** - recommended 0.5-1 second delay between requests
- **File safety** - The library automatically sanitizes filenames for cross-platform compatibility
- **Memory usage** - Large files are streamed during download to minimize memory footprint

## Development & Testing

### Running Tests
```bash
pytest tests/
```

### Testing Checklist
Test with:
- ✅ Magnet links (multi-file torrents)
- ✅ Single file downloads
- ✅ ZIP archives
- ✅ Various file types (PDF, video, etc.)
- ✅ Both premium and free accounts
- ✅ Error conditions (invalid URLs, expired downloads, etc.)
- ✅ Local download functionality
- ✅ API response handling

## Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -am 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Create Pull Request

Please ensure all tests pass and add tests for new features.

## License

This project is licensed under the **Non‑Commercial MIT License**.  
You are free to use, copy, modify and distribute this library **only for non‑commercial purposes**.  
Derivative works that add substantial new content may be licensed (and sold) separately.  
See [LICENSE](LICENSE) for full terms.

## Changelog

### v0.1.0 (Initial Release)
- Complete Offcloud API coverage
- Support for instant, cloud, and remote downloads
- Local file download capabilities
- Batch download functionality for archives/torrents
- BitTorrent cache checking and magnet link support
- Automatic retry with exponential backoff
- Comprehensive error handling with typed exceptions
- Account management and history features
- Smart filename sanitization and progress tracking