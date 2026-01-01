"""
FIXED PDF Generator - Multilingual Support (Arabic, Hindi, Chinese, etc.)
Replace backend/utils/pdf_generator.py with this version
"""

from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from datetime import datetime
import os
import sys


def setup_multilingual_fonts():
    """
    Setup fonts supporting multiple languages including Arabic, Hindi, Chinese, etc.
    Returns: (success: bool, font_name: str, font_name_bold: str)
    """
    
    # === COMPREHENSIVE FONT PATHS ===
    # Organized by priority: Best Arabic support first
    
    font_candidates = [
        # === ARABIC-OPTIMIZED FONTS (HIGHEST PRIORITY) ===
        {
            'name': 'DejaVuSans',
            'regular': [
                # Linux
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/dejavu/DejaVuSans.ttf',
                # Windows (if DejaVu is installed)
                'C:\\Windows\\Fonts\\DejaVuSans.ttf',
                # Mac
                '/Library/Fonts/DejaVuSans.ttf',
                '/System/Library/Fonts/Supplemental/DejaVuSans.ttf',
            ],
            'bold': [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf',
                'C:\\Windows\\Fonts\\DejaVuSans-Bold.ttf',
                '/Library/Fonts/DejaVuSans-Bold.ttf',
            ]
        },
        
        # === WINDOWS SYSTEM FONTS ===
        {
            'name': 'Arial Unicode',
            'regular': [
                'C:\\Windows\\Fonts\\ARIALUNI.TTF',
                'C:\\Windows\\Fonts\\arialuni.ttf',
            ],
            'bold': [
                'C:\\Windows\\Fonts\\ARIALUNI.TTF',  # Same as regular
            ]
        },
        {
            'name': 'Tahoma',
            'regular': [
                'C:\\Windows\\Fonts\\tahoma.ttf',
                'C:\\Windows\\Fonts\\Tahoma.ttf',
            ],
            'bold': [
                'C:\\Windows\\Fonts\\tahomabd.ttf',
                'C:\\Windows\\Fonts\\Tahomabd.ttf',
            ]
        },
        {
            'name': 'Segoe UI',
            'regular': [
                'C:\\Windows\\Fonts\\segoeui.ttf',
                'C:\\Windows\\Fonts\\SegoeUI.ttf',
            ],
            'bold': [
                'C:\\Windows\\Fonts\\segoeuib.ttf',
                'C:\\Windows\\Fonts\\SegoeUIBold.ttf',
            ]
        },
        
        # === LINUX SYSTEM FONTS ===
        {
            'name': 'Noto Sans',
            'regular': [
                '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
                '/usr/share/fonts/noto/NotoSans-Regular.ttf',
                '/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf',
            ],
            'bold': [
                '/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf',
                '/usr/share/fonts/noto/NotoSans-Bold.ttf',
                '/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf',
            ]
        },
        {
            'name': 'FreeSans',
            'regular': [
                '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
                '/usr/share/fonts/gnu-free/FreeSans.ttf',
            ],
            'bold': [
                '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf',
                '/usr/share/fonts/gnu-free/FreeSansBold.ttf',
            ]
        },
        
        # === MAC SYSTEM FONTS ===
        {
            'name': 'Arial Unicode',
            'regular': [
                '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
                '/Library/Fonts/Arial Unicode.ttf',
            ],
            'bold': [
                '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
            ]
        },
        {
            'name': 'Helvetica Neue',
            'regular': [
                '/System/Library/Fonts/HelveticaNeue.ttc',
            ],
            'bold': [
                '/System/Library/Fonts/HelveticaNeue.ttc',
            ]
        },
    ]
    
    # Try each font candidate
    for font_info in font_candidates:
        try:
            regular_font = None
            bold_font = None
            
            # Find regular font
            for path in font_info['regular']:
                if os.path.exists(path):
                    regular_font = path
                    break
            
            # Find bold font
            for path in font_info['bold']:
                if os.path.exists(path):
                    bold_font = path
                    break
            
            if regular_font:
                try:
                    # Register fonts
                    pdfmetrics.registerFont(TTFont('MultiLang', regular_font))
                    
                    if bold_font:
                        pdfmetrics.registerFont(TTFont('MultiLang-Bold', bold_font))
                    else:
                        # Use regular font for bold if bold variant not found
                        pdfmetrics.registerFont(TTFont('MultiLang-Bold', regular_font))
                    
                    print(f"✅ Successfully loaded font: {font_info['name']}")
                    print(f"   Regular: {regular_font}")
                    print(f"   Bold: {bold_font or regular_font}")
                    
                    return True, 'MultiLang', 'MultiLang-Bold'
                
                except Exception as e:
                    print(f"⚠️  Failed to register {font_info['name']}: {e}")
                    continue
        
        except Exception as e:
            continue
    
    print("⚠️  No suitable multilingual font found. Using default Helvetica.")
    print("   Arabic and other complex scripts may not display correctly.")
    return False, 'Helvetica', 'Helvetica-Bold'


def is_rtl_text(text):
    """
    Detect if text contains Right-to-Left languages (Arabic, Hebrew, etc.)
    """
    if not text:
        return False
    
    # Unicode ranges for RTL scripts
    rtl_ranges = [
        (0x0600, 0x06FF),  # Arabic
        (0x0750, 0x077F),  # Arabic Supplement
        (0x08A0, 0x08FF),  # Arabic Extended-A
        (0xFB50, 0xFDFF),  # Arabic Presentation Forms-A
        (0xFE70, 0xFEFF),  # Arabic Presentation Forms-B
        (0x0590, 0x05FF),  # Hebrew
        (0xFB1D, 0xFB4F),  # Hebrew Presentation Forms
    ]
    
    # Check if any character is in RTL range
    for char in str(text):
        code = ord(char)
        for start, end in rtl_ranges:
            if start <= code <= end:
                return True
    
    return False


def reshape_arabic_text(text):
    """
    Reshape Arabic text for proper display in PDF
    Handles character joining and bidirectional text
    """
    if not text:
        return text
    
    try:
        # Only process if text contains RTL characters
        if not is_rtl_text(text):
            return text
        
        # Import libraries (only if needed)
        try:
            import arabic_reshaper
            from bidi.algorithm import get_display
        except ImportError:
            print("⚠️  WARNING: arabic-reshaper and python-bidi not installed!")
            print("   Install with: pip install arabic-reshaper python-bidi")
            return text
        
        # Step 1: Reshape Arabic characters (handles ligatures and connections)
        reshaped_text = arabic_reshaper.reshape(str(text))
        
        # Step 2: Apply bidirectional algorithm (handles RTL ordering)
        bidi_text = get_display(reshaped_text)
        
        return bidi_text
    
    except Exception as e:
        print(f"⚠️  Error reshaping Arabic text: {e}")
        return text


def create_multilingual_paragraph(text, style, is_bold=False, has_font=True):
    """
    Create a paragraph with proper multilingual support
    Handles Arabic, Hebrew, and other complex scripts
    """
    if not text:
        return Paragraph("", style)
    
    # Process Arabic/Hebrew text
    processed_text = reshape_arabic_text(str(text))
    
    # Determine text alignment
    alignment = TA_RIGHT if is_rtl_text(text) else TA_LEFT
    
    if has_font:
        # Use custom multilingual font
        font_name = 'MultiLang-Bold' if is_bold else 'MultiLang'
        
        custom_style = ParagraphStyle(
            name='CustomMultilang',
            parent=style,
            fontName=font_name,
            fontSize=getattr(style, 'fontSize', 10),
            wordWrap='CJK',  # Support for CJK (Chinese, Japanese, Korean)
            alignment=alignment,
            leading=getattr(style, 'leading', 12),
        )
        
        return Paragraph(processed_text, custom_style)
    else:
        # Fallback to default font with alignment
        fallback_style = ParagraphStyle(
            name='Fallback',
            parent=style,
            alignment=alignment,
        )
        return Paragraph(processed_text, fallback_style)


def generate_patient_pdf(patient_data):
    """
    Generate a comprehensive PDF report from patient data
    
    Args:
        patient_data: Dictionary containing:
            - demographic: {name, age, gender, email, phone}
            - per_symptom: {symptom_name: {Duration, Severity, Frequency, Factors, Additional Notes}}
            - Gen_questions: {question: answer}
            - summary: Optional clinical summary
    
    Returns:
        BytesIO buffer containing the PDF
    """
    
    # Create PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )
    
    # Setup fonts and check availability
    has_font, font_regular, font_bold = setup_multilingual_fonts()
    
    # Get default styles
    styles = getSampleStyleSheet()
    
    # Create custom styles
    if has_font:
        header_style = ParagraphStyle(
            'MultilangHeader',
            parent=styles['Heading1'],
            fontName=font_bold,
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1f77b4'),
        )
        
        subheader_style = ParagraphStyle(
            'MultilangSubHeader',
            parent=styles['Heading2'],
            fontName=font_bold,
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor('#2c3e50'),
        )
        
        normal_style = ParagraphStyle(
            'MultilangNormal',
            parent=styles['Normal'],
            fontName=font_regular,
            fontSize=10,
            wordWrap='CJK',
            leading=14,
        )
    else:
        header_style = styles['Heading1']
        subheader_style = styles['Heading2']
        normal_style = styles['Normal']
    
    # Build PDF content
    story = []
    
    # === TITLE ===
    title_text = "PATIENT HEALTH ASSESSMENT REPORT"
    title = create_multilingual_paragraph(title_text, header_style, is_bold=True, has_font=has_font)
    story.append(title)
    story.append(Spacer(1, 0.2 * inch))
    
    # === GENERATION DATE ===
    date_str = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    date_text = f"<i>Generated on: {date_str}</i>"
    date_para = create_multilingual_paragraph(date_text, normal_style, has_font=has_font)
    story.append(date_para)
    story.append(Spacer(1, 0.3 * inch))
    
    # === PATIENT INFORMATION ===
    story.append(create_multilingual_paragraph("Patient Information", subheader_style, is_bold=True, has_font=has_font))
    
    demo_data = [
        [
            create_multilingual_paragraph("<b>Field</b>", normal_style, is_bold=True, has_font=has_font),
            create_multilingual_paragraph("<b>Information</b>", normal_style, is_bold=True, has_font=has_font)
        ]
    ]
    
    for field, value in patient_data.get("demographic", {}).items():
        if field.lower() not in ["password", "pwd"]:
            demo_data.append([
                create_multilingual_paragraph(f"<b>{field.capitalize()}</b>", normal_style, is_bold=True, has_font=has_font),
                create_multilingual_paragraph(str(value), normal_style, has_font=has_font)
            ])
    
    demo_table = Table(demo_data, colWidths=[200, 400])
    demo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), font_bold if has_font else 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f2f6')])
    ]))
    
    story.append(demo_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # === CLINICAL SUMMARY ===
    if "summary" in patient_data and patient_data["summary"]:
        story.append(create_multilingual_paragraph("Clinical Summary", subheader_style, is_bold=True, has_font=has_font))
        
        summary_text = str(patient_data["summary"])
        summary_para = create_multilingual_paragraph(summary_text, normal_style, has_font=has_font)
        story.append(summary_para)
        story.append(Spacer(1, 0.3 * inch))
    
    # === REPORTED SYMPTOMS ===
    story.append(create_multilingual_paragraph("Reported Symptoms", subheader_style, is_bold=True, has_font=has_font))
    
    symptoms_data = [[
        create_multilingual_paragraph("<b>Symptom</b>", normal_style, is_bold=True, has_font=has_font),
        create_multilingual_paragraph("<b>Duration</b>", normal_style, is_bold=True, has_font=has_font),
        create_multilingual_paragraph("<b>Severity</b>", normal_style, is_bold=True, has_font=has_font),
        create_multilingual_paragraph("<b>Frequency</b>", normal_style, is_bold=True, has_font=has_font),
        create_multilingual_paragraph("<b>Additional Notes</b>", normal_style, is_bold=True, has_font=has_font)
    ]]
    
    for symptom, details in patient_data.get("per_symptom", {}).items():
        row = [
            create_multilingual_paragraph(f"<b>{symptom.upper()}</b>", normal_style, is_bold=True, has_font=has_font),
            create_multilingual_paragraph(str(details.get("Duration", "N/A")), normal_style, has_font=has_font),
            create_multilingual_paragraph(str(details.get("Severity", "N/A")), normal_style, has_font=has_font),
            create_multilingual_paragraph(str(details.get("Frequency", "N/A")), normal_style, has_font=has_font),
            create_multilingual_paragraph(str(details.get("Additional Notes", "N/A")), normal_style, has_font=has_font)
        ]
        symptoms_data.append(row)
    
    symptoms_table = Table(symptoms_data, colWidths=[120, 120, 100, 120, 240])
    symptoms_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), font_bold if has_font else 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f2f6')])
    ]))
    
    story.append(symptoms_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # === GENERAL HEALTH INFORMATION ===
    story.append(create_multilingual_paragraph("General Health Information", subheader_style, is_bold=True, has_font=has_font))
    
    health_data = [[
        create_multilingual_paragraph("<b>Question</b>", normal_style, is_bold=True, has_font=has_font),
        create_multilingual_paragraph("<b>Answer</b>", normal_style, is_bold=True, has_font=has_font)
    ]]
    
    for question, answer in patient_data.get("Gen_questions", {}).items():
        health_data.append([
            create_multilingual_paragraph(f"<b>{question}</b>", normal_style, is_bold=True, has_font=has_font),
            create_multilingual_paragraph(str(answer), normal_style, has_font=has_font)
        ])
    
    health_table = Table(health_data, colWidths=[350, 350])
    health_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), font_bold if has_font else 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f2f6')])
    ]))
    
    story.append(health_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # === DISCLAIMER ===
    disclaimer_text = ("<i><b>Disclaimer:</b> This report is for informational purposes only and does not "
                      "constitute medical advice. Please consult with a qualified healthcare professional "
                      "for proper diagnosis and treatment.</i>")
    disclaimer = create_multilingual_paragraph(disclaimer_text, normal_style, has_font=has_font)
    story.append(disclaimer)
    
    # === BUILD PDF ===
    try:
        doc.build(story)
        print("✅ PDF generated successfully")
    except Exception as e:
        print(f"❌ PDF generation error: {e}")
        
        # Fallback: Create simple error PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = [
            Paragraph("PATIENT HEALTH ASSESSMENT REPORT", styles['Heading1']),
            Paragraph("<i>Note: Some characters could not be displayed due to font limitations.</i>", styles['Normal']),
            Spacer(1, 0.5 * inch),
            Paragraph("Please ensure proper fonts are installed on the server.", styles['Normal']),
        ]
        doc.build(story)
    
    # Reset buffer position
    buffer.seek(0)
    return buffer