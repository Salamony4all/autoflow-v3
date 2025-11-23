# Contributing to Questemate

Thank you for your interest in contributing to Questemate! This document provides guidelines and instructions for contributing to the project.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Documentation](#documentation)

---

## 🤝 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. Please be respectful and constructive in all interactions.

### Expected Behavior

- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Git
- Text editor (VS Code recommended)
- Basic knowledge of Flask and JavaScript

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/BOQ-platform1.git
   cd BOQ-platform1
   ```
3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/Salamony4all/BOQ-platform1.git
   ```

---

## 💻 Development Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file (optional):
```
FLASK_ENV=development
FLASK_DEBUG=1
API_TOKEN=your_test_token
```

### 4. Run Development Server

```bash
python app.py
```

---

## 📁 Project Structure

```
quque1/
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
├── QUICK_START.md           # Quick start guide
├── CHANGELOG.md             # Version history
├── CONTRIBUTING.md          # This file
│
├── templates/
│   └── index.html           # Main UI template
│
├── static/
│   ├── css/                 # Stylesheets (inline in index.html)
│   ├── js/
│   │   └── table_manager.js # Table manipulation logic
│   └── images/              # Static images
│
├── utils/
│   ├── pdf_processor.py     # PDF extraction
│   ├── costing_engine.py    # Costing calculations
│   ├── offer_generator.py   # PDF generation
│   ├── value_engineering.py # Alternative suggestions
│   └── brand_scraper.py     # Web scraping
│
├── uploads/                 # Temporary uploads (gitignored)
├── outputs/                 # Generated files (gitignored)
└── brands_data/            # Brand catalog data
```

---

## 📝 Coding Standards

### Python Style Guide

Follow [PEP 8](https://pep8.org/) guidelines:

```python
# Good
def process_table_data(file_id, settings):
    """Process extracted table data with given settings."""
    result = extract_data(file_id)
    return apply_settings(result, settings)

# Bad
def processTableData(fileId,settings):
    result=extractData(fileId)
    return applySettings(result,settings)
```

**Key Points:**
- Use 4 spaces for indentation
- Max line length: 100 characters
- Use descriptive variable names
- Add docstrings to functions
- Use type hints where appropriate

### JavaScript Style Guide

Follow modern ES6+ standards:

```javascript
// Good
async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        return await response.json();
    } catch (error) {
        console.error('Upload failed:', error);
        throw error;
    }
}

// Bad
function uploadFile(file) {
    var formData = new FormData()
    formData.append('file',file)
    fetch('/upload',{method:'POST',body:formData}).then(function(response){
        return response.json()
    })
}
```

**Key Points:**
- Use `const` and `let`, avoid `var`
- Use arrow functions for callbacks
- Use async/await over promises
- Add error handling
- Use meaningful variable names

### HTML/CSS Style Guide

```html
<!-- Good -->
<div class="progress-bar" id="uploadProgress">
    <div class="progress-fill" id="uploadProgressFill">0%</div>
</div>

<!-- Bad -->
<div class=progress-bar id=uploadProgress><div class=progress-fill id=uploadProgressFill>0%</div></div>
```

**Key Points:**
- Use semantic HTML5 elements
- Indent nested elements
- Use kebab-case for classes
- Use camelCase for IDs
- Add ARIA labels for accessibility

---

## 📦 Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

### Examples

```
feat(extraction): add empty row filtering

- Implement backend filtering in app.py
- Add frontend filtering in table_manager.js
- Remove rows with only whitespace
- Log filtered row count

Closes #123
```

```
fix(ui): resolve duplicate button issue

- Update button cleanup logic
- Add robust button identification
- Remove invalid CSS selectors

Fixes #456
```

---

## 🔄 Pull Request Process

### Before Submitting

1. **Update your fork**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Write clean, documented code
   - Follow coding standards
   - Add tests if applicable

4. **Test thoroughly**
   - Test on your local machine
   - Check for console errors
   - Verify all features work

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat(scope): description"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

### Submitting the PR

1. Go to GitHub and create a Pull Request
2. Fill out the PR template:
   - **Title**: Clear, descriptive title
   - **Description**: What changes were made and why
   - **Testing**: How you tested the changes
   - **Screenshots**: If UI changes, include before/after
   - **Related Issues**: Link to related issues

3. Wait for review
   - Address reviewer comments
   - Make requested changes
   - Push updates to the same branch

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings or errors
- [ ] Tested on local machine
- [ ] Screenshots included (if UI changes)

---

## 🧪 Testing

### Manual Testing

1. **Test the happy path**
   - Upload a valid PDF
   - Verify extraction works
   - Check table editing
   - Generate PDF offer

2. **Test edge cases**
   - Large files (>20MB)
   - Multi-page documents
   - Files with images
   - Invalid file formats

3. **Test error handling**
   - Invalid API token
   - Network errors
   - Session timeout
   - Corrupted files

### Browser Testing

Test on:
- ✅ Chrome (latest)
- ✅ Firefox (latest)
- ✅ Edge (latest)
- ⚠️ Safari (if available)

### Logging

Add logging for debugging:

```python
import logging
logger = logging.getLogger(__name__)

logger.info('Processing file: %s', file_id)
logger.warning('Large file detected: %s MB', file_size_mb)
logger.error('Extraction failed: %s', error_message)
```

---

## 📚 Documentation

### Code Documentation

**Python:**
```python
def stitch_tables(file_id: str, settings: dict) -> dict:
    """
    Stitch tables from multiple pages into a single table.
    
    Args:
        file_id: Unique identifier for the uploaded file
        settings: Dictionary of extraction settings
        
    Returns:
        Dictionary containing stitched HTML and metadata
        
    Raises:
        ValueError: If file_id is invalid
        RuntimeError: If stitching fails
    """
    pass
```

**JavaScript:**
```javascript
/**
 * Upload file and extract tables automatically
 * @param {File} file - The file to upload
 * @returns {Promise<Object>} Upload result with file_id
 * @throws {Error} If upload fails
 */
async function uploadFile(file) {
    // Implementation
}
```

### README Updates

When adding features:
1. Update `README.md` with feature description
2. Add to "Features" section
3. Update "Quick Start" if needed
4. Add to `CHANGELOG.md`

---

## 🐛 Reporting Bugs

### Before Reporting

1. Check existing issues
2. Test on latest version
3. Gather error messages
4. Note steps to reproduce

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g., Windows 10]
- Browser: [e.g., Chrome 120]
- Python version: [e.g., 3.10]

**Additional context**
Any other relevant information.
```

---

## 💡 Feature Requests

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
What you want to happen.

**Describe alternatives you've considered**
Other solutions you've thought about.

**Additional context**
Mockups, examples, or references.
```

---

## 📞 Getting Help

- **Documentation**: Check README.md and QUICK_START.md
- **Issues**: Search existing GitHub issues
- **Discussions**: Start a discussion on GitHub
- **Email**: support@questemate.com

---

## 🏆 Recognition

Contributors will be:
- Listed in CHANGELOG.md
- Mentioned in release notes
- Added to contributors list

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to Questemate! 🎉**

*Every contribution, no matter how small, makes a difference.*
