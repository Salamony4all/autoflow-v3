# Railway Deployment Guide for Autoflow V3

## Prerequisites
- Railway account (https://railway.app)
- GitHub repository connected to Railway

## Quick Deploy Steps

### 1. Create New Project in Railway
- Go to Railway Dashboard
- Click "New Project"
- Select "Deploy from GitHub repo"
- Choose: Salamony4all/autoflow-v3

### 2. Configure Environment Variables
In Railway project settings, add these environment variables:

```bash
# Required
PORT=5000
SECRET_KEY=your-secure-random-secret-key-here

# Optional - API Configuration
PP_STRUCTURE_API_URL=https://wfk3ide9lcd0x0k9.aistudio-hub.baidu.com/layout-parsing
PP_STRUCTURE_TOKEN=031c87b3c44d16aa4adf6928bcfa132e23393afc

# Volume Configuration (if using Railway Volume)
BRANDS_DATA_PATH=/data/brands_data

# Flask Configuration
FLASK_DEBUG=False
```

### 3. Create Railway Volume for Persistent Storage

**IMPORTANT: To preserve brand data and user uploads, create a Railway Volume:**

1. In your Railway project, go to "Variables" tab
2. Click "New Volume"
3. Create volume with these settings:
   - **Volume Name**: `brands-data-volume`
   - **Mount Path**: `/data/brands_data`
   
4. Set environment variable:
   ```
   BRANDS_DATA_PATH=/data/brands_data
   ```

**Volume Path Information:**
- **Mount Path for brands_data**: `/data/brands_data`
- **Mount Path for uploads** (optional): `/data/uploads`
- **Mount Path for outputs** (optional): `/data/outputs`

The application will automatically:
- Copy brand JSON files from the repository to the volume on first run
- Use the volume for all brand data operations
- Persist data across deployments

### 4. Deploy
Railway will automatically:
- Detect nixpacks.toml configuration
- Install system dependencies (LibreOffice, Tesseract, etc.)
- Install Python dependencies from requirements.txt
- Start the application with Gunicorn

### 5. Access Your Application
- Railway will provide a public URL like: `https://your-app.up.railway.app`
- The application will be running on the PORT specified by Railway

## Volume Configuration Details

### Recommended Volume Setup

Create **three volumes** for optimal data persistence:

1. **Brand Data Volume**
   - Mount Path: `/data/brands_data`
   - Environment Variable: `BRANDS_DATA_PATH=/data/brands_data`
   - Contains: Brand JSON files (OTTIMO, Narbutas, etc.)

2. **Uploads Volume** (Optional but Recommended)
   - Mount Path: `/data/uploads`
   - Environment Variable: `UPLOAD_FOLDER=/data/uploads`
   - Contains: User uploaded PDF/Excel files

3. **Outputs Volume** (Optional but Recommended)
   - Mount Path: `/data/outputs`
   - Environment Variable: `OUTPUT_FOLDER=/data/outputs`
   - Contains: Generated MAS, presentations, costed files

### Setting Up Volumes in Railway

1. Go to your Railway project
2. Click on your service
3. Navigate to "Variables" tab
4. Scroll down to "Volumes" section
5. Click "+ New Volume"
6. For each volume:
   - Enter the mount path (e.g., `/data/brands_data`)
   - Click "Add"

## Application Features

This application includes:
- PDF table extraction and processing
- Excel file processing
- Multi-budget costing system
- Brand database integration (10 brands)
- MAS (Material Approval Submission) generation
- Presentation generation (PPTX and PDF)
- Product enrichment with brand data
- Value engineering calculations

## System Dependencies (Auto-installed)

The following are automatically installed via nixpacks.toml:
- LibreOffice (for document conversion)
- Ghostscript (for PDF processing)
- Tesseract OCR (for text extraction)
- Poppler Utils (for PDF utilities)
- wkhtmltopdf (for HTML to PDF conversion)

## Monitoring

- Check logs in Railway dashboard under "Deployments"
- Application logs to both console and server.log file
- Health check endpoint: `/` (root path)

## Troubleshooting

### If deployment fails:
1. Check build logs for missing dependencies
2. Verify all environment variables are set
3. Ensure Python version compatibility (3.11+)

### If brand data is missing:
1. Verify `BRANDS_DATA_PATH` environment variable is set
2. Check volume is mounted correctly
3. Review logs for brand initialization messages

### If uploads don't persist:
1. Create volumes for uploads and outputs directories
2. Set appropriate environment variables

## Scaling

Gunicorn is configured with:
- 2 workers (adjust based on Railway plan)
- 120s timeout for long-running operations
- Automatic restart on failure

To adjust workers, modify railway.json or Procfile.

## Security Notes

- Never commit `.env` file with secrets
- Use Railway's environment variables for sensitive data
- SECRET_KEY should be a strong random string
- Consider setting FLASK_DEBUG=False in production

## Support

For issues:
- Check Railway logs
- Review application server.log
- Verify volume mounts and permissions
