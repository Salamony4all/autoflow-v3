# Questemate - Quick Start Guide

> Get up and running with Questemate in 5 minutes!

---

## 🎯 Prerequisites

Before you begin, ensure you have:

- ✅ Python 3.8 or higher installed
- ✅ pip (Python package manager)
- ✅ PP-StructureV3 API access token
- ✅ Modern web browser (Chrome, Firefox, Edge)

---

## 📦 Installation Steps

### Step 1: Download the Project

```bash
git clone https://github.com/Salamony4all/BOQ-platform1.git
cd BOQ-platform1
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
- Flask (web framework)
- pandas (data processing)
- PyMuPDF, pdfplumber (PDF handling)
- opencv-python (image processing)
- ReportLab (PDF generation)
- beautifulsoup4 (web scraping)
- And more... (see requirements.txt)

### Step 3: Configure API Token

1. Open `app.py` in a text editor
2. Find the line: `TOKEN = "your_token_here"`
3. Replace with your PP-StructureV3 API token:
   ```python
   TOKEN = "actual_token_from_baidu_aistudio"
   ```
4. Save the file

**Where to get the token:**
- File: `PP-STRUCTURE V3 API KEY.txt` (in project root)
- Or visit: Baidu AIStudio Platform

### Step 4: Run the Application

```bash
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * Debugger is active!
```

### Step 5: Access the Application

Open your browser and go to:
```
http://127.0.0.1:5000
```

You should see the Questemate landing page with four workflow cards.

---

## 🎬 Your First Extraction

### Workflow 1: Quote with Price List

**What you'll need:**
- A PDF file containing a Bill of Quantities (BOQ)
- Optionally: A price list (Excel or PDF)

**Steps:**

1. **Click "Quote with Price List"** on the landing page

2. **Upload Your File**
   - Click the upload area or drag & drop your PDF
   - Supported formats: PDF, XLSX, XLS, JPG, PNG
   - Max size: 50MB

3. **Watch the Progress**
   
   You'll see 7 detailed steps:
   - 📤 Step 1: Uploading file to server
   - ✅ Step 2: Upload complete, initializing extraction
   - 🤖 Step 3: Calling PP-StructureV3 API
   - 📊 Step 4: Processing extracted content
   - 🔍 Step 5: Detecting table structures
   - 🔗 Step 6: Stitching tables from multiple pages
   - 🎨 Step 7: Rendering interactive table

4. **Edit the Table**
   
   Once extraction completes:
   - ✏️ Click any cell to edit
   - ➕ Click green button to add row below
   - 🗑️ Click red button to delete row
   - 🖼️ Drag images between cells

5. **Apply Costing** (Optional)
   
   Click "💰 Costing" to add:
   - Net Margin (%)
   - Freight (%)
   - Customs (%)
   - Installation (%)
   - Exchange Rate
   - Additional Costs

6. **Generate Offer**
   
   Click "📄 Generate Offer" to create a professional PDF with:
   - Company branding
   - Formatted tables
   - VAT calculation
   - Terms and conditions

---

## 🎨 Understanding the Interface

### Main Sections

#### 1. **Upload & Extract Files** 📤
- Upload area with drag & drop
- Extraction settings panel
- Progress bar with detailed status
- File size and format validation

#### 2. **Extracted Tables** 📊
- Fully editable table view
- Add/delete row buttons
- Drag & drop images
- Alternating row colors
- Real-time updates

#### 3. **Costing** 💰
- Interactive sliders for each factor
- Real-time calculation preview
- Apply/reset buttons
- Visual feedback

#### 4. **Results & Export** 📥
- Download as Excel
- Generate PDF offer
- Create presentation
- Export MAS document

### Extraction Settings

Click "⚙️ Extraction Settings" to configure:

**Enabled by default:**
- ✅ Table Recognition (required)
- ✅ Seal Recognition
- ✅ Region Detection
- ✅ Format Block Content

**Disabled by default:**
- ☐ Formula Recognition (enable for math-heavy docs)
- ☐ Chart Recognition (enable for graphs)
- ☐ Visualize (Debug) (for troubleshooting)

**Tip:** Keep default settings for best results!

---

## 💡 Tips & Tricks

### For Best Results

1. **File Quality**
   - Use high-resolution PDFs (300 DPI or higher)
   - Ensure text is searchable (not scanned images)
   - Clear table borders improve accuracy

2. **Table Format**
   - Consistent column widths
   - Clear headers
   - Avoid merged cells when possible
   - One table per page works best

3. **File Size**
   - Keep files under 20MB for faster processing
   - Split large documents (50+ pages) into batches
   - Compress images before embedding

4. **Editing Tables**
   - Review extracted data before applying costs
   - Use Tab key to move between cells
   - Double-click to edit, click outside to save
   - Undo is not available - edit carefully!

5. **Costing Factors**
   - Start with small margins to test calculations
   - Verify totals after applying factors
   - Download Excel to keep a backup
   - Exchange rate applies to all amounts

---

## 🔧 Common Workflows

### Workflow 1: Simple BOQ Extraction

```
Upload PDF → Extract → Edit → Download Excel
```

**Time:** 2-5 minutes
**Use case:** Quick data extraction without pricing

### Workflow 2: Full Quotation

```
Upload PDF → Extract → Edit → Apply Costing → Generate Offer
```

**Time:** 5-10 minutes
**Use case:** Complete commercial offer with branding

### Workflow 3: Multi-Budget Comparison

```
Upload PDF → Extract → Select Products → Generate 3-Tier Offer
```

**Time:** 10-15 minutes
**Use case:** Budgetary, Mid-Range, High-End options

### Workflow 4: Presentation Creation

```
Upload PDF with Images → Extract → Generate PPTX
```

**Time:** 5-8 minutes
**Use case:** Client presentations with product showcase

---

## ❓ Troubleshooting

### Issue: "File not found" error

**Symptoms:** Error appears after successful extraction

**Solution:**
1. Refresh the browser page
2. Re-upload the file
3. Check if session expired (24-hour limit)

### Issue: Extraction takes too long

**Symptoms:** Progress stuck at "Calling API"

**Possible causes:**
- Large file size (>20MB)
- Slow internet connection
- API server busy

**Solutions:**
1. Wait 2-3 minutes (large files take time)
2. Check internet connection
3. Try splitting the PDF into smaller files
4. Reduce PDF resolution

### Issue: Empty rows between products

**Status:** ✅ Fixed in latest version

**If still occurring:**
1. Update to latest code
2. Clear browser cache
3. Refresh the page

### Issue: Duplicate add/remove buttons

**Status:** ✅ Fixed in latest version

**If still occurring:**
1. Update to latest code
2. Hard refresh (Ctrl+F5 or Cmd+Shift+R)

### Issue: API extraction fails

**Error message:** "Extraction failed: [error details]"

**Solutions:**
1. Check API token is correct in `app.py`
2. Verify file format is supported
3. Ensure file is not corrupted
4. Try a different file to isolate the issue
5. Check `server.log` for detailed errors

---

## 📊 Sample Files

### Test Files Included

The project includes sample files for testing:

1. **Sample BOQ** (in `test_files/` if available)
   - Multi-page table
   - Product images
   - Various column types

2. **Sample Price List**
   - Excel format
   - Multiple products
   - Unit prices

**Note:** If test files are not included, use your own BOQ documents.

---

## 🎓 Learning Path

### Beginner (Day 1)
1. Install and run the application
2. Upload a simple 1-page PDF
3. Edit the extracted table
4. Download as Excel

### Intermediate (Day 2-3)
1. Upload multi-page documents
2. Apply costing factors
3. Generate PDF offers
4. Customize extraction settings

### Advanced (Week 1)
1. Use multi-budget workflow
2. Integrate brand scraping
3. Generate presentations
4. Understand the codebase

---

## 🚀 Next Steps

After completing this quick start:

1. **Read the Full README**
   - Detailed feature documentation
   - Technical architecture
   - API integration details

2. **Explore Advanced Features**
   - Value engineering
   - Brand scraping
   - Custom templates

3. **Customize for Your Needs**
   - Modify branding (logo, colors)
   - Adjust costing factors
   - Add custom fields

4. **Contribute**
   - Report bugs on GitHub
   - Suggest features
   - Submit pull requests

---

## 📞 Getting Help

**Documentation:**
- `README.md` - Complete project documentation
- `PP-StructureV3_API_en documentation.txt` - API reference

**Support:**
- GitHub Issues: Report bugs and request features
- Email: support@questemate.com
- Logs: Check `server.log` for errors

---

## ✅ Checklist

Before you start using Questemate in production:

- [ ] Python 3.8+ installed
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] API token configured in `app.py`
- [ ] Application runs without errors
- [ ] Test extraction with sample file
- [ ] Costing factors tested and verified
- [ ] PDF generation works
- [ ] Browser cache cleared
- [ ] Backup strategy in place

---

**Ready to extract? Let's go! 🚀**

*For detailed documentation, see README.md*
*Last Updated: November 2025*
