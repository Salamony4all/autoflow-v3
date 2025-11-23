# Automatic Brand File Synchronization

## What Was Fixed

Previously, when scraping brand data, the system only saved to `brands_dynamic.json` but NOT to the individual brand files (e.g., `OTTIMO_budgetary.json`). This meant you had to manually sync the files every time.

## New Behavior ✅

Now, when you scrape a brand, the system **automatically saves to BOTH files**:

1. **`brands_data/brands_dynamic.json`** - Master file with all brands
2. **`brands_data/{BRAND}_{tier}.json`** - Individual brand file (e.g., `OTTIMO_budgetary.json`)

## How It Works

### New Function Added: `save_individual_brand_file()`

This function is called automatically after every successful scrape. It:

- Creates/updates the individual brand file (e.g., `OTTIMO_budgetary.json`)
- Saves all scraped data including:
  - `category_tree` (hierarchical product structure)
  - `categories` (legacy format support)
  - `total_products` count
  - `includes_descriptions` flag
  - Timestamps and metadata

### Integration Point

```python
# In scrape_and_add_brand() function (line ~2576)
# Save to brands_dynamic.json
with open(brands_file, 'w', encoding='utf-8') as f:
    json.dump(brands_data, f, indent=2, ensure_ascii=False)

# ✅ NEW: Also save to individual brand file
save_individual_brand_file(brand_name, website, country, tier, scraped_data)
```

## What This Means for You

### ✅ No Manual Sync Needed Anymore!

When you scrape a brand using the "Add Brand" function:

1. Click "Add Brand" in the UI
2. Enter brand details and select scraping method
3. Click "Scrape and Add"
4. **BOTH files are automatically updated** ✅

### Frontend Immediately Sees New Data

The frontend dropdowns for:
- Brand selection
- Category selection
- Subcategory selection
- Model/Product selection

...will all immediately reflect the newly scraped data because they read from the individual brand files (`{BRAND}_{tier}.json`).

## Files Modified

- **`app.py`**:
  - Added `save_individual_brand_file()` function (line 3367-3415)
  - Modified `scrape_and_add_brand()` to call the new function (line 2576)

## No Action Required

This is now handled automatically in the background. Future scraping operations will maintain synchronization between both files automatically.

## Notes

- The individual brand file is updated **after** the master file
- If the individual file update fails, scraping still succeeds (logged as error)
- Existing data in individual files is completely replaced with new scraped data
- All metadata (timestamps, product counts, descriptions flag) is preserved

---

**Created**: 2025-11-22  
**Purpose**: Documentation for automatic brand file synchronization feature

