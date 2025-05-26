#!/usr/bin/env python3
"""
Enhanced offcloud_api test script that downloads files to your local PC
"""

import os
import time
import requests
from pathlib import Path
from urllib.parse import urlparse
from offcloud_api import OffcloudAPI
from offcloud_api.exceptions import (
    OffcloudError,
    AuthError, 
    RateLimitError,
    TemporaryError,
    FeatureNotAvailableError
)

def download_file(url: str, local_path: str, session: requests.Session = None) -> bool:
    """Download a file from URL to local path"""
    if session is None:
        session = requests.Session()
    
    try:
        print(f"   📥 Downloading: {os.path.basename(local_path)}")
        
        response = session.get(url, stream=True)
        response.raise_for_status()
        
        # Get file size for progress
        total_size = int(response.headers.get('content-length', 0))
        
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        with open(local_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r   📊 Progress: {percent:.1f}% ({downloaded:,}/{total_size:,} bytes)", end='', flush=True)
        
        print(f"\n   ✅ Downloaded: {local_path}")
        return True
        
    except Exception as e:
        print(f"\n   ❌ Failed to download {os.path.basename(local_path)}: {e}")
        return False

def main():
    # TODO: Replace with your actual Offcloud API key
    API_KEY = "OiskOg2iC3ov5Yg5LrmWNQaxaj75q2sG"
    
    # The magnet link to download
    MAGNET_URL = ("magnet:?xt=urn:btih:C6A5F797B392B0C4CE50C3A274E4FD5573FFE92D"
                  "&dn=ChatGPT%20For%20Dummies%201st%20Edition"
                  "&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337"
                  "&tr=udp%3A%2F%2Fopen.stealth.si%3A80%2Fannounce"
                  "&tr=udp%3A%2F%2Ftracker.torrent.eu.org%3A451%2Fannounce"
                  "&tr=udp%3A%2F%2Ftracker.bittor.pw%3A1337%2Fannounce"
                  "&tr=udp%3A%2F%2Fpublic.popcorn-tracker.org%3A6969%2Fannounce"
                  "&tr=udp%3A%2F%2Ftracker.dler.org%3A6969%2Fannounce"
                  "&tr=udp%3A%2F%2Fexodus.desync.com%3A6969"
                  "&tr=udp%3A%2F%2Fopen.demonii.com%3A1337%2Fannounce")
    
    # Local download directory
    DOWNLOAD_DIR = "./downloads"
    
    print("🚀 Offcloud API Test - Full Download to PC")
    print("=" * 55)
    
    # Initialize the client
    if API_KEY == "your_api_key_here":
        print("❌ Error: Please set your actual API key in the script!")
        print("   Get your API key from: https://offcloud.com/#/account")
        return
    
    try:
        client = OffcloudAPI(api_key=API_KEY)
        
        # Check account status first
        print("📊 Checking account status...")
        stats = client.get_account_stats()
        print(f"   ✅ Account: {stats.get('email', 'Unknown')}")
        print(f"   ✅ Premium: {stats.get('isPremium', False)}")
        print(f"   ✅ Cloud storage limit: {stats.get('limits', {}).get('cloud', 0):,} bytes")
        print()
        
        # Start the cloud download
        print("📥 Starting cloud download...")
        print(f"   🧲 Magnet: ChatGPT For Dummies 1st Edition")
        
        job = client.cloud(MAGNET_URL)
        request_id = job.get("requestId")
        
        if not request_id:
            print(f"❌ Error: No request ID received. Response: {job}")
            return
        
        print(f"   ✅ Download started with ID: {request_id}")
        print()
        
        # Monitor the download progress
        print("⏳ Monitoring download progress...")
        start_time = time.time()
        
        while True:
            try:
                status_response = client.cloud_status(request_id)
                
                # Handle nested response structure
                if "status" in status_response and isinstance(status_response["status"], dict):
                    status_data = status_response["status"]
                else:
                    status_data = status_response
                
                current_status = status_data.get("status", "unknown")
                
                elapsed = int(time.time() - start_time)
                print(f"   [{elapsed:03d}s] Status: {current_status}")
                
                # Show additional info
                if "fileName" in status_data:
                    print(f"         File: {status_data['fileName']}")
                if "fileSize" in status_data:
                    print(f"         Size: {status_data['fileSize']:,} bytes")
                if "amount" in status_data and status_data['amount'] > 0:
                    print(f"         Downloaded: {status_data['amount']:,} bytes")
                
                if current_status == "downloaded":
                    print("   🎉 Download completed on Offcloud!")
                    print()
                    
                    # Now download to local PC
                    print("💾 Downloading files to your PC...")
                    download_session = requests.Session()
                    
                    # Try to explore the archive if it's a directory/archive
                    if status_data.get("isDirectory", False):
                        print("📋 Getting file list...")
                        try:
                            # According to API docs, explore should return JSON array of download links
                            contents = client.explore_cloud(request_id)
                            print(f"   🔍 Debug - explore_cloud returned: {type(contents)}")
                            print(f"   🔍 Debug - content preview: {str(contents)[:300]}...")
                            
                            if isinstance(contents, list) and len(contents) > 0:
                                print(f"   Found {len(contents)} files to download")
                                
                                successful_downloads = 0
                                total_files = len(contents)
                                
                                for i, file_info in enumerate(contents, 1):
                                    if isinstance(file_info, dict):
                                        filename = file_info.get('fileName', f'file_{i}')
                                        filesize = file_info.get('fileSize', 0)
                                        download_url = file_info.get('downloadUrl', '')
                                        
                                        print(f"\n📁 [{i}/{total_files}] {filename} ({filesize:,} bytes)")
                                        print(f"   🔗 URL: {download_url[:80]}...")
                                        
                                        if download_url:
                                            # Create safe filename and path
                                            safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                                            local_path = os.path.join(DOWNLOAD_DIR, safe_filename)
                                            
                                            if download_file(download_url, local_path, download_session):
                                                successful_downloads += 1
                                        else:
                                            print(f"   ❌ No download URL for {filename}")
                                    elif isinstance(file_info, str):
                                        # Sometimes the API returns URLs directly as strings
                                        download_url = file_info
                                        filename = f"file_{i}"
                                        
                                        # Try to extract filename from URL
                                        if '/' in download_url:
                                            potential_filename = download_url.split('/')[-1]
                                            if potential_filename and ('.' in potential_filename or len(potential_filename) > 3):
                                                filename = potential_filename
                                        
                                        print(f"\n📁 [{i}/{total_files}] {filename}")
                                        print(f"   🔗 URL: {download_url[:80]}...")
                                        
                                        safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                                        local_path = os.path.join(DOWNLOAD_DIR, safe_filename)
                                        
                                        if download_file(download_url, local_path, download_session):
                                            successful_downloads += 1
                                    else:
                                        print(f"   ⚠️  Unexpected file_info type: {type(file_info)} = {file_info}")
                                
                                print(f"\n🎉 Download Summary:")
                                print(f"   ✅ Successfully downloaded: {successful_downloads}/{total_files} files")
                                print(f"   📂 Files saved to: {os.path.abspath(DOWNLOAD_DIR)}")
                                
                            else:
                                print("   ⚠️  explore_cloud didn't return expected list format")
                                print("   🔄 Trying list_cloud method...")
                                
                                # Fallback to list method
                                try:
                                    list_response = client.list_cloud(request_id)
                                    print(f"   🔍 list_cloud returned: {type(list_response)}")
                                    print(f"   🔍 Content: {str(list_response)[:300]}...")
                                    
                                    if isinstance(list_response, str) and list_response.strip():
                                        # Parse URLs from the text response (one per line)
                                        urls = [url.strip() for url in list_response.split('\n') if url.strip()]
                                        print(f"   Found {len(urls)} download URLs from list method")
                                        
                                        successful_downloads = 0
                                        for i, url in enumerate(urls, 1):
                                            filename = f"file_{i}"
                                            
                                            # Try to extract filename from URL
                                            if '/' in url:
                                                potential_filename = url.split('/')[-1]
                                                if potential_filename and ('.' in potential_filename or len(potential_filename) > 3):
                                                    filename = potential_filename
                                            
                                            print(f"\n📁 [{i}/{len(urls)}] {filename}")
                                            print(f"   🔗 URL: {url[:80]}...")
                                            
                                            safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                                            local_path = os.path.join(DOWNLOAD_DIR, safe_filename)
                                            
                                            if download_file(url, local_path, download_session):
                                                successful_downloads += 1
                                        
                                        print(f"\n🎉 Download Summary:")
                                        print(f"   ✅ Successfully downloaded: {successful_downloads}/{len(urls)} files")
                                        print(f"   📂 Files saved to: {os.path.abspath(DOWNLOAD_DIR)}")
                                    else:
                                        print("   ❌ list_cloud didn't return any URLs")
                                        raise Exception("Both explore and list methods failed to return downloadable URLs")
                                except Exception as list_error:
                                    print(f"   ❌ list_cloud also failed: {list_error}")
                                    raise Exception("Both explore and list methods failed")
                                
                        except Exception as e:
                            print(f"   ❌ Could not get file list: {e}")
                            print("   💡 The torrent might be downloadable as a single archive")
                            print(f"   🌐 Try manually visiting: https://offcloud.com/cloud/download/{request_id}")
                            print(f"   📖 API docs suggest using explore/list endpoints for multi-file torrents")
                    else:
                        print("📄 Single file download")
                        download_url = f"https://offcloud.com/cloud/download/{request_id}"
                        filename = status_data.get('fileName', 'download')
                        local_path = os.path.join(DOWNLOAD_DIR, filename)
                        
                        if download_file(download_url, local_path, download_session):
                            print(f"🎉 File downloaded to: {os.path.abspath(local_path)}")
                    
                    break
                    
                elif current_status == "error":
                    print(f"   ❌ Download failed!")
                    if "error" in status_data:
                        print(f"   Error: {status_data['error']}")
                    break
                    
                elif current_status in ["downloading", "processing", "queued"]:
                    # Continue monitoring
                    time.sleep(10)  # Check every 10 seconds
                    
                else:
                    print(f"   ⚠️  Unexpected status: {current_status}")
                    time.sleep(5)
                    
            except TemporaryError:
                print("   ⚠️  Temporary error, retrying in 30 seconds...")
                time.sleep(30)
            except KeyboardInterrupt:
                print("\n🛑 Download monitoring cancelled by user")
                print(f"   Request ID: {request_id}")
                print("   You can check status later with cloud_status()")
                break
                
    except AuthError:
        print("❌ Authentication failed!")
        print("   Please check your API key")
        
    except FeatureNotAvailableError as e:
        print(f"❌ Feature not available: {e.feature}")
        print("   This might require a premium account")
        
    except RateLimitError:
        print("❌ Rate limit exceeded!")
        print("   Please wait before making more requests")
        
    except OffcloudError as e:
        print(f"❌ Offcloud API error: {e}")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()