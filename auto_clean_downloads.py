#!/usr/bin/env python3
"""
Auto-Clean Downloads - Organize and clean your Downloads folder automatically.
"""

import os
import sys
import json
import shutil
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional

# File categories mapping
CATEGORIES = {
    'Images': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico', '.tiff', '.heic'},
    'Documents': {'.doc', '.docx', '.txt', '.rtf', '.odt', '.pages', '.tex', '.wpd', '.wps'},
    'PDFs': {'.pdf'},
    'Archives': {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso', '.dmg'},
    'Installers': {'.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm', '.appimage'},
    'Video': {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg'},
    'Audio': {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus'},
    'Code': {'.py', '.js', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss', '.json', '.xml', '.yaml', '.yml', '.sh', '.bat', '.ps1'},
}

TEMP_EXTENSIONS = {'.crdownload', '.part', '.tmp', '.partial', '.download', '.temp'}

HISTORY_FILE = '.cleanup_history.json'


class DownloadsCleaner:
    def __init__(self, source_path: Path, target_path: Path, dry_run: bool = False,
                 no_temp_clean: bool = False, no_duplicates: bool = False,
                 merge_pdfs: bool = False, verbose: bool = False):
        self.source_path = source_path
        self.target_path = target_path
        self.dry_run = dry_run
        self.no_temp_clean = no_temp_clean
        self.no_duplicates = no_duplicates
        self.merge_pdfs = merge_pdfs
        self.verbose = verbose
        
        self.stats = {
            'categorized': 0,
            'temp_removed': 0,
            'duplicates_found': 0,
            'pdfs_merged': 0,
            'errors': 0
        }
        
        self.history: List[Dict] = []
        self.file_hashes: Dict[str, List[Path]] = defaultdict(list)
    
    def log(self, message: str, force: bool = False):
        """Print message if verbose mode is enabled or force is True."""
        if self.verbose or force:
            print(message)
    
    def calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            self.log(f"Error hashing {file_path}: {e}")
            return ""
    
    def get_category(self, file_path: Path) -> str:
        """Determine the category of a file based on its extension."""
        ext = file_path.suffix.lower()
        for category, extensions in CATEGORIES.items():
            if ext in extensions:
                return category
        return 'Others'
    
    def move_file(self, source: Path, destination: Path) -> bool:
        """Move a file from source to destination, handling conflicts."""
        try:
            if destination.exists():
                # Handle name conflict
                base = destination.stem
                ext = destination.suffix
                counter = 1
                while destination.exists():
                    destination = destination.parent / f"{base}_{counter}{ext}"
                    counter += 1
            
            if not self.dry_run:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(destination))
            
            self.history.append({
                'action': 'move',
                'source': str(source),
                'destination': str(destination),
                'timestamp': datetime.now().isoformat()
            })
            
            return True
        except Exception as e:
            self.log(f"Error moving {source} to {destination}: {e}", force=True)
            self.stats['errors'] += 1
            return False
    
    def remove_file(self, file_path: Path) -> bool:
        """Remove a file."""
        try:
            if not self.dry_run:
                file_path.unlink()
            
            self.history.append({
                'action': 'delete',
                'source': str(file_path),
                'timestamp': datetime.now().isoformat()
            })
            
            return True
        except Exception as e:
            self.log(f"Error removing {file_path}: {e}", force=True)
            self.stats['errors'] += 1
            return False

    def clean_temp_files(self):
        """Remove temporary and partial download files."""
        if self.no_temp_clean:
            return
        
        self.log("\n=== Cleaning Temporary Files ===")
        for file_path in self.source_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in TEMP_EXTENSIONS:
                self.log(f"Removing temp file: {file_path.name}")
                if self.remove_file(file_path):
                    self.stats['temp_removed'] += 1
    
    def find_duplicates(self):
        """Find duplicate files by comparing SHA-256 hashes."""
        if self.no_duplicates:
            return
        
        self.log("\n=== Scanning for Duplicates ===")
        files = [f for f in self.source_path.iterdir() if f.is_file()]
        
        for file_path in files:
            if file_path.suffix.lower() in TEMP_EXTENSIONS:
                continue
            
            file_hash = self.calculate_hash(file_path)
            if file_hash:
                self.file_hashes[file_hash].append(file_path)
        
        # Process duplicates
        for file_hash, file_list in self.file_hashes.items():
            if len(file_list) > 1:
                # Keep the first file, move others to Duplicates
                self.log(f"Found {len(file_list)} duplicates:")
                for i, file_path in enumerate(file_list):
                    self.log(f"  [{i+1}] {file_path.name}")
                
                for duplicate in file_list[1:]:
                    dest = self.target_path / 'Duplicates' / duplicate.name
                    self.log(f"Moving duplicate: {duplicate.name}")
                    if self.move_file(duplicate, dest):
                        self.stats['duplicates_found'] += 1
    
    def categorize_files(self):
        """Categorize and move files to appropriate folders."""
        self.log("\n=== Categorizing Files ===")
        files = [f for f in self.source_path.iterdir() if f.is_file()]
        
        for file_path in files:
            if file_path.suffix.lower() in TEMP_EXTENSIONS:
                continue
            
            category = self.get_category(file_path)
            dest = self.target_path / category / file_path.name
            
            self.log(f"Categorizing {file_path.name} -> {category}")
            if self.move_file(file_path, dest):
                self.stats['categorized'] += 1
    
    def merge_pdf_files(self):
        """Merge all PDF files in the PDFs folder into a single file."""
        if not self.merge_pdfs:
            return
        
        try:
            from pypdf import PdfMerger
        except ImportError:
            print("\n⚠️  pypdf not installed. To enable PDF merging, run:")
            print("    pip install pypdf")
            return
        
        pdf_folder = self.target_path / 'PDFs'
        if not pdf_folder.exists():
            return
        
        pdf_files = sorted(pdf_folder.glob('*.pdf'))
        if len(pdf_files) < 2:
            self.log("Not enough PDFs to merge (need at least 2)")
            return
        
        self.log(f"\n=== Merging {len(pdf_files)} PDF files ===")
        
        try:
            merger = PdfMerger()
            for pdf in pdf_files:
                self.log(f"Adding: {pdf.name}")
                if not self.dry_run:
                    merger.append(str(pdf))
            
            output_name = f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_path = pdf_folder / output_name
            
            if not self.dry_run:
                merger.write(str(output_path))
                merger.close()
                
                # Remove original PDFs after successful merge
                for pdf in pdf_files:
                    pdf.unlink()
            
            self.history.append({
                'action': 'merge_pdfs',
                'files': [str(p) for p in pdf_files],
                'output': str(output_path),
                'timestamp': datetime.now().isoformat()
            })
            
            self.stats['pdfs_merged'] = len(pdf_files)
            self.log(f"✓ Merged into: {output_name}", force=True)
        
        except Exception as e:
            self.log(f"Error merging PDFs: {e}", force=True)
            self.stats['errors'] += 1
    
    def save_history(self):
        """Save cleanup history to JSON file."""
        if self.dry_run or not self.history:
            return
        
        history_path = self.source_path / HISTORY_FILE
        
        try:
            existing_history = []
            if history_path.exists():
                with open(history_path, 'r') as f:
                    existing_history = json.load(f)
            
            existing_history.append({
                'session': datetime.now().isoformat(),
                'operations': self.history,
                'stats': self.stats
            })
            
            with open(history_path, 'w') as f:
                json.dump(existing_history, f, indent=2)
            
            self.log(f"\n✓ History saved to {history_path}")
        
        except Exception as e:
            self.log(f"Error saving history: {e}", force=True)
    
    def print_summary(self):
        """Print summary of operations."""
        mode = "[DRY RUN] " if self.dry_run else ""
        print(f"\n{'='*50}")
        print(f"{mode}CLEANUP SUMMARY")
        print(f"{'='*50}")
        print(f"Files categorized:     {self.stats['categorized']}")
        print(f"Temp files removed:    {self.stats['temp_removed']}")
        print(f"Duplicates moved:      {self.stats['duplicates_found']}")
        if self.merge_pdfs:
            print(f"PDFs merged:           {self.stats['pdfs_merged']}")
        print(f"Errors encountered:    {self.stats['errors']}")
        print(f"{'='*50}")
        
        if self.dry_run:
            print("\n💡 This was a dry run. No files were actually moved.")
            print("   Run without --dry-run to apply changes.")
    
    def run(self):
        """Execute the cleanup process."""
        if not self.source_path.exists():
            print(f"❌ Error: Source path does not exist: {self.source_path}")
            sys.exit(1)
        
        print(f"\n🧹 Auto-Clean Downloads")
        print(f"Source: {self.source_path}")
        print(f"Target: {self.target_path}")
        if self.dry_run:
            print("Mode: DRY RUN (no changes will be made)")
        print()
        
        self.clean_temp_files()
        self.find_duplicates()
        self.categorize_files()
        self.merge_pdf_files()
        self.save_history()
        self.print_summary()


def undo_cleanup(source_path: Path, dry_run: bool = False, verbose: bool = False):
    """Attempt to undo the last cleanup operation."""
    history_path = source_path / HISTORY_FILE
    
    if not history_path.exists():
        print("❌ No cleanup history found. Cannot undo.")
        sys.exit(1)
    
    try:
        with open(history_path, 'r') as f:
            history = json.load(f)
        
        if not history:
            print("❌ No cleanup sessions found in history.")
            sys.exit(1)
        
        last_session = history[-1]
        operations = last_session['operations']
        
        print(f"\n🔄 Undoing cleanup from: {last_session['session']}")
        print(f"Operations to reverse: {len(operations)}")
        
        if dry_run:
            print("\n[DRY RUN] Would reverse the following operations:")
        
        success_count = 0
        error_count = 0
        
        # Reverse operations in reverse order
        for op in reversed(operations):
            action = op['action']
            
            if action == 'move':
                source = Path(op['destination'])
                dest = Path(op['source'])
                
                if verbose or dry_run:
                    print(f"  Move: {source} -> {dest}")
                
                if not dry_run:
                    try:
                        if source.exists():
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.move(str(source), str(dest))
                            success_count += 1
                        else:
                            if verbose:
                                print(f"    ⚠️  File not found: {source}")
                            error_count += 1
                    except Exception as e:
                        print(f"    ❌ Error: {e}")
                        error_count += 1
                else:
                    success_count += 1
            
            elif action == 'delete':
                if verbose or dry_run:
                    print(f"  Cannot restore deleted file: {op['source']}")
                error_count += 1
        
        print(f"\n{'='*50}")
        print(f"UNDO SUMMARY")
        print(f"{'='*50}")
        print(f"Successfully reversed: {success_count}")
        print(f"Could not reverse:     {error_count}")
        print(f"{'='*50}")
        
        if not dry_run:
            # Remove the last session from history
            history.pop()
            with open(history_path, 'w') as f:
                json.dump(history, f, indent=2)
            print("\n✓ History updated.")
        else:
            print("\n💡 This was a dry run. No files were actually moved.")
    
    except Exception as e:
        print(f"❌ Error reading history: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Auto-Clean Downloads - Organize and clean your Downloads folder',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Clean default Downloads folder
  %(prog)s --dry-run                # Preview changes without applying
  %(prog)s --path ~/MyDownloads     # Clean custom folder
  %(prog)s --merge-pdfs             # Merge all PDFs after organizing
  %(prog)s --undo                   # Undo last cleanup operation
  %(prog)s --verbose                # Show detailed progress
        """
    )
    
    parser.add_argument('--path', type=str, default=None,
                        help='Source folder to clean (default: ~/Downloads)')
    parser.add_argument('--target', type=str, default=None,
                        help='Target folder for organized files (default: <source>/Cleaned)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without actually moving files')
    parser.add_argument('--no-temp-clean', action='store_true',
                        help='Skip removal of temporary files')
    parser.add_argument('--no-duplicates', action='store_true',
                        help='Skip duplicate detection')
    parser.add_argument('--merge-pdfs', action='store_true',
                        help='Merge all PDF files into one (requires pypdf)')
    parser.add_argument('--undo', action='store_true',
                        help='Undo the last cleanup operation')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed progress information')
    
    args = parser.parse_args()
    
    # Determine source path
    if args.path:
        source_path = Path(args.path).expanduser().resolve()
    else:
        source_path = Path.home() / 'Downloads'
    
    # Handle undo operation
    if args.undo:
        undo_cleanup(source_path, dry_run=args.dry_run, verbose=args.verbose)
        return
    
    # Determine target path
    if args.target:
        target_path = Path(args.target).expanduser().resolve()
    else:
        target_path = source_path / 'Cleaned'
    
    # Create and run cleaner
    cleaner = DownloadsCleaner(
        source_path=source_path,
        target_path=target_path,
        dry_run=args.dry_run,
        no_temp_clean=args.no_temp_clean,
        no_duplicates=args.no_duplicates,
        merge_pdfs=args.merge_pdfs,
        verbose=args.verbose
    )
    
    cleaner.run()


if __name__ == '__main__':
    main()
