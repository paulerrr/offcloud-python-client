import time
import requests
import os
from typing import Optional, Dict, List, Any, Union
from pathlib import Path

from .exceptions import HTTPError, AuthError, NotFoundError, RateLimitError, OffcloudError, TemporaryError


class OffcloudAPI:
    def __init__(self, api_key: str = None):
        self.base_url = "https://offcloud.com/api"
        self.session = requests.Session()
        self.api_key = api_key
        # Set default headers for JSON requests
        self.session.headers.update({
            'Content-Type': 'application/json'
        })

    def _params(self) -> dict:
        """Build query parameters with API key"""
        return {"key": self.api_key} if self.api_key else {}

    def _request(self, method: str, url: str, **kwargs):
        """Make HTTP request with proper error handling"""
        # Ensure we're using JSON for POST requests
        if method == "post" and "data" in kwargs:
            kwargs["json"] = kwargs.pop("data")
        
        # Merge params properly
        params = self._params()
        if "params" in kwargs:
            params.update(kwargs.pop("params"))
        
        resp = getattr(self.session, method)(url, params=params, **kwargs)
        
        # Handle status codes
        code = resp.status_code
        if code == 401:
            raise AuthError(code, resp.text)
        if code == 404:
            raise NotFoundError(code, resp.text)
        if code == 429:
            raise RateLimitError(code, resp.text)
        if code == 502:
            raise HTTPError(code, "Bad Gateway - check request format (use JSON body for POST)")
        if not resp.ok:
            raise HTTPError(code, resp.text)
        
        # Parse JSON response
        try:
            data = resp.json()
            # Check for Offcloud-specific errors
            if isinstance(data, dict):
                if "error" in data:
                    if data["error"] == "Temporary error":
                        raise OffcloudError(f"Temporary error - retry after 10-30 seconds")
                    raise OffcloudError(data["error"])
                if "not_available" in data:
                    raise OffcloudError(f"Feature not available: {data['not_available']} (premium required?)")
            return data
        except ValueError:
            # Return text if not JSON
            return resp.text

    def _request_with_retry(self, method: str, url: str, max_retries: int = 3, **kwargs):
        """Request with exponential backoff for temporary errors"""
        for attempt in range(max_retries):
            try:
                return self._request(method, url, **kwargs)
            except OffcloudError as e:
                if "Temporary error" in str(e) and attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 10  # 10s, 20s, 40s
                    time.sleep(wait_time)
                    continue
                raise
        
    # Authentication
    def login(self, username: str, password: str) -> dict:
        """Login with username/password"""
        url = f"{self.base_url}/login"
        return self._request("post", url, json={"username": username, "password": password})

    def get_api_key(self) -> dict:
        """Get API key (requires active session from login)"""
        url = f"{self.base_url}/key"
        return self._request("post", url)

    def check_login(self) -> dict:
        """Check login status"""
        url = f"{self.base_url}/check"
        return self._request("get", url)

    # Account Management
    def get_account_stats(self) -> dict:
        """Get account statistics and limits"""
        url = f"{self.base_url}/account/stats"
        return self._request("get", url)

    # Download submissions
    def instant(self, url: str, proxy_id: str = None) -> dict:
        """Start instant download through proxy"""
        endpoint = f"{self.base_url}/instant"
        data = {"url": url}
        if proxy_id:
            data["proxyId"] = proxy_id
        return self._request("post", endpoint, json=data)

    def cloud(self, url: str) -> dict:
        """Start cloud download"""
        endpoint = f"{self.base_url}/cloud"
        return self._request("post", endpoint, json={"url": url})

    def remote(self, url: str, remote_option_id: str = None, folder_id: str = None) -> dict:
        """Start remote download to connected storage"""
        endpoint = f"{self.base_url}/remote"
        data = {"url": url}
        if remote_option_id:
            data["remoteOptionId"] = remote_option_id
        if folder_id:
            data["folderId"] = folder_id
        return self._request("post", endpoint, json=data)

    # Configuration
    def get_proxies(self) -> dict:
        """List available proxy servers"""
        url = f"{self.base_url}/proxy"
        return self._request("post", url)

    def get_remote_accounts(self) -> dict:
        """List connected remote storage accounts"""
        url = f"{self.base_url}/remote/accounts"
        return self._request("post", url)

    # Status checking
    def cloud_status(self, request_id: str) -> dict:
        """
        Check cloud download status
        
        Note: API may return nested response like {"status": {...}} 
        This method handles both formats automatically.
        """
        url = f"{self.base_url}/cloud/status"
        response = self._request("post", url, json={"requestId": request_id})
        
        # Handle nested response structure
        if isinstance(response, dict) and "status" in response and isinstance(response["status"], dict):
            return response["status"]
        return response

    def remote_status(self, request_id: str) -> dict:
        """Check remote download status"""
        url = f"{self.base_url}/remote/status"
        return self._request("post", url, json={"requestId": request_id})

    # History
    def get_history(self, limit: int = 10, offset: int = 0, 
                   sort: str = "createdOn", order: str = "desc") -> dict:
        """Get download history"""
        url = f"{self.base_url}/history"
        params = {
            "limit": limit,
            "offset": offset,
            "sort": sort,
            "order": order
        }
        return self._request("get", url, params=params)

    # BitTorrent
    def cache_info(self, hashes: List[str]) -> dict:
        """Check if torrents are cached for instant download"""
        url = f"{self.base_url}/cache"
        return self._request("post", url, json={"hashes": hashes})

    # Archive management
    def explore_cloud(self, request_id: str) -> Union[List[dict], List[str]]:
        """
        Explore archive contents (for ZIP files and torrents)
        
        Returns:
            List of download URLs or file info dictionaries
        """
        url = f"{self.base_url}/cloud/explore/{request_id}"
        return self._request("get", url)

    def list_cloud(self, request_id: str) -> str:
        """
        Get plain text list of download URLs from archive
        
        Returns:
            String with one download URL per line
        """
        url = f"{self.base_url}/cloud/list/{request_id}"
        return self._request("get", url)

    # Retry operations
    def retry_cloud(self, request_id: str) -> dict:
        """Retry failed cloud download"""
        url = f"{self.base_url}/cloud/retry/{request_id}"
        return self._request("get", url)

    def retry_remote(self, request_id: str) -> dict:
        """Retry failed remote download"""
        url = f"{self.base_url}/remote/retry/{request_id}"
        return self._request("get", url)

    # Helper methods
    def wait_for_download(self, request_id: str, download_type: str = "cloud", 
                         poll_interval: int = 5, timeout: int = 3600) -> dict:
        """
        Wait for download to complete with polling
        
        Args:
            request_id: The download request ID
            download_type: Either "cloud" or "remote"
            poll_interval: Seconds between status checks
            timeout: Maximum seconds to wait
            
        Returns:
            Final status dict
            
        Raises:
            TimeoutError: If download doesn't complete within timeout
            OffcloudError: If download fails
        """
        start_time = time.time()
        status_method = self.cloud_status if download_type == "cloud" else self.remote_status
        
        while time.time() - start_time < timeout:
            status = status_method(request_id)
            
            if status.get("status") == "downloaded":
                return status
            elif status.get("status") == "error":
                raise OffcloudError(f"Download failed: {status}")
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Download did not complete within {timeout} seconds")

    def download_and_wait(self, url: str, download_type: str = "cloud", **kwargs) -> dict:
        """
        Start a download and wait for completion
        
        Args:
            url: URL to download
            download_type: "instant", "cloud", or "remote"
            **kwargs: Additional arguments for the download method
            
        Returns:
            Completed download information
        """
        # Start download
        if download_type == "instant":
            return self.instant(url, **kwargs)
        elif download_type == "cloud":
            job = self.cloud(url)
        elif download_type == "remote":
            job = self.remote(url, **kwargs)
        else:
            raise ValueError(f"Invalid download_type: {download_type}")
        
        # Instant downloads return URL immediately
        if download_type == "instant":
            return job
        
        # Wait for cloud/remote downloads
        request_id = job.get("requestId")
        if not request_id:
            raise OffcloudError(f"No requestId in response: {job}")
        
        return self.wait_for_download(request_id, download_type)

    def get_download_urls(self, request_id: str) -> List[str]:
        """
        Get all download URLs for a completed download
        
        Args:
            request_id: The download request ID
            
        Returns:
            List of download URLs
            
        Raises:
            OffcloudError: If files cannot be accessed
        """
        try:
            # First try explore method
            contents = self.explore_cloud(request_id)
            
            if isinstance(contents, list):
                urls = []
                for item in contents:
                    if isinstance(item, dict) and "downloadUrl" in item:
                        urls.append(item["downloadUrl"])
                    elif isinstance(item, str):
                        urls.append(item)
                
                if urls:
                    return urls
            
            # Fallback to list method
            list_response = self.list_cloud(request_id)
            if isinstance(list_response, str) and list_response.strip():
                return [url.strip() for url in list_response.split('\n') if url.strip()]
            
            raise OffcloudError("No download URLs found")
            
        except Exception as e:
            raise OffcloudError(f"Failed to get download URLs: {e}")

    def download_file_to_local(self, url: str, local_path: str, 
                              chunk_size: int = 8192, show_progress: bool = True) -> bool:
        """
        Download a file from Offcloud to local storage
        
        Args:
            url: Download URL from Offcloud
            local_path: Local file path to save to
            chunk_size: Size of download chunks in bytes
            show_progress: Whether to show download progress
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use a separate session without API key params for direct downloads
            temp_session = requests.Session()
            temp_session.headers.update(self.session.headers)
            
            response = temp_session.get(url, stream=True)
            response.raise_for_status()
            
            # Get file size for progress
            total_size = int(response.headers.get('content-length', 0))
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            with open(local_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if show_progress and total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r   📊 Progress: {percent:.1f}% ({downloaded:,}/{total_size:,} bytes)", 
                                  end='', flush=True)
            
            if show_progress:
                print(f"\n   ✅ Downloaded: {local_path}")
            
            return True
            
        except Exception as e:
            if show_progress:
                print(f"\n   ❌ Failed to download: {e}")
            return False

    def download_all_files(self, request_id: str, download_dir: str = "./downloads", 
                          show_progress: bool = True) -> Dict[str, bool]:
        """
        Download all files from a completed cloud download
        
        Args:
            request_id: The download request ID
            download_dir: Local directory to save files
            show_progress: Whether to show download progress
            
        Returns:
            Dictionary mapping filenames to success status
        """
        results = {}
        
        try:
            # Get file information
            contents = self.explore_cloud(request_id)
            
            if isinstance(contents, list):
                for i, item in enumerate(contents, 1):
                    if isinstance(item, dict):
                        filename = item.get('fileName', f'file_{i}')
                        download_url = item.get('downloadUrl', '')
                        filesize = item.get('fileSize', 0)
                        
                        if show_progress:
                            print(f"\n📁 [{i}/{len(contents)}] {filename} ({filesize:,} bytes)")
                        
                        if download_url:
                            # Create safe filename
                            safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                            local_path = os.path.join(download_dir, safe_filename)
                            
                            success = self.download_file_to_local(download_url, local_path, show_progress=show_progress)
                            results[filename] = success
                        else:
                            if show_progress:
                                print(f"   ❌ No download URL for {filename}")
                            results[filename] = False
                    
                    elif isinstance(item, str):
                        # Direct URL
                        download_url = item
                        filename = f"file_{i}"
                        
                        # Try to extract filename from URL
                        if '/' in download_url:
                            potential_filename = download_url.split('/')[-1]
                            if potential_filename and ('.' in potential_filename or len(potential_filename) > 3):
                                filename = potential_filename
                        
                        if show_progress:
                            print(f"\n📁 [{i}/{len(contents)}] {filename}")
                        
                        safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                        local_path = os.path.join(download_dir, safe_filename)
                        
                        success = self.download_file_to_local(download_url, local_path, show_progress=show_progress)
                        results[filename] = success
            else:
                # Fallback to list method
                urls = self.get_download_urls(request_id)
                for i, url in enumerate(urls, 1):
                    filename = f"file_{i}"
                    
                    # Try to extract filename from URL
                    if '/' in url:
                        potential_filename = url.split('/')[-1]
                        if potential_filename and ('.' in potential_filename or len(potential_filename) > 3):
                            filename = potential_filename
                    
                    if show_progress:
                        print(f"\n📁 [{i}/{len(urls)}] {filename}")
                    
                    safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                    local_path = os.path.join(download_dir, safe_filename)
                    
                    success = self.download_file_to_local(url, local_path, show_progress=show_progress)
                    results[filename] = success
            
        except Exception as e:
            raise OffcloudError(f"Failed to download files: {e}")
        
        return results

    def get_direct_download_url(self, url: str, use_retry: bool = True) -> str:
        """
        Get direct download URL with retry for temporary errors
        
        Args:
            url: Offcloud download URL (e.g. from cloud storage)
            use_retry: Whether to retry on temporary errors
            
        Returns:
            Direct download URL or content
        """
        # For direct download URLs, we don't need to add API key params
        # Create a temporary session without default params
        temp_session = requests.Session()
        temp_session.headers.update(self.session.headers)
        
        if use_retry:
            for attempt in range(3):
                try:
                    resp = temp_session.get(url)
                    resp.raise_for_status()
                    try:
                        data = resp.json()
                        if isinstance(data, dict) and data.get("error") == "Temporary error":
                            if attempt < 2:
                                wait_time = (2 ** attempt) * 10
                                time.sleep(wait_time)
                                continue
                            raise TemporaryError("Temporary error - retry after 10-30 seconds")
                    except ValueError:
                        pass
                    return resp.text
                except Exception as e:
                    if attempt == 2:
                        raise
        else:
            resp = temp_session.get(url)
            resp.raise_for_status()
            return resp.text
