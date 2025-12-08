# Railway Volume Paths - Quick Reference

## Volume Mount Paths for Railway

When creating volumes in Railway, use these mount paths:

### 1. Brands Data (REQUIRED)
```
Mount Path: /data/brands_data
Environment Variable: BRANDS_DATA_PATH=/data/brands_data
Purpose: Stores brand JSON files (OTTIMO, Narbutas, SEDUS, etc.)
Size: ~50MB minimum
```

### 2. Uploads (RECOMMENDED)
```
Mount Path: /data/uploads
Environment Variable: UPLOAD_FOLDER=/data/uploads
Purpose: User uploaded PDF/Excel files
Size: 1GB+ recommended
```

### 3. Outputs (RECOMMENDED)
```
Mount Path: /data/outputs
Environment Variable: OUTPUT_FOLDER=/data/outputs
Purpose: Generated MAS, presentations, and processed files
Size: 2GB+ recommended
```

## How to Create Volumes in Railway

1. Open your Railway project
2. Click on your service
3. Go to **Variables** tab
4. Scroll to **Volumes** section
5. Click **+ New Volume**
6. Enter mount path (e.g., `/data/brands_data`)
7. Click **Add**
8. Repeat for each volume

## After Creating Volumes

Set these environment variables in Railway:

```bash
BRANDS_DATA_PATH=/data/brands_data
UPLOAD_FOLDER=/data/uploads
OUTPUT_FOLDER=/data/outputs
```

## Brand Files Included

The following brand files will be automatically copied to the volume:
- brands_dynamic.json
- BT_mid_range.json
- LAS_mid_range.json
- MARELLI_high_end.json
- MARTEX_high_end.json
- NARBUTAS_mid_range.json
- NURUS_mid_range.json
- OFIFRAN_mid_range.json
- OTTIMO_budgetary.json
- SEDUS_mid_range.json

Total: 10 brand files covering budgetary, mid-range, and high-end tiers.

## Verification

After deployment, check logs for:
```
INFO - Brands data directory configured: /data/brands_data
INFO - Brand files available in /data/brands_data: 10 files
```

## Important Notes

- **Without volumes**: Data will be lost on each deployment
- **With volumes**: Data persists across deployments and restarts
- Volumes are automatically backed up by Railway
- You can access volume data via Railway CLI or dashboard
