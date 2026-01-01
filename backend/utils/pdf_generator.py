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
from datetime import datetime
import os


def setup_multilingual_fonts():
    """
    Setup fonts that support multiple languages including Arabic, Hindi, Chinese, etc.
    Using DejaVu fonts which support most Unicode characters
    """
    try:
        # Try to register DejaVu fonts (widely available on most systems)
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            'C:\\Windows\\Fonts\\DejaVuSans.ttf',
            'C:\\Windows\\Fonts\\DejaVuSans-Bold.ttf',
            '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    if 'Bold' in font_path:
                        pdfmetrics.registerFont(TTFont('MultiLang-Bold', font_path))
                    else:
                        pdfmetrics.registerFont(TTFont('MultiLang', font_path))
                    return True
                except:
                    continue
        
        # If no system fonts found, use fallback
        return False
    except Exception as e:
        print(f"Font setup error: {e}")
        return False


def is_rtl_text(text):
    """
    Detect if text contains Right-to-Left languages (Arabic, Hebrew, etc.)
    """
    if not text:
        return False
    
    rtl_ranges = [
        (0x0600, 0x06FF),  # Arabic
        (0x0750, 0x077F),  # Arabic Supplement
        (0x0590, 0x05FF),  # Hebrew
        (0xFB50, 0xFDFF),  # Arabic Presentation Forms-A
        (0xFE70, 0xFEFF),  # Arabic Presentation Forms-B
    ]
    
    for char in str(text):
        code = ord(char)
        for start, end in rtl_ranges:
            if start <= code <= end:
                return True
    return False


def reshape_arabic_text(text):
    """
    Reshape Arabic text for proper display in PDF
    """
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        
        if is_rtl_text(text):
            # Reshape Arabic characters
            reshaped_text = arabic_reshaper.reshape(str(text))
            # Apply bidirectional algorithm
            bidi_text = get_display(reshaped_text)
            return bidi_text
        return text
    except ImportError:
        # If libraries not available, return as-is
        return text
    except Exception as e:
        print(f"Arabic reshaping error: {e}")
        return text


def create_multilingual_paragraph(text, style, is_bold=False):
    """
    Create paragraph with proper font support for multilingual text
    """
    has_multilang_font = setup_multilingual_fonts()
    
    # Process Arabic/RTL text
    processed_text = reshape_arabic_text(str(text))
    
    if has_multilang_font:
        font_name = 'MultiLang-Bold' if is_bold else 'MultiLang'
        custom_style = ParagraphStyle(
            name='CustomMultilang',
            parent=style,
            fontName=font_name,
            fontSize=style.fontSize if hasattr(style, 'fontSize') else 10,
            wordWrap='CJK',  # Support for Chinese, Japanese, Korean
            alignment=2 if is_rtl_text(text) else 0,  # Right-align for RTL
        )
        
        return Paragraph(processed_text, custom_style)
    else:
        # Fallback: use default fonts
        return Paragraph(processed_text, style)


def generate_patient_pdf(patient_data):
    """
    Generate a PDF report from patient data with FULL multilingual support
    
    Args:
        patient_data: Dictionary containing patient information
    
    Returns:
        BytesIO buffer containing the PDF
    """
    # Create PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    
    # Setup multilingual fonts
    has_multilang_font = setup_multilingual_fonts()
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Create custom styles with multilingual font support
    if has_multilang_font:
        header_style = ParagraphStyle(
            'MultilangHeader',
            parent=styles['Heading1'],
            fontName='MultiLang-Bold',
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center
        )
        subheader_style = ParagraphStyle(
            'MultilangSubHeader',
            parent=styles['Heading2'],
            fontName='MultiLang-Bold',
            fontSize=14,
            spaceAfter=12
        )
        normal_style = ParagraphStyle(
            'MultilangNormal',
            parent=styles['Normal'],
            fontName='MultiLang',
            fontSize=10,
            wordWrap='CJK'
        )
    else:
        header_style = styles['Heading1']
        subheader_style = styles['Heading2']
        normal_style = styles['Normal']
    
    story = []
    
    # Title
    title = create_multilingual_paragraph(
        "PATIENT HEALTH ASSESSMENT REPORT",
        header_style,
        is_bold=True
    )
    story.append(title)
    story.append(Spacer(1, 0.2*inch))
    
    # Generation date
    date_text = create_multilingual_paragraph(
        f"<i>Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</i>",
        normal_style
    )
    story.append(date_text)
    story.append(Spacer(1, 0.3*inch))
    
    # Patient Demographics
    story.append(create_multilingual_paragraph("Patient Information", subheader_style, is_bold=True))
    
    demo_data = [["Field", "Information"]]
    for label, data in patient_data.get("demographic", {}).items():
        if label.lower() not in ["password", "pwd"]:
            demo_data.append([
                create_multilingual_paragraph(f"<b>{label.capitalize()}</b>", normal_style, is_bold=True),
                create_multilingual_paragraph(str(data), normal_style)
            ])
    
    demo_table = Table(demo_data, colWidths=[200, 400])
    demo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f2f6')])
    ]))
    story.append(demo_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Summary (if available)
    if "summary" in patient_data and patient_data["summary"]:
        story.append(create_multilingual_paragraph("Clinical Summary", subheader_style, is_bold=True))
        summary_para = create_multilingual_paragraph(patient_data["summary"], normal_style)
        story.append(summary_para)
        story.append(Spacer(1, 0.3*inch))
    
    # Symptoms
    story.append(create_multilingual_paragraph("Reported Symptoms", subheader_style, is_bold=True))
    
    symptoms_data = [["Symptom", "Duration", "Severity", "Frequency", "Additional Notes"]]
    
    for symptom, details in patient_data.get("per_symptom", {}).items():
        row = [
            create_multilingual_paragraph(f"<b>{symptom.upper()}</b>", normal_style, is_bold=True),
            create_multilingual_paragraph(str(details.get("Duration", "N/A")), normal_style),
            create_multilingual_paragraph(str(details.get("Severity", "N/A")), normal_style),
            create_multilingual_paragraph(str(details.get("Frequency", "N/A")), normal_style),
            create_multilingual_paragraph(str(details.get("Additional Notes", "N/A")), normal_style)
        ]
        symptoms_data.append(row)
    
    symptoms_table = Table(symptoms_data, colWidths=[120, 120, 100, 120, 240])
    symptoms_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f2f6')])
    ]))
    story.append(symptoms_table)
    story.append(Spacer(1, 0.3*inch))
    
    # General Health Questions
    story.append(create_multilingual_paragraph("General Health Information", subheader_style, is_bold=True))
    
    gen_health_data = [["Question", "Answer"]]
    
    for question, answer in patient_data.get("Gen_questions", {}).items():
        gen_health_data.append([
            create_multilingual_paragraph(f"<b>{question}</b>", normal_style, is_bold=True),
            create_multilingual_paragraph(str(answer), normal_style)
        ])
    
    gen_health_table = Table(gen_health_data, colWidths=[350, 350])
    gen_health_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f2f6')])
    ]))
    story.append(gen_health_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Disclaimer
    disclaimer = create_multilingual_paragraph(
        "<i><b>Disclaimer:</b> This report is for informational purposes only and does not constitute medical advice. "
        "Please consult with a qualified healthcare professional for proper diagnosis and treatment.</i>",
        normal_style
    )
    story.append(disclaimer)
    
    # Build PDF
    try:
        doc.build(story)
    except Exception as e:
        print(f"PDF generation error: {e}")
        # Try building without multilingual support as fallback
        story = []
        story.append(Paragraph("PATIENT HEALTH ASSESSMENT REPORT", styles['Heading1']))
        story.append(Paragraph("Note: Some characters may not display correctly due to font limitations.", styles['Normal']))
        doc.build(story)
    
    # Reset buffer position
    buffer.seek(0)
    
    return buffer