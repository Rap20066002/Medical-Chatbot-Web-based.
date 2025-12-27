"""
PDF Generator Utility
Generates professional health reports
"""

from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from datetime import datetime


def generate_patient_pdf(patient_data):
    """
    Generate a PDF report from patient data.
    
    Args:
        patient_data: Dictionary containing patient information
    
    Returns:
        BytesIO buffer containing the PDF
    """
    # Create PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    
    # Styles
    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Center
    )
    subheader_style = ParagraphStyle(
        'SubHeaderStyle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12
    )
    
    story = []
    
    # Title
    title = Paragraph("PATIENT HEALTH ASSESSMENT REPORT", header_style)
    story.append(title)
    story.append(Spacer(1, 0.2*inch))
    
    # Generation date
    date_text = Paragraph(
        f"<i>Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</i>",
        normal_style
    )
    story.append(date_text)
    story.append(Spacer(1, 0.3*inch))
    
    # Patient Demographics
    story.append(Paragraph("Patient Information", subheader_style))
    
    demo_data = [["Field", "Information"]]
    for label, data in patient_data.get("demographic", {}).items():
        # Don't include sensitive info like password
        if label.lower() not in ["password", "pwd"]:
            demo_data.append([
                Paragraph(f"<b>{label.capitalize()}</b>", normal_style),
                Paragraph(str(data), normal_style)
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
        story.append(Paragraph("Clinical Summary", subheader_style))
        summary_para = Paragraph(patient_data["summary"], normal_style)
        story.append(summary_para)
        story.append(Spacer(1, 0.3*inch))
    
    # Symptoms
    story.append(Paragraph("Reported Symptoms", subheader_style))
    
    symptoms_data = [["Symptom", "Duration", "Severity", "Frequency", "Additional Notes"]]
    
    for symptom, details in patient_data.get("per_symptom", {}).items():
        row = [
            Paragraph(f"<b>{symptom.upper()}</b>", normal_style),
            Paragraph(str(details.get("Duration", "N/A")), normal_style),
            Paragraph(str(details.get("Severity", "N/A")), normal_style),
            Paragraph(str(details.get("Frequency", "N/A")), normal_style),
            Paragraph(str(details.get("Additional Notes", "N/A")), normal_style)
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
    story.append(Paragraph("General Health Information", subheader_style))
    
    gen_health_data = [["Question", "Answer"]]
    
    for question, answer in patient_data.get("Gen_questions", {}).items():
        gen_health_data.append([
            Paragraph(f"<b>{question}</b>", normal_style),
            Paragraph(str(answer), normal_style)
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
    disclaimer = Paragraph(
        "<i><b>Disclaimer:</b> This report is for informational purposes only and does not constitute medical advice. "
        "Please consult with a qualified healthcare professional for proper diagnosis and treatment.</i>",
        normal_style
    )
    story.append(disclaimer)
    
    # Build PDF
    doc.build(story)
    
    # Reset buffer position
    buffer.seek(0)
    
    return buffer