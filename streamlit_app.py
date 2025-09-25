#!/usr/bin/env python3
import streamlit as st
import tempfile
import os
import io
from pathlib import Path
import time
from document_extractor import DocumentExtractor
from rag_pipeline import RAGPipeline
from report_generator import BibliometricReportGenerator


class StreamlitApp:

    def __init__(self):
        self.init_session_state()
        self.setup_page_config()

    def setup_page_config(self):
        st.set_page_config(
            page_title="Document Processing Suite",
            page_icon="📄",
            layout="wide",
            initial_sidebar_state="expanded"
        )

    def init_session_state(self):
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

    def render_sidebar(self):
        st.sidebar.title("📄 Document Processing Suite")
        st.sidebar.markdown("---")
        page = st.sidebar.selectbox(
            "Choose Function:",
            [
                "🏠 Home",
                "🤖 RAG Q&A System",
                "📊 Medical Reports",
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
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                return tmp_file.name
        except Exception as e:
            st.error(f"Error saving file: {e}")

            return None

    def render_home_page(self):
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
            st.markdown("### 📊 Medical Reports")
            st.markdown(
                """
                **Generate Research Reports**
                - Upload PDF research papers
                - AI analysis of medical documents
                - Professional HTML reports
                - Publication insights
                """
            )
            if st.button("Generate Report", key="home_report"):
                st.session_state.page = "📊 Medical Reports"
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
        with st.spinner("🔄 Processing document for Q&A..."):
            try:
                temp_path = self.save_uploaded_file(uploaded_file)
                if not temp_path:
                    return
                progress_bar = st.progress(0)
                st.text("Step 1/3: Extracting text...")
                progress_bar.progress(33)
                extracted_text = st.session_state.document_extractor.extract_from_document(
                    temp_path,
                    "temp_extracted.txt"
                )
                st.text("Step 2/3: Initializing RAG system...")
                progress_bar.progress(66)
                rag_pipeline = RAGPipeline()
                rag_pipeline.initialize_pipeline_from_text(extracted_text)
                st.text("Step 3/3: Finalizing setup...")
                progress_bar.progress(100)
                st.session_state.rag_pipeline = rag_pipeline
                st.session_state.rag_initialized = True
                st.session_state.extracted_text = extracted_text
                st.session_state.chat_history = []
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
        chat_container = st.container()
        with chat_container:
            for i, (question, answer) in enumerate(st.session_state.chat_history):
                with st.chat_message("user"):
                    st.write(question)
                with st.chat_message("assistant"):
                    st.write(answer)
        user_question = st.chat_input("Ask a question about the document...")
        if user_question:
            with st.chat_message("user"):
                st.write(user_question)
            with st.chat_message("assistant"):
                with st.spinner("🤔 Thinking..."):
                    try:
                        if hasattr(st.session_state.rag_pipeline, 'vectorstore'):
                            retriever = st.session_state.rag_pipeline.vectorstore.as_retriever(
                                search_type="similarity",
                                search_kwargs={"k": 5}
                            )
                            relevant_docs = retriever.get_relevant_documents(user_question)
                            context = "\n\n".join([doc.page_content for doc in relevant_docs])
                            chat_history_str = ""
                            if st.session_state.chat_history:
                                recent_history = st.session_state.chat_history[-3:]
                                for q, a in recent_history:
                                    chat_history_str += f"Human: {q}\nAssistant: {a}\n\n"
                            full_prompt = f"""You are an intelligent document assistant. Your primary role is to help users understand and extract information from uploaded documents, while also being able to engage in natural conversation.

    Instructions for responding:

    1. CONVERSATIONAL INTERACTIONS (greetings, small talk, general chat):
       - If the user is greeting you, making small talk, or having casual conversation that doesn't require document analysis, respond naturally and conversationally
       - Be helpful and friendly without mentioning the uploaded documents
       - Examples: "Hello", "How are you?", "Thank you", "What can you do?", etc.

    2. DOCUMENT-RELATED QUESTIONS (queries about content, analysis, specific information):
       - First, carefully examine the provided context from the uploaded document
       - If the answer is clearly found in the context, provide a comprehensive response based on that information
       - Reference the document naturally (e.g., "According to the document...", "The text indicates...", "Based on the uploaded content...")

    3. OUT-OF-SCOPE QUESTIONS (information not in the document):
       - If the question is document-related but the answer is not available in the provided context, respond with:
       "This information is not available in the provided document. However, based on my general knowledge: [provide helpful general information]"
       - Be clear about what comes from the document vs. your general knowledge

    Context from uploaded document:
    {context}

    Previous conversation:
    {chat_history_str}

    Current question: {user_question}

    Response:"""
                            response = st.session_state.rag_pipeline.llm.invoke(full_prompt)
                            answer = response.content if hasattr(response, 'content') else str(response)
                            if hasattr(st.session_state.rag_pipeline,
                                       'memory') and st.session_state.rag_pipeline.memory:
                                st.session_state.rag_pipeline.memory.save_context(
                                    {"question": user_question},
                                    {"answer": answer}
                                )
                        else:
                            result = st.session_state.rag_pipeline.query(user_question)
                            answer = result["answer"]
                        st.write(answer)
                        if 'relevant_docs' in locals() and relevant_docs:
                            st.caption(f"📚 Based on {len(relevant_docs)} relevant document sections")
                    except Exception as e:
                        answer = f"Sorry, I encountered an error: {e}"
                        st.error(answer)
            st.session_state.chat_history.append((user_question, answer))

    def render_report_page(self):
        st.title("📊 Medical Report Generator")
        st.markdown("Upload a PDF research document to generate comprehensive analysis!")
        st.markdown("---")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("### 📤 Upload PDF Document")
            uploaded_file = st.file_uploader(
                "Choose a PDF file",
                type=['pdf'],
                help="Upload a PDF containing medical research data",
                key="report_uploader"
            )
            if uploaded_file is not None:
                st.success(f"📁 PDF uploaded: {uploaded_file.name}")
                st.info(f"📏 Size: {uploaded_file.size:,} bytes")
                custom_title = st.text_input(
                    "Custom Report Title (optional)",
                    placeholder="Enter custom title or leave blank for auto-title",
                    key="custom_title"
                )


                if st.button("🔄 Generate Report", key="generate_report"):
                    self.generate_bibliometric_report(uploaded_file, custom_title)
            st.markdown("### 💡 Tips for Best Results")
            st.markdown(
                """
                - Upload PDF files with medical data
                - Research papers with citation analysis work best
                - Files with tables and statistics are ideal
                - Ensure text is readable (not scanned images)
                """
            )
        with col2:
            st.markdown("### 📋 Report Preview")
            if 'generated_report_html' in st.session_state and 'report_filename' in st.session_state:
                st.success("✅ Report generated successfully!")
                st.download_button(
                    label="📥 Download Report",
                    data=st.session_state.generated_report_html,
                    file_name=st.session_state.report_filename,
                    mime="text/html",
                    key="download_report"
                )
                with st.expander("👁️ Preview Report"):
                    st.components.v1.html(
                        st.session_state.generated_report_html,
                        height=600,
                        scrolling=True
                    )
                if st.button("🗑️ Clear Report", key="clear_report"):
                    del st.session_state.generated_report_html
                    del st.session_state.report_filename
                    st.rerun()
            else:
                st.info("👆 Upload a PDF and click 'Generate Report' to see results here!")
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
                    """
                )

    def generate_bibliometric_report(self, uploaded_file, custom_title):
        with st.spinner("🔄 Generating medical report..."):
            try:
                progress_bar = st.progress(0)
                st.text("Step 1/4: Processing PDF...")
                progress_bar.progress(25)
                pdf_content = uploaded_file.getvalue()
                st.text("Step 2/4: Extracting text...")
                progress_bar.progress(50)
                document_text = st.session_state.report_generator.extract_text_from_pdf_bytes(pdf_content)
                if not document_text:
                    st.error("❌ Could not extract text from PDF. Please ensure the file contains readable text.")
                    return
                st.text("Step 3/4: Analyzing document with AI...")
                progress_bar.progress(75)
                analysis_data = st.session_state.report_generator.analyze_document(document_text)
                if not analysis_data:
                    st.error("❌ Could not analyze document content.")
                    return
                st.text("Step 4/4: Creating report...")
                progress_bar.progress(90)
                report_title = custom_title if custom_title else f"Analysis of {uploaded_file.name.replace('.pdf', '')}"
                html_content = st.session_state.report_generator.generate_report_html(analysis_data, report_title)
                progress_bar.progress(100)
                st.session_state.generated_report_html = html_content
                st.session_state.report_filename = f"{uploaded_file.name.replace('.pdf', '')}_report.html"
                st.success("🎉 Report generated successfully!")
                st.balloons()
            except Exception as e:
                st.error(f"❌ Error generating report: {e}")



    def render_extraction_page(self):
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
                text_content = st.session_state.extracted_text_content
                stats_col1, stats_col2, stats_col3 = st.columns(3)
                with stats_col1:
                    st.metric("Words", f"{len(text_content.split()):,}")
                with stats_col2:
                    st.metric("Characters", f"{len(text_content):,}")
                with stats_col3:
                    st.metric("Lines", f"{len(text_content.split('\n')):,}")
                st.download_button(
                    label="📥 Download Text File",
                    data=text_content,
                    file_name=st.session_state.extraction_filename,
                    mime="text/plain",
                    key="download_text"
                )
                with st.expander("👁️ Preview Text (First 1000 characters)"):
                    preview_text = text_content[:1000] + "..." if len(text_content) > 1000 else text_content
                    st.text_area("Extracted content:", preview_text, height=300, disabled=True)
                if st.button("🗑️ Clear Extraction", key="clear_extraction"):
                    del st.session_state.extracted_text_content
                    del st.session_state.extraction_filename
                    st.rerun()
            else:
                st.info("👆 Upload a document and click 'Extract Text' to see results here!")
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
        with st.spinner("🔄 Extracting text from document..."):
            try:
                temp_path = self.save_uploaded_file(uploaded_file)
                if not temp_path:
                    return
                progress_bar = st.progress(0)
                st.text("Processing document with advanced parser...")
                progress_bar.progress(50)
                extracted_text = st.session_state.document_extractor.extract_from_document(
                    temp_path,
                    "temp_extraction.txt"
                )
                progress_bar.progress(100)
                base_name = uploaded_file.name.split('.')[0]
                st.session_state.extracted_text_content = extracted_text
                st.session_state.extraction_filename = f"{base_name}_extracted.txt"
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
        page = self.render_sidebar()

        if page == "🏠 Home":
            self.render_home_page()
        elif page == "🤖 RAG Q&A System":
            self.render_rag_page()
        elif page == "📊 Medical Reports":
            self.render_report_page()
        elif page == "📝 Text Extraction":
            self.render_extraction_page()


def main():
    try:
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
