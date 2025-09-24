#!/usr/bin/env python3
"""
Bibliometric Report Generator Module
===================================

This module generates bibliometric reports from academic papers using Gemini 2.5 Flash.
Contains its own PDF loading functionality separate from document extraction.
"""

import os
import json
import io
from typing import Dict
import PyPDF2

try:
    import google.generativeai as genai
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Please install: pip install google-generativeai PyPDF2")
    raise


class BibliometricReportGenerator:
    """
    A class to generate bibliometric reports from academic papers using Gemini 2.5 Flash
    """

    def __init__(self, api_key: str = "AIzaSyD3R_-41HkKljnZgeI0_QXz5bdymMMsBbs"):
        """
        Initialize the report generator with Gemini API key

        Args:
            api_key (str): Google AI API key for Gemini
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.api_key = api_key

    def extract_text_from_pdf_file(self, pdf_path: str) -> str:
        """
        Extract text content from PDF file

        Args:
            pdf_path (str): Path to PDF file

        Returns:
            str: Extracted text content
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""

    def extract_text_from_pdf_bytes(self, pdf_content: bytes) -> str:
        """
        Extract text content from PDF bytes

        Args:
            pdf_content (bytes): PDF file content as bytes

        Returns:
            str: Extracted text content
        """
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""

    def analyze_document(self, document_text: str) -> Dict:
        """
        Analyze the document and extract key bibliometric data

        Args:
            document_text (str): Text content of the document

        Returns:
            Dict: Structured data extracted from the document
        """
        analysis_prompt = """
        Analyze this bibliometric/research document and extract the following structured information in JSON format:

        1. Study overview (title, period, database used, total publications)
        2. Key statistics (total papers, citations, CPP, growth rates, rankings)
        3. Regional/country breakdown with numbers
        4. Top organizations (name, papers, citations, CPP)
        5. Top authors (name, affiliation, papers, citations)
        6. Collaboration statistics (international %, funding %, regional cooperation)
        7. Publication venues (journals, papers published)
        8. Key findings and trends
        9. Research focus areas and keywords
        10. Recommendations or conclusions

        Provide the response as a valid JSON object with clear structure.

        Document text:
        """ + document_text[:15000]  # Limit text to avoid token limits

        try:
            response = self.model.generate_content(analysis_prompt)
            # Clean response to extract JSON
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]

            return json.loads(response_text)
        except Exception as e:
            print(f"Error analyzing document: {e}")
            return {}

    def generate_report_html(self, analysis_data: Dict, report_title: str = None) -> str:
        """
        Generate HTML report from analyzed data with built-in PDF download functionality.

        Args:
            analysis_data (Dict): Structured data from document analysis
            report_title (str): Custom title for the report

        Returns:
            str: HTML content for the report with PDF download capability
        """
        if not report_title:
            report_title = analysis_data.get('title', 'Bibliometric Analysis Report')

        # Generate HTML using Gemini with PDF functionality
        html_prompt = f"""
        Create a beautiful, professional HTML report based on this bibliometric analysis data.

        Requirements:
        1. Use modern CSS styling with gradients, cards, and responsive design
        2. Include professional layout with header, sections, and tables
        3. Create sections for: Executive Summary, Publication Trends, Leading Organizations, Top Authors, Collaboration Analysis, Publication Venues, Key Findings, Recommendations
        4. Use tables for data presentation with proper styling
        5. Include statistics cards with key metrics
        6. Use professional color scheme (blues, grays, whites)
        7. Ensure the HTML is complete and self-contained
        8. Make it visually appealing and well-structured
        9. IMPORTANT: Add a "Download as PDF" button that uses window.print() with print-optimized CSS
        10. Include print-specific CSS that preserves colors and styling when printed/saved as PDF
        11. Add JavaScript functionality for the PDF download button

        Data to include:
        {json.dumps(analysis_data, indent=2)}

        Report Title: {report_title}

        IMPORTANT: Include these specific elements:
        - A "Download as PDF" button in the header that triggers window.print()
        - Print-specific CSS with @media print rules
        - CSS to ensure backgrounds and colors are preserved in PDF
        - Proper page break handling for PDF

        Return only the complete HTML code, starting with <!DOCTYPE html>
        """

        try:
            response = self.model.generate_content(html_prompt)
            html_content = response.text.strip()
            
            # Ensure the HTML includes PDF functionality
            if 'window.print()' not in html_content:
                html_content = self._add_pdf_functionality(html_content, report_title)
            
            return html_content
        except Exception as e:
            print(f"Error generating HTML: {e}")
            return self._fallback_html_with_pdf(analysis_data, report_title)

    def _add_pdf_functionality(self, html_content: str, title: str) -> str:
        """
        Add PDF download functionality to existing HTML content.
        
        Args:
            html_content: Original HTML content
            title: Report title
            
        Returns:
            Enhanced HTML with PDF functionality
        """
        # PDF button and JavaScript
        pdf_functionality = '''
        <script>
        function downloadPDF() {
            // Hide the PDF button during print
            document.getElementById('pdf-btn').style.display = 'none';
            
            // Set document title for PDF filename
            document.title = "''' + title.replace('"', '\\"') + '''";
            
            // Trigger print dialog
            window.print();
            
            // Show the button again after print dialog closes
            setTimeout(function() {
                document.getElementById('pdf-btn').style.display = 'block';
            }, 1000);
        }
        
        // Add print event listeners
        window.addEventListener('beforeprint', function() {
            document.body.classList.add('printing');
        });
        
        window.addEventListener('afterprint', function() {
            document.body.classList.remove('printing');
            document.getElementById('pdf-btn').style.display = 'block';
        });
        </script>
        
        <style>
        /* PDF Download Button */
        #pdf-btn {
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #e74c3c, #c0392b);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(231, 76, 60, 0.3);
            transition: all 0.3s ease;
            z-index: 1000;
        }
        
        #pdf-btn:hover {
            background: linear-gradient(135deg, #c0392b, #a93226);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(231, 76, 60, 0.4);
        }
        
        /* Print-specific styles */
        @media print {
            #pdf-btn {
                display: none !important;
            }
            
            body {
                -webkit-print-color-adjust: exact !important;
                color-adjust: exact !important;
                print-color-adjust: exact !important;
            }
            
            * {
                -webkit-print-color-adjust: exact !important;
                color-adjust: exact !important;
                print-color-adjust: exact !important;
            }
            
            .header {
                background: #2c3e50 !important;
                color: white !important;
            }
            
            .stat-card {
                background: #3498db !important;
                color: white !important;
            }
            
            th {
                background: #34495e !important;
                color: white !important;
            }
            
            .data-container {
                background: #f8f9fa !important;
                border-left: 5px solid #3498db !important;
            }
            
            /* Page breaks */
            .section {
                page-break-inside: avoid;
            }
            
            h2 {
                page-break-after: avoid;
            }
            
            /* Margins for print */
            @page {
                margin: 1cm;
                size: A4;
            }
            
            body {
                margin: 0;
                font-size: 12px;
                line-height: 1.4;
            }
        }
        
        .printing #pdf-btn {
            display: none !important;
        }
        </style>
        '''
        
        # Add PDF button to the body
        pdf_button = '<button id="pdf-btn" onclick="downloadPDF()">📄 Download as PDF</button>'
        
        # Insert the functionality before closing body tag
        if '</body>' in html_content:
            html_content = html_content.replace('</body>', pdf_functionality + pdf_button + '</body>')
        else:
            html_content += pdf_functionality + pdf_button
        
        return html_content

    def _fallback_html_with_pdf(self, data: Dict, title: str) -> str:
        """
        Fallback HTML template with PDF functionality if AI generation fails
        """
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    margin: 0; 
                    padding: 20px; 
                    background-color: #f5f5f5; 
                }}
                .container {{ 
                    max-width: 1200px; 
                    margin: 0 auto; 
                    background: white; 
                    border-radius: 10px; 
                    box-shadow: 0 0 20px rgba(0,0,0,0.1); 
                }}
                .header {{ 
                    background: linear-gradient(135deg, #2c3e50, #3498db); 
                    color: white; 
                    padding: 40px; 
                    text-align: center; 
                    border-radius: 10px 10px 0 0; 
                }}
                .header h1 {{ 
                    margin: 0; 
                    font-size: 2.5em; 
                    font-weight: 300; 
                }}
                .content {{ 
                    padding: 40px; 
                }}
                .section {{ 
                    margin: 40px 0; 
                }}
                h2 {{ 
                    color: #2c3e50; 
                    border-bottom: 3px solid #3498db; 
                    padding-bottom: 10px; 
                    font-size: 1.8em; 
                }}
                .data-container {{ 
                    background: #f8f9fa; 
                    padding: 30px; 
                    border-radius: 10px; 
                    border-left: 5px solid #3498db; 
                    margin: 20px 0; 
                }}
                .json-data {{ 
                    background: #2c3e50; 
                    color: #ecf0f1; 
                    padding: 20px; 
                    border-radius: 5px; 
                    overflow-x: auto; 
                    font-family: 'Courier New', monospace; 
                    white-space: pre-wrap; 
                }}
                .stats-grid {{ 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                    gap: 20px; 
                    margin: 30px 0; 
                }}
                .stat-card {{ 
                    background: linear-gradient(135deg, #3498db, #2980b9); 
                    color: white; 
                    padding: 25px; 
                    border-radius: 10px; 
                    text-align: center; 
                    box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3); 
                }}
                .stat-card h3 {{ 
                    margin: 0 0 10px 0; 
                    font-size: 1.2em; 
                }}
                .stat-card .value {{ 
                    font-size: 2em; 
                    font-weight: bold; 
                }}
                
                /* PDF Download Button */
                #pdf-btn {{
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: linear-gradient(135deg, #e74c3c, #c0392b);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 25px;
                    font-size: 14px;
                    font-weight: bold;
                    cursor: pointer;
                    box-shadow: 0 4px 15px rgba(231, 76, 60, 0.3);
                    transition: all 0.3s ease;
                    z-index: 1000;
                }}
                
                #pdf-btn:hover {{
                    background: linear-gradient(135deg, #c0392b, #a93226);
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(231, 76, 60, 0.4);
                }}
                
                @media print {{
                    #pdf-btn {{ display: none !important; }}
                    body {{ 
                        -webkit-print-color-adjust: exact !important;
                        color-adjust: exact !important;
                        print-color-adjust: exact !important;
                        background: white !important;
                    }}
                    * {{
                        -webkit-print-color-adjust: exact !important;
                        color-adjust: exact !important;
                        print-color-adjust: exact !important;
                    }}
                    .container {{ box-shadow: none !important; }}
                    .header {{ 
                        background: #2c3e50 !important; 
                        color: white !important;
                    }}
                    .stat-card {{
                        background: #3498db !important;
                        color: white !important;
                    }}
                    .data-container {{
                        background: #f8f9fa !important;
                        border-left: 5px solid #3498db !important;
                    }}
                    @page {{ margin: 1cm; size: A4; }}
                }}
            </style>
        </head>
        <body>
            <button id="pdf-btn" onclick="downloadPDF()">📄 Download as PDF</button>
            
            <div class="container">
                <div class="header">
                    <h1>{title}</h1>
                    <p>Generated Bibliometric Analysis Report</p>
                </div>
                <div class="content">
                    <div class="section">
                        <h2>Executive Summary</h2>
                        <p>This report presents a comprehensive bibliometric analysis based on the provided research document.</p>
                    </div>
                    
                    <div class="section">
                        <h2>Analysis Results</h2>
                        <div class="data-container">
                            <div class="json-data">{json.dumps(data, indent=2)}</div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>Key Insights</h2>
                        <div class="stats-grid">
                            <div class="stat-card">
                                <h3>Data Points</h3>
                                <div class="value">{len(data)}</div>
                            </div>
                            <div class="stat-card">
                                <h3>Analysis Date</h3>
                                <div class="value">Today</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <script>
            function downloadPDF() {{
                document.getElementById('pdf-btn').style.display = 'none';
                document.title = "{title}";
                window.print();
                setTimeout(function() {{
                    document.getElementById('pdf-btn').style.display = 'block';
                }}, 1000);
            }}
            
            window.addEventListener('beforeprint', function() {{
                document.body.classList.add('printing');
            }});
            
            window.addEventListener('afterprint', function() {{
                document.body.classList.remove('printing');
                document.getElementById('pdf-btn').style.display = 'block';
            }});
            </script>
        </body>
        </html>
        """

    def _fallback_html(self, data: Dict, title: str) -> str:
        """
        Fallback HTML template if AI generation fails
        """
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    margin: 0; 
                    padding: 20px; 
                    background-color: #f5f5f5; 
                }}
                .container {{ 
                    max-width: 1200px; 
                    margin: 0 auto; 
                    background: white; 
                    border-radius: 10px; 
                    box-shadow: 0 0 20px rgba(0,0,0,0.1); 
                }}
                .header {{ 
                    background: linear-gradient(135deg, #2c3e50, #3498db); 
                    color: white; 
                    padding: 40px; 
                    text-align: center; 
                    border-radius: 10px 10px 0 0; 
                }}
                .header h1 {{ 
                    margin: 0; 
                    font-size: 2.5em; 
                    font-weight: 300; 
                }}
                .content {{ 
                    padding: 40px; 
                }}
                .section {{ 
                    margin: 40px 0; 
                }}
                h2 {{ 
                    color: #2c3e50; 
                    border-bottom: 3px solid #3498db; 
                    padding-bottom: 10px; 
                    font-size: 1.8em; 
                }}
                .data-container {{ 
                    background: #f8f9fa; 
                    padding: 30px; 
                    border-radius: 10px; 
                    border-left: 5px solid #3498db; 
                    margin: 20px 0; 
                }}
                .json-data {{ 
                    background: #2c3e50; 
                    color: #ecf0f1; 
                    padding: 20px; 
                    border-radius: 5px; 
                    overflow-x: auto; 
                    font-family: 'Courier New', monospace; 
                    white-space: pre-wrap; 
                }}
                .stats-grid {{ 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                    gap: 20px; 
                    margin: 30px 0; 
                }}
                .stat-card {{ 
                    background: linear-gradient(135deg, #3498db, #2980b9); 
                    color: white; 
                    padding: 25px; 
                    border-radius: 10px; 
                    text-align: center; 
                    box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3); 
                }}
                .stat-card h3 {{ 
                    margin: 0 0 10px 0; 
                    font-size: 1.2em; 
                }}
                .stat-card .value {{ 
                    font-size: 2em; 
                    font-weight: bold; 
                }}
                @media print {{
                    body {{ background: white; }}
                    .container {{ box-shadow: none; }}
                    .header {{ background: #2c3e50 !important; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{title}</h1>
                    <p>Generated Bibliometric Analysis Report</p>
                </div>
                <div class="content">
                    <div class="section">
                        <h2>Executive Summary</h2>
                        <p>This report presents a comprehensive bibliometric analysis based on the provided research document.</p>
                    </div>
                    
                    <div class="section">
                        <h2>Analysis Results</h2>
                        <div class="data-container">
                            <div class="json-data">{json.dumps(data, indent=2)}</div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>Key Insights</h2>
                        <div class="stats-grid">
                            <div class="stat-card">
                                <h3>Data Points</h3>
                                <div class="value">{len(data)}</div>
                            </div>
                            <div class="stat-card">
                                <h3>Analysis Date</h3>
                                <div class="value">Today</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

    def generate_report_from_file(self, pdf_path: str, output_path: str = None, report_title: str = None) -> str:
        """
        Complete workflow to generate a bibliometric report from PDF file

        Args:
            pdf_path (str): Path to PDF file
            output_path (str): Path to save HTML report
            report_title (str): Custom title for the report

        Returns:
            str: Path to generated HTML report
        """
        print("Extracting text from PDF document...")
        document_text = self.extract_text_from_pdf_file(pdf_path)

        if not document_text:
            raise ValueError("Could not extract text from document")

        print("Analyzing document with Gemini...")
        analysis_data = self.analyze_document(document_text)

        if not analysis_data:
            raise ValueError("Could not analyze document")

        print("Generating HTML report...")
        if not report_title:
            filename = os.path.basename(pdf_path).replace('.pdf', '')
            report_title = f"Analysis of {filename}"

        html_content = self.generate_report_html(analysis_data, report_title)

        # Save report
        if not output_path:
            output_path = f"{os.path.basename(pdf_path).replace('.pdf', '')}_report.html"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"Report generated successfully: {output_path}")
        return output_path

    def generate_report_from_bytes(self, pdf_content: bytes, filename: str, output_path: str = None, report_title: str = None) -> str:
        """
        Complete workflow to generate a bibliometric report from PDF bytes

        Args:
            pdf_content (bytes): PDF file content as bytes
            filename (str): Original filename
            output_path (str): Path to save HTML report
            report_title (str): Custom title for the report

        Returns:
            str: Path to generated HTML report
        """
        print("Extracting text from uploaded document...")
        document_text = self.extract_text_from_pdf_bytes(pdf_content)

        if not document_text:
            raise ValueError("Could not extract text from document")

        print("Analyzing document with Gemini...")
        analysis_data = self.analyze_document(document_text)

        if not analysis_data:
            raise ValueError("Could not analyze document")

        print("Generating HTML report...")
        if not report_title:
            report_title = f"Analysis of {filename.replace('.pdf', '')}"

        html_content = self.generate_report_html(analysis_data, report_title)

        # Save report
        if not output_path:
            output_path = f"{filename.replace('.pdf', '')}_report.html"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"Report generated successfully: {output_path}")
        return output_path
