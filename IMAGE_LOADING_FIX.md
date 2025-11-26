# Image Loading Issue - Investigation & Fix

## Problem Description
Some images in the stitched table were not displaying, showing as "Image" placeholders instead of actual thumbnails.

## Root Cause Analysis

### Investigation Findings:
1. **Images ARE being downloaded** during the extraction process (lines 1009-1093 in app.py)
2. **Images ARE being saved** to the correct location: `outputs/{session_id}/{file_id}/imgs/`
3. **The issue**: Some images were failing to download due to:
   - **Timeout issues**: Original timeout was only 30 seconds
   - **No retry logic**: If a download failed, it was permanently lost
   - **Connection errors**: Network issues could cause failures
   - **URL replacement bug**: Image URLs were being replaced in HTML even when downloads failed

### Key Problems:
1. **Short timeout (30s)**: Large images or slow connections would timeout
2. **No retries**: Single failure = permanent loss
3. **Premature URL replacement**: URLs were replaced before verifying successful download
4. **No verification**: No check if downloaded file actually exists and has content

## Solution Implemented

### Enhanced Image Download Logic:

#### 1. **Increased Timeout**
- Changed from 30 seconds to **60 seconds**
- Uses streaming download for large images

#### 2. **Retry Logic**
- **3 retry attempts** for each image
- Exponential backoff (1s, 2s delays between retries)
- Separate retry handling for different error types:
  - Timeout errors: 2-second delay
  - Connection errors: 2-second delay
  - HTTP errors: 1-second delay

#### 3. **Download Verification**
- Tracks successfully downloaded images in a dictionary
- Verifies file exists AND has content (size > 0)
- Only replaces URLs for **successfully downloaded** images

#### 4. **Chunked Download**
```python
for chunk in img_response.iter_content(chunk_size=8192):
    if chunk:
        img_file.write(chunk)
```
- Handles large images better
- Prevents memory issues

#### 5. **Better Logging**
- Logs each download attempt
- Shows success/failure with ✓/✗ symbols
- Shows file size for successful downloads
- Summary at end: "Downloaded X/Y images successfully"

### Code Changes:

**Before:**
```python
img_response = requests.get(img_url, timeout=30)
if img_response.status_code == 200:
    # Save and replace URL
```

**After:**
```python
successfully_downloaded_images = {}

for attempt in range(max_retries):
    img_response = requests.get(img_url, timeout=60, stream=True)
    if img_response.status_code == 200:
        # Save in chunks
        # Verify file exists
        if os.path.exists(local_img_path) and os.path.getsize(local_img_path) > 0:
            successfully_downloaded_images[img_path] = local_url
            break
```

## Benefits

1. **Higher success rate**: Retry logic catches transient failures
2. **Better reliability**: Longer timeout handles slow connections
3. **No broken links**: Only replaces URLs for successful downloads
4. **Better debugging**: Detailed logs show exactly what happened
5. **Memory efficient**: Streaming download for large images

## Testing Recommendations

1. **Test with slow connection**: Verify retry logic works
2. **Test with large images**: Verify streaming download works
3. **Test with mixed success/failure**: Verify only successful images show
4. **Check logs**: Verify summary shows correct counts

## Expected Behavior After Fix

- All successfully downloaded images will display correctly
- Failed images will keep original URL (or show as broken)
- Logs will show: "Image download summary: X/Y images downloaded successfully"
- Response will include: `images_downloaded` and `total_images` counts

## Session Cleanup - Not the Issue

The investigation confirmed that **session cleanup is NOT aggressive**:
- Images are downloaded DURING extraction (not after)
- Images are saved to session-specific directories
- Session cleanup only happens on explicit user action or after 24 hours
- The stitching function doesn't delete any files

## Monitoring

Check server logs for:
```
✓ Downloaded image: [path] -> [local_path] (X bytes)
✗ Failed to download image after 3 attempts: [url]
Image download summary: X/Y images downloaded successfully
```
