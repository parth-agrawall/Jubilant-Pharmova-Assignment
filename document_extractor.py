#!/usr/bin/env python3
"""
Document Text Extractor Module
==============================

This module handles document text extraction using LlamaParse API.
Used specifically for RAG pipeline document processing.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import nest_asyncio

try:
    from llama_parse import LlamaParse
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Please install required packages:")
    print("pip install llama-parse nest-asyncio")
    sys.exit(1)

# Apply nest_asyncio for compatibility
nest_asyncio.apply()


class DocumentExtractor:
    """Document text extraction class using LlamaParse."""

    def __init__(self, api_key: str = "llx-0KzX07POPszi7vBhDxUeXu9sm6MxjjLlzzyDNheaw9R06ntt"):
        """
        Initialize the DocumentExtractor with LlamaParse API key.

        Args:
            api_key: LlamaParse API key
        """
        self.api_key = api_key

        # Initialize parser with compatible settings
        try:
            self.parser = LlamaParse(
                api_key=api_key,
                result_type="markdown",
                verbose=True,
                language="en",
                split_by_page=True,
                premium_mode=True,
            )
            print("✓ Parser initialized with premium mode")

        except Exception as e:
            if "Incompatible parsing modes" in str(e):
                print("⚠️  Parsing mode conflict detected. Trying with basic settings...")
                self.parser = LlamaParse(
                    api_key=api_key,
                    result_type="markdown",
                    verbose=True,
                    language="en",
                    split_by_page=True,
                )
                print("✓ Parser initialized with basic mode")
            else:
                raise e

    def get_supported_files(self, directory: str = ".") -> List[str]:
        """
        Get list of supported document files in the specified directory.

        Args:
            directory: Directory to search for files (default: current directory)

        Returns:
            List of supported file paths
        """
        supported_extensions = [
            '.pdf', '.docx', '.doc', '.pptx', '.ppt',
            '.xlsx', '.xls', '.txt', '.md', '.html', '.htm',
            '.png', '.jpg', '.jpeg'
        ]

        supported_files = []
        directory_path = Path(directory)

        if directory_path.exists() and directory_path.is_dir():
            for file_path in directory_path.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                    supported_files.append(str(file_path))

        return sorted(supported_files)

    def select_file_interactive(self) -> str:
        """
        Interactive file selection from available supported documents.

        Returns:
            Selected file path
        """
        print("\n📄 Document File Selection")
        print("=" * 40)
        print("Scanning for supported document files...")

        # Get files from current directory
        current_files = self.get_supported_files(".")

        # Also check common document directories if they exist
        common_dirs = ["Documents", "documents", "files", "Files", "data", "Data"]
        all_files = current_files.copy()

        for dir_name in common_dirs:
            if Path(dir_name).exists():
                dir_files = self.get_supported_files(dir_name)
                all_files.extend(dir_files)

        # Remove duplicates while preserving order
        seen = set()
        unique_files = []
        for file in all_files:
            if file not in seen:
                seen.add(file)
                unique_files.append(file)

        if not unique_files:
            print("❌ No supported document files found in current directory or common subdirectories.")
            print("\nSupported file types: PDF, DOCX, DOC, PPTX, PPT, XLSX, XLS, TXT, MD, HTML, PNG, JPG, JPEG")
            print("\nOptions:")
            print("1. Add files to current directory and restart")
            print("2. Enter file path manually")

            choice = input("\nChoose option (1 or 2): ").strip()
            if choice == "2":
                return self._get_manual_file_path()
            else:
                raise FileNotFoundError("No supported files available")

        print(f"\n📋 Found {len(unique_files)} supported document(s):")
        print("-" * 50)

        # Display files with numbers
        for i, file_path in enumerate(unique_files, 1):
            file_obj = Path(file_path)
            file_size = file_obj.stat().st_size
            size_str = self._format_file_size(file_size)
            print(f"  {i:2d}. {file_obj.name} ({size_str}) - {file_obj.parent}")

        print(f"\n  {len(unique_files) + 1:2d}. Enter custom file path")
        print(f"  {len(unique_files) + 2:2d}. Cancel")

        # Get user selection
        while True:
            try:
                choice = input(f"\nSelect file (1-{len(unique_files) + 2}): ").strip()
                choice_num = int(choice)

                if 1 <= choice_num <= len(unique_files):
                    selected_file = unique_files[choice_num - 1]
                    print(f"✓ Selected: {Path(selected_file).name}")
                    return selected_file
                elif choice_num == len(unique_files) + 1:
                    return self._get_manual_file_path()
                elif choice_num == len(unique_files) + 2:
                    raise KeyboardInterrupt("File selection cancelled")
                else:
                    print(f"Invalid choice. Please enter 1-{len(unique_files) + 2}")

            except ValueError:
                print("Please enter a valid number.")
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"Error: {e}")

    def _get_manual_file_path(self) -> str:
        """Get file path manually from user input."""
        print("\n📝 Manual File Path Entry")
        print("-" * 30)

        while True:
            file_path = input("Enter the full path to your document: ").strip().strip('"\'')

            if not file_path:
                print("File path cannot be empty.")
                continue

            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                retry = input("Try again? (y/n): ").strip().lower()
                if retry not in ['y', 'yes']:
                    raise FileNotFoundError("File not found")
                continue

            if not os.path.isfile(file_path):
                print(f"Path is not a file: {file_path}")
                continue

            return file_path

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = float(size_bytes)

        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1

        return f"{size:.1f} {size_names[i]}"

    def extract_text_with_headings(self, json_data: List[Dict[str, Any]]) -> str:
        """
        Extract and organize text content with proper heading structure.

        Args:
            json_data: JSON data from LlamaParse

        Returns:
            Formatted text with headings preserved
        """
        full_text = []

        for doc in json_data:
            pages = doc.get("pages", [])
            for page_num, page in enumerate(pages, 1):
                full_text.append(f"\n{'=' * 50}")
                full_text.append(f"PAGE {page_num}")
                full_text.append(f"{'=' * 50}\n")

                # Get markdown content which preserves structure
                markdown_content = page.get("md", "")
                if markdown_content:
                    full_text.append(markdown_content)
                else:
                    # Fallback to plain text
                    text_content = page.get("text", "")
                    full_text.append(text_content)

                full_text.append(f"\n{'-' * 30}\n")

        return "\n".join(full_text)

    def save_text(self, text_content: str, output_path: str) -> None:
        """
        Save extracted text content to file.

        Args:
            text_content: Extracted text with headings
            output_path: Path where to save the text file
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text_content)
            print(f"✓ Text content saved to: {output_path}")
        except Exception as e:
            print(f"✗ Error saving text content: {e}")

    def extract_from_document(self, file_path: str = None, output_file: str = "extracted_text.txt") -> str:
        """
        Extract text from a document file.

        Args:
            file_path: Path to the document to process (if None, will prompt for selection)
            output_file: Path for the output text file

        Returns:
            Extracted text content
        """
        # If no file path provided, use interactive selection
        if file_path is None:
            file_path = self.select_file_interactive()

        print(f"Processing document: {Path(file_path).name}")

        try:
            print("Parsing document with LlamaParse...")
            json_data = self.parser.get_json_result(file_path)

            if not json_data:
                raise ValueError("No data extracted from document.")

            print("✓ Document parsed successfully")

            print("Extracting text content...")
            text_content = self.extract_text_with_headings(json_data)

            if not text_content.strip():
                raise ValueError("No text content found in the document")

            self.save_text(text_content, output_file)

            print(f"🎉 Text extraction complete!")
            print(f"📄 Text saved to: {output_file}")

            # Display statistics
            lines = text_content.split('\n')
            words = text_content.split()
            chars = len(text_content)

            print(f"📊 Content Statistics:")
            print(f"   • Lines: {len(lines):,}")
            print(f"   • Words: {len(words):,}")
            print(f"   • Characters: {chars:,}")

            return text_content

        except Exception as e:
            print(f"❌ Error processing document: {e}")
            raise

    def extract_interactive(self, output_file: str = "extracted_text.txt") -> str:
        """
        Interactive document extraction with file selection.

        Args:
            output_file: Path for the output text file

        Returns:
            Extracted text content
        """
        return self.extract_from_document(file_path=None, output_file=output_file)