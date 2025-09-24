#!/usr/bin/env python3
"""
Streamlit Multi-Functional Document Processing Application
========================================================

This Streamlit app provides:
1. RAG Q&A System with document upload
2. Bibliometric Report Generation with PDF upload
3. Text Extraction with document upload

All modules integrated with file upload functionality.
"""

import streamlit as st
import tempfile
import os
import io
from pathlib import Path
import time

# Import custom modules
from document_extractor import DocumentExtractor
from rag_pipeline import RAGPipeline
from report_generator import BibliometricReportGenerator


class StreamlitApp:
    """Main Streamlit application class."""

    def __init__(self):
        """Initialize the Streamlit app."""
        self.init_session_state()
        self.setup_page_config()

    def setup_page_config(self):
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title="Document Processing Suite",
            page_icon="📄",
            layout="wide",
            initial_sidebar_state="expanded"
        )

    def init_session_state(self):
        """Initialize Streamlit session state variables."""
        if 'document_extractor' not in st.session_state:
            st.session_state.document_extractor = DocumentExtractor()

        if 'rag_pipeline' not in st.session_state:
            st.session_state.rag_pipeline = None

        if 'report_generator' not in st.session_state:
            st.session_state.report_generator = BibliometricReportGenerator()

        if 'rag_initialized' not in st.session_state:
            st.session_state.rag_initialized = False

        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []

        if 'extracted_text' not in st.session_state:
            st.session_state.extracted_text = None

    def convert_html_to_pdf(self, html_content: str, output_filename: str) -> bytes:
        """
        Convert HTML content to PDF bytes while preserving all styling.

        Args:
            html_content: HTML string to convert
            output_filename: Base filename for the PDF

        Returns:
            PDF content as bytes
        """
        try:
            # Method 1: Use Playwright for high-fidelity HTML-to-PDF conversion
            return self._convert_with_playwright(html_content)

        except ImportError:
            st.warning("Playwright not available, trying alternative method...")
        except Exception as e:
            st.warning(f"Playwright conversion failed: {e}")

        try:
            # Method 2: Enhanced HTML conversion with better CSS preservation
            return self._convert_with_enhanced_html(html_content)

        except Exception as e:
            st.warning(f"Enhanced HTML conversion failed: {e}")

        # If all methods fail, raise an informative error
        raise Exception(
            "PDF conversion failed. The HTML report is still available for download. "
            "For PDF functionality, please ensure all dependencies are properly installed."
        )

    def _convert_with_playwright(self, html_content: str) -> bytes:
        """
        Convert HTML to PDF using Playwright (preserves all styling).

        Args:
            html_content: HTML string to convert

        Returns:
            PDF content as bytes
        """
        from playwright.sync_api import sync_playwright
        import tempfile
        import os

        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Set content and wait for it to load
            page.set_content(html_content, wait_until="networkidle")

            # Generate PDF with high quality settings
            pdf_bytes = page.pdf(
                format="A4",
                margin={
                    "top": "1cm",
                    "right": "1cm",
                    "bottom": "1cm",
                    "left": "1cm"
                },
                print_background=True,  # Include background colors/images
                prefer_css_page_size=True
            )

            browser.close()
            return pdf_bytes

    def _convert_with_enhanced_html(self, html_content: str) -> bytes:
        """
        Enhanced HTML to PDF conversion with better CSS preservation.

        Args:
            html_content: HTML string to convert

        Returns:
            PDF content as bytes
        """
        try:
            from xhtml2pdf import pisa
            import io

            # Enhance HTML for better PDF rendering
            enhanced_html = self._enhance_html_for_pdf(html_content)

            pdf_buffer = io.BytesIO()
            pisa_status = pisa.CreatePDF(
                enhanced_html,
                dest=pdf_buffer,
                encoding='utf-8'
            )

            if not pisa_status.err:
                pdf_buffer.seek(0)
                return pdf_buffer.getvalue()
            else:
                raise Exception("Enhanced HTML conversion failed")

        except ImportError:
            raise ImportError("xhtml2pdf not available")

    def _enhance_html_for_pdf(self, html_content: str) -> str:
        """
        Enhance HTML content for better PDF conversion while preserving styling.

        Args:
            html_content: Original HTML content

        Returns:
            Enhanced HTML content with improved CSS
        """
        import re

        # Add print-specific CSS
        print_css = """
        <style type="text/css">
        @media print {
            body { 
                -webkit-print-color-adjust: exact !important;
                color-adjust: exact !important;
            }
        }

        /* Fix for gradients in PDF */
        .header {
            background: #2c3e50 !important;
            background-image: none !important;
        }

        .stat-card {
            background: #3498db !important;
            background-image: none !important;
            -webkit-print-color-adjust: exact;
            color-adjust: exact;
        }

        /* Ensure text is visible */
        body, p, div, span, td, th {
            color: #2c3e50 !important;
        }

        .header, .header h1, .header p {
            color: white !important;
        }

        .stat-card, .stat-card h3, .stat-card .value {
            color: white !important;
        }

        /* Fix table styling */
        table {
            border-collapse: collapse !important;
            width: 100% !important;
        }

        th {
            background-color: #34495e !important;
            color: white !important;
            -webkit-print-color-adjust: exact;
            color-adjust: exact;
        }

        /* Ensure borders are visible */
        table, th, td {
            border: 1px solid #ddd !important;
        }

        /* Fix for container backgrounds */
        .container {
            background: white !important;
            box-shadow: none !important;
        }

        .data-container {
            background: #f8f9fa !important;
            border-left: 5px solid #3498db !important;
            -webkit-print-color-adjust: exact;
            color-adjust: exact;
        }

        /* Page break handling */
        .section {
            page-break-inside: avoid;
        }

        h2 {
            page-break-after: avoid;
        }
        </style>
        """

        # Insert the print CSS before closing head tag
        if '</head>' in html_content:
            html_content = html_content.replace('</head>', print_css + '</head>')
        else:
            # If no head tag, add it
            html_content = html_content.replace('<html>', '<html><head>' + print_css + '</head>')

        # Convert complex gradients to solid colors for PDF compatibility
        html_content = re.sub(
            r'background:\s*linear-gradient\([^)]+\)',
            'background: #2c3e50',
            html_content
        )

        # Ensure all text has proper color contrast
        html_content = re.sub(
            r'color:\s*#ecf0f1',
            'color: white',
            html_content
        )

        return html_content

    def render_sidebar(self):
        """Render the sidebar with navigation."""
        st.sidebar.title("📄 Document Processing Suite")
        st.sidebar.markdown("---")

        # Navigation menu
        page = st.sidebar.selectbox(
            "Choose Function:",
            [
                "🏠 Home",
                "🤖 RAG Q&A System",
                "📊 Bibliometric Reports",
                "📝 Text Extraction"
            ]
        )

        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🔧 System Info")
        st.sidebar.info(
            "**API Keys**: All hardcoded ✅\n\n"
            "**Supported Formats**:\n"
            "- PDF, DOCX, DOC\n"
            "- PPTX, PPT, XLSX, XLS\n"
            "- TXT, MD, HTML\n"
            "- Images: PNG, JPG, JPEG"
        )

        return page

    def save_uploaded_file(self, uploaded_file):
        """Save uploaded file to temporary directory and return path."""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                return tmp_file.name
        except Exception as e:
            st.error(f"Error saving file: {e}")
            return None

    def render_home_page(self):
        """Render the home page."""
        st.title("📄 Multi-Functional Document Processing System")
        st.markdown("---")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### 🤖 RAG Q&A System")
            st.markdown(
                """
                **Upload & Query Documents**
                - Extract text from any document
                - Ask questions about content
                - Get AI-powered answers
                - Conversational memory
                """
            )
            if st.button("Start Q&A Session", key="home_qa"):
                st.session_state.page = "🤖 RAG Q&A System"
                st.rerun()

        with col2:
            st.markdown("### 📊 Bibliometric Reports")
            st.markdown(
                """
                **Generate Research Reports**
                - Upload PDF research papers
                - AI analysis of bibliometrics
                - Professional HTML & PDF reports
                - Publication insights
                """
            )
            if st.button("Generate Report", key="home_report"):
                st.session_state.page = "📊 Bibliometric Reports"
                st.rerun()

        with col3:
            st.markdown("### 📝 Text Extraction")
            st.markdown(
                """
                **Extract Document Text**
                - Parse any document format
                - Preserve structure & headings
                - Download extracted text
                - Quick preview
                """
            )
            if st.button("Extract Text", key="home_extract"):
                st.session_state.page = "📝 Text Extraction"
                st.rerun()

        st.markdown("---")
        st.markdown("### 🚀 Quick Start Guide")

        with st.expander("How to use this system"):
            st.markdown(
                """
                1. **Choose a function** from the sidebar
                2. **Upload your document** using the file uploader
                3. **Wait for processing** (may take a few moments)
                4. **Interact with results** - ask questions, download reports, or save text

                **Tips:**
                - Larger files take longer to process
                - PDF files work best for bibliometric analysis
                - All processing is done securely on the server
                """
            )

    def render_rag_page(self):
        """Render the RAG Q&A page."""
        st.title("🤖 RAG Q&A System")
        st.markdown("Upload a document and ask questions about its content!")
        st.markdown("---")

        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("### 📤 Upload Document")

            uploaded_file = st.file_uploader(
                "Choose a document file",
                type=['pdf', 'docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls', 'txt', 'md', 'html', 'png', 'jpg', 'jpeg'],
                help="Supported formats: PDF, Word, PowerPoint, Excel, Text files, Images (PNG, JPG)",
                key="rag_uploader"
            )

            if uploaded_file is not None:
                st.success(f"📁 File uploaded: {uploaded_file.name}")
                st.info(f"📏 Size: {uploaded_file.size:,} bytes")

                if st.button("🔄 Process Document", key="process_rag"):
                    self.process_document_for_rag(uploaded_file)

            # RAG Status
            st.markdown("### 📊 System Status")
            if st.session_state.rag_initialized:
                st.success("✅ RAG System Ready")
                if st.button("🧹 Clear Memory", key="clear_memory"):
                    if st.session_state.rag_pipeline:
                        st.session_state.rag_pipeline.clear_memory()
                    st.session_state.chat_history = []
                    st.success("Memory cleared!")
                    st.rerun()
            else:
                st.warning("⏳ Upload and process a document first")

        with col2:
            st.markdown("### 💬 Chat Interface")

            if st.session_state.rag_initialized:
                self.render_chat_interface()
            else:
                st.info("👆 Upload a document on the left to start chatting!")

                # Show example questions
                st.markdown("### 💡 Example Questions")
                st.markdown(
                    """
                    Once you upload a document, you can ask questions like:
                    - "What is the main topic of this document?"
                    - "Summarize the key findings"
                    - "What are the conclusions?"
                    - "Explain the methodology used"
                    """
                )

    def process_document_for_rag(self, uploaded_file):
        """Process uploaded document for RAG system."""
        with st.spinner("🔄 Processing document for Q&A..."):
            try:
                # Save uploaded file
                temp_path = self.save_uploaded_file(uploaded_file)
                if not temp_path:
                    return

                # Extract text
                progress_bar = st.progress(0)
                st.text("Step 1/3: Extracting text...")
                progress_bar.progress(33)

                extracted_text = st.session_state.document_extractor.extract_from_document(
                    temp_path,
                    "temp_extracted.txt"
                )

                # Initialize RAG pipeline
                st.text("Step 2/3: Initializing RAG system...")
                progress_bar.progress(66)

                rag_pipeline = RAGPipeline()
                rag_pipeline.initialize_pipeline_from_text(extracted_text)

                st.text("Step 3/3: Finalizing setup...")
                progress_bar.progress(100)

                # Store in session state
                st.session_state.rag_pipeline = rag_pipeline
                st.session_state.rag_initialized = True
                st.session_state.extracted_text = extracted_text
                st.session_state.chat_history = []

                # Cleanup
                os.unlink(temp_path)

                st.success("🎉 Document processed successfully! You can now ask questions.")

            except Exception as e:
                st.error(f"❌ Error processing document: {e}")
                if 'temp_path' in locals():
                    try:
                        os.unlink(temp_path)
                    except:
                        pass

    def render_chat_interface(self):
        """Render the chat interface for RAG Q&A."""
        # Display chat history
        chat_container = st.container()

        with chat_container:
            for i, (question, answer) in enumerate(st.session_state.chat_history):
                with st.chat_message("user"):
                    st.write(question)
                with st.chat_message("assistant"):
                    st.write(answer)

        # Chat input
        user_question = st.chat_input("Ask a question about the document...")

        if user_question:
            # Add user message to chat
            with st.chat_message("user"):
                st.write(user_question)

            # Get response from RAG system
            with st.chat_message("assistant"):
                with st.spinner("🤔 Thinking..."):
                    try:
                        result = st.session_state.rag_pipeline.query(user_question)
                        answer = result["answer"]

                        st.write(answer)

                        # Show source info if available
                        if result.get("source_documents"):
                            st.caption(f"📚 Based on {len(result['source_documents'])} relevant document sections")

                    except Exception as e:
                        answer = f"Sorry, I encountered an error: {e}"
                        st.error(answer)

            # Add to chat history
            st.session_state.chat_history.append((user_question, answer))

    def render_report_page(self):
        """Render the bibliometric report generation page."""
        st.title("📊 Bibliometric Report Generator")
        st.markdown("Upload a PDF research document to generate comprehensive bibliometric analysis!")
        st.markdown("---")

        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("### 📤 Upload PDF Document")

            uploaded_file = st.file_uploader(
                "Choose a PDF file",
                type=['pdf'],
                help="Upload a PDF containing bibliometric research data",
                key="report_uploader"
            )

            if uploaded_file is not None:
                st.success(f"📁 PDF uploaded: {uploaded_file.name}")
                st.info(f"📏 Size: {uploaded_file.size:,} bytes")

                # Custom report title
                custom_title = st.text_input(
                    "Custom Report Title (optional)",
                    placeholder="Enter custom title or leave blank for auto-title",
                    key="custom_title"
                )

                if st.button("🔄 Generate Report", key="generate_report"):
                    self.generate_bibliometric_report(uploaded_file, custom_title)

            # Report generation tips
            st.markdown("### 💡 Tips for Best Results")
            st.markdown(
                """
                - Upload PDF files with bibliometric data
                - Research papers with citation analysis work best
                - Files with tables and statistics are ideal
                - Ensure text is readable (not scanned images)
                """
            )

        with col2:
            st.markdown("### 📋 Report Preview")

            # Check if we have a generated report in session state
            if 'generated_report_html' in st.session_state and 'report_filename' in st.session_state:
                st.success("✅ Report generated successfully!")

                # Create two columns for download buttons
                download_col1, download_col2 = st.columns(2)

                with download_col1:
                    # HTML Download button
                    st.download_button(
                        label="📄 Download HTML Report",
                        data=st.session_state.generated_report_html,
                        file_name=st.session_state.report_filename,
                        mime="text/html",
                        key="download_html_report",
                        use_container_width=True
                    )

                with download_col2:
                    # PDF Download button
                    if st.button("📑 Generate & Download PDF", key="generate_pdf", use_container_width=True):
                        try:
                            with st.spinner("Converting HTML to PDF..."):
                                pdf_filename = st.session_state.report_filename.replace('.html', '.pdf')
                                pdf_bytes = self.convert_html_to_pdf(
                                    st.session_state.generated_report_html,
                                    pdf_filename
                                )

                                # Store PDF in session state for download
                                st.session_state.generated_report_pdf = pdf_bytes
                                st.session_state.pdf_filename = pdf_filename

                                # Automatic download
                                st.download_button(
                                    label="📥 Download PDF Report",
                                    data=pdf_bytes,
                                    file_name=pdf_filename,
                                    mime="application/pdf",
                                    key="download_pdf_report"
                                )

                        except Exception as e:
                            st.error(f"❌ Error generating PDF: {e}")
                            st.info("💡 HTML download is still available above")

                # If PDF was already generated, show download button
                if 'generated_report_pdf' in st.session_state and 'pdf_filename' in st.session_state:
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=st.session_state.generated_report_pdf,
                        file_name=st.session_state.pdf_filename,
                        mime="application/pdf",
                        key="download_existing_pdf"
                    )

                # Preview in expander
                with st.expander("👁️ Preview Report"):
                    st.components.v1.html(
                        st.session_state.generated_report_html,
                        height=600,
                        scrolling=True
                    )

                # Clear report button
                if st.button("🗑️ Clear Report", key="clear_report"):
                    # Clear both HTML and PDF from session state
                    keys_to_clear = [
                        'generated_report_html', 'report_filename',
                        'generated_report_pdf', 'pdf_filename'
                    ]
                    for key in keys_to_clear:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()

            else:
                st.info("👆 Upload a PDF and click 'Generate Report' to see results here!")

                # Show example of what reports include
                st.markdown("### 📊 Report Contents")
                st.markdown(
                    """
                    Your generated report will include:
                    - **Executive Summary** with key statistics
                    - **Publication Trends** over time
                    - **Leading Organizations** and rankings
                    - **Top Authors** and their contributions
                    - **Collaboration Analysis** (international, regional)
                    - **Key Research Areas** and keywords
                    - **Recommendations** for future research

                    **Download Options:**
                    - 📄 **HTML Format**: Interactive web report
                    - 📑 **PDF Format**: Print-ready document
                    """
                )

    def generate_bibliometric_report(self, uploaded_file, custom_title):
        """Generate bibliometric report from uploaded PDF."""
        with st.spinner("🔄 Generating bibliometric report..."):
            try:
                progress_bar = st.progress(0)

                # Step 1: Save file
                st.text("Step 1/4: Processing PDF...")
                progress_bar.progress(25)

                # Use BytesIO to work with file content directly
                pdf_content = uploaded_file.getvalue()

                # Step 2: Extract text
                st.text("Step 2/4: Extracting text...")
                progress_bar.progress(50)

                document_text = st.session_state.report_generator.extract_text_from_pdf_bytes(pdf_content)

                if not document_text:
                    st.error("❌ Could not extract text from PDF. Please ensure the file contains readable text.")
                    return

                # Step 3: Analyze document
                st.text("Step 3/4: Analyzing document with AI...")
                progress_bar.progress(75)

                analysis_data = st.session_state.report_generator.analyze_document(document_text)

                if not analysis_data:
                    st.error("❌ Could not analyze document content.")
                    return

                # Step 4: Generate HTML report
                st.text("Step 4/4: Creating report...")
                progress_bar.progress(90)

                report_title = custom_title if custom_title else f"Analysis of {uploaded_file.name.replace('.pdf', '')}"
                html_content = st.session_state.report_generator.generate_report_html(analysis_data, report_title)

                progress_bar.progress(100)

                # Store in session state
                st.session_state.generated_report_html = html_content
                st.session_state.report_filename = f"{uploaded_file.name.replace('.pdf', '')}_report.html"

                st.success("🎉 Report generated successfully!")
                st.balloons()

            except Exception as e:
                st.error(f"❌ Error generating report: {e}")

    def render_extraction_page(self):
        """Render the text extraction page."""
        st.title("📝 Text Extraction Tool")
        st.markdown("Extract clean, structured text from any document format!")
        st.markdown("---")

        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown("### 📤 Upload Document")

            uploaded_file = st.file_uploader(
                "Choose a document file",
                type=['pdf', 'docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls', 'txt', 'md', 'html', 'png', 'jpg', 'jpeg'],
                help="Supported: PDF, Word, PowerPoint, Excel, Text files, Images",
                key="extract_uploader"
            )

            if uploaded_file is not None:
                st.success(f"📁 File uploaded: {uploaded_file.name}")
                st.info(f"📏 Size: {uploaded_file.size:,} bytes")

                if st.button("🔄 Extract Text", key="extract_text"):
                    self.extract_text_from_document(uploaded_file)

            # Extraction info
            st.markdown("### ℹ️ About Text Extraction")
            st.markdown(
                """
                **Features:**
                - Preserves document structure
                - Maintains headings and formatting
                - Handles multiple file formats
                - High-quality text extraction

                **Best for:**
                - Content analysis
                - Data preparation for RAG
                - Document conversion
                - Text preprocessing
                """
            )

        with col2:
            st.markdown("### 📄 Extracted Text")

            if 'extracted_text_content' in st.session_state and 'extraction_filename' in st.session_state:
                st.success("✅ Text extracted successfully!")

                # Statistics
                text_content = st.session_state.extracted_text_content
                stats_col1, stats_col2, stats_col3 = st.columns(3)

                with stats_col1:
                    st.metric("Words", f"{len(text_content.split()):,}")
                with stats_col2:
                    st.metric("Characters", f"{len(text_content):,}")
                with stats_col3:
                    st.metric("Lines", f"{len(text_content.split('\n')):,}")

                # Download button
                st.download_button(
                    label="📥 Download Text File",
                    data=text_content,
                    file_name=st.session_state.extraction_filename,
                    mime="text/plain",
                    key="download_text"
                )

                # Preview
                with st.expander("👁️ Preview Text (First 1000 characters)"):
                    preview_text = text_content[:1000] + "..." if len(text_content) > 1000 else text_content
                    st.text_area("Extracted content:", preview_text, height=300, disabled=True)

                # Clear extraction button
                if st.button("🗑️ Clear Extraction", key="clear_extraction"):
                    del st.session_state.extracted_text_content
                    del st.session_state.extraction_filename
                    st.rerun()

            else:
                st.info("👆 Upload a document and click 'Extract Text' to see results here!")

                # Show supported formats
                st.markdown("### 📋 Supported Formats")
                formats_col1, formats_col2 = st.columns(2)

                with formats_col1:
                    st.markdown(
                        """
                        **Documents:**
                        - PDF (.pdf)
                        - Word (.docx, .doc)
                        - PowerPoint (.pptx, .ppt)
                        """
                    )

                with formats_col2:
                    st.markdown(
                        """
                        **Data & Other:**
                        - Excel (.xlsx, .xls)
                        - Text (.txt, .md)
                        - HTML (.html)
                        - Images (.png, .jpg, .jpeg)
                        """
                    )

    def extract_text_from_document(self, uploaded_file):
        """Extract text from uploaded document."""
        with st.spinner("🔄 Extracting text from document..."):
            try:
                # Save uploaded file
                temp_path = self.save_uploaded_file(uploaded_file)
                if not temp_path:
                    return

                progress_bar = st.progress(0)
                st.text("Processing document with advanced parser...")
                progress_bar.progress(50)

                # Extract text using document extractor
                extracted_text = st.session_state.document_extractor.extract_from_document(
                    temp_path,
                    "temp_extraction.txt"
                )

                progress_bar.progress(100)

                # Store in session state
                base_name = uploaded_file.name.split('.')[0]
                st.session_state.extracted_text_content = extracted_text
                st.session_state.extraction_filename = f"{base_name}_extracted.txt"

                # Cleanup
                os.unlink(temp_path)

                st.success("🎉 Text extraction completed!")

            except Exception as e:
                st.error(f"❌ Error extracting text: {e}")
                if 'temp_path' in locals():
                    try:
                        os.unlink(temp_path)
                    except:
                        pass

    def run(self):
        """Run the Streamlit application."""
        # Render sidebar
        page = self.render_sidebar()

        # Route to appropriate page
        if page == "🏠 Home":
            self.render_home_page()
        elif page == "🤖 RAG Q&A System":
            self.render_rag_page()
        elif page == "📊 Bibliometric Reports":
            self.render_report_page()
        elif page == "📝 Text Extraction":
            self.render_extraction_page()


def main():
    """Main function to run the Streamlit app."""
    try:
        # Check if running in Streamlit context
        import streamlit as st
        app = StreamlitApp()
        app.run()
    except ImportError:
        print("Error: Streamlit is not installed.")
        print("Install with: pip install streamlit")
    except Exception as e:
        if "ScriptRunContext" in str(e):
            print("Error: This script must be run with 'streamlit run streamlit_app.py'")
            print("Do not run it directly with 'python streamlit_app.py'")
        else:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()