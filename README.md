# Auto-Clean Downloads

A production-ready Python script to automatically organize and clean your Downloads folder. Categorizes files, removes temporary files, detects duplicates, and optionally merges PDFs.

## Features

**Smart Categorization** - Automatically sorts files into organized folders:
- Images (jpg, png, gif, etc.)
- Documents (doc, txt, rtf, etc.)
- PDFs
- Archives (zip, rar, 7z, etc.)
- Installers (exe, msi, dmg, etc.)
- Video (mp4, avi, mkv, etc.)
- Audio (mp3, wav, flac, etc.)
- Code (py, js, java, etc.)
- Others (everything else)

**Temp File Cleanup** - Removes incomplete downloads and temporary files (.crdownload, .part, .tmp, .partial)

**Duplicate Detection** - Uses SHA-256 hashing to find and move duplicate files to a separate folder (no data loss)

**PDF Merging** - Optionally merge all PDFs into a single file (requires pypdf)

**Undo Support** - Best-effort reversal of cleanup operations using history tracking

**Dry Run Mode** - Preview all changes before applying them

## Installation

1. Clone or download this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Make the script executable (Linux/Mac):

```bash
chmod +x auto_clean_downloads.py
```

## Usage

### Basic Usage

Clean your default Downloads folder:
```bash
python auto_clean_downloads.py
```

### Preview Changes (Dry Run)

See what would happen without making any changes:
```bash
python auto_clean_downloads.py --dry-run
```

### Custom Source Folder

Clean a specific folder:
```bash
python auto_clean_downloads.py --path ~/MyDownloads
```

### Custom Target Folder

Organize files into a specific location:
```bash
python auto_clean_downloads.py --target ~/Organized
```

### Merge PDFs

Organize files and merge all PDFs into one:
```bash
python auto_clean_downloads.py --merge-pdfs
```

### Undo Last Cleanup

Reverse the last cleanup operation:
```bash
python auto_clean_downloads.py --undo
```

### Verbose Output

Show detailed progress information:
```bash
python auto_clean_downloads.py --verbose
```

### Skip Specific Operations

Skip temporary file cleanup:
```bash
python auto_clean_downloads.py --no-temp-clean
```

Skip duplicate detection:
```bash
python auto_clean_downloads.py --no-duplicates
```

## Command-Line Options

| Option | Description |
|--------|-------------|
| `--path PATH` | Source folder to clean (default: ~/Downloads) |
| `--target PATH` | Target folder for organized files (default: <source>/Cleaned) |
| `--dry-run` | Preview changes without actually moving files |
| `--no-temp-clean` | Skip removal of temporary files |
| `--no-duplicates` | Skip duplicate detection |
| `--merge-pdfs` | Merge all PDF files into one (requires pypdf) |
| `--undo` | Undo the last cleanup operation |
| `--verbose`, `-v` | Show detailed progress information |

## How It Works

1. **Temp File Cleanup**: Scans for and removes incomplete downloads (.crdownload, .part, .tmp, .partial)

2. **Duplicate Detection**: 
   - Calculates SHA-256 hash for each file
   - Identifies files with identical content
   - Keeps the first occurrence, moves duplicates to `Cleaned/Duplicates`

3. **File Categorization**:
   - Analyzes file extensions
   - Creates category folders in `Cleaned/` directory
   - Moves files to appropriate categories
   - Handles filename conflicts automatically

4. **PDF Merging** (optional):
   - Combines all PDFs in the PDFs folder
   - Creates a timestamped merged file
   - Removes original PDFs after successful merge

5. **History Tracking**:
   - Records all operations in `.cleanup_history.json`
   - Enables undo functionality
   - Tracks timestamps and file paths

## Output Structure

After running the script, your Downloads folder will contain:

```
Downloads/
├── Cleaned/
│   ├── Images/
│   ├── Documents/
│   ├── PDFs/
│   ├── Archives/
│   ├── Installers/
│   ├── Video/
│   ├── Audio/
│   ├── Code/
│   ├── Others/
│   └── Duplicates/
└── .cleanup_history.json
```

## Example Output

```
🧹 Auto-Clean Downloads
Source: /home/user/Downloads
Target: /home/user/Downloads/Cleaned

=== Cleaning Temporary Files ===
Removing temp file: document.pdf.crdownload
Removing temp file: video.mp4.part

=== Scanning for Duplicates ===
Found 2 duplicates:
  [1] photo.jpg
  [2] photo (1).jpg
Moving duplicate: photo (1).jpg

=== Categorizing Files ===
Categorizing report.pdf -> PDFs
Categorizing vacation.jpg -> Images
Categorizing installer.exe -> Installers

==================================================
CLEANUP SUMMARY
==================================================
Files categorized:     15
Temp files removed:    2
Duplicates moved:      1
Errors encountered:    0
==================================================
```

## Safety Features

- **No Data Loss**: Duplicates are moved, not deleted
- **Conflict Handling**: Automatically renames files if names conflict
- **Dry Run Mode**: Preview all changes before applying
- **Undo Support**: Reverse operations using history tracking
- **Error Handling**: Gracefully handles permission errors and missing files
- **History Logging**: All operations are recorded with timestamps

## Requirements

- Python 3.6+
- pypdf (optional, for PDF merging)

## Troubleshooting

### PDF Merging Not Working

If you see a message about pypdf not being installed:
```bash
pip install pypdf
```

### Permission Errors

Make sure you have read/write permissions for the source and target folders.

### Undo Not Working

The undo feature can only reverse file moves, not deletions. Temporary files that were deleted cannot be restored.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

## License

MIT License - feel free to use this script for personal or commercial projects.

## Author

Created by shreya for keeping Downloads folders organized and clutter-free.
