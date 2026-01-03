"""
ULTIMATE MULTILINGUAL PDF GENERATOR - FIXED VERSION WITH GUJARATI
✅ Now includes proper Gujarati font support
✅ All other languages preserved
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
import urllib.request
import tempfile


def download_noto_fonts():
    """
    Download Google Noto Sans fonts - FIXED with Gujarati
    """
    fonts_dir = os.path.join(tempfile.gettempdir(), "noto_fonts")
    os.makedirs(fonts_dir, exist_ok=True)
    
    # ✅ FIXED: Added Gujarati font
    font_urls = {
        # Base Latin font
        'NotoSans-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/notosans/NotoSans%5Bwdth%2Cwght%5D.ttf',
        
        # Hindi (Devanagari)
        'NotoSansDevanagari-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/notosansdevanagari/NotoSansDevanagari%5Bwdth%2Cwght%5D.ttf',
        
        # ✅ NEW: Gujarati (separate from Devanagari!)
        'NotoSansGujarati-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/notosansgujarati/NotoSansGujarati%5Bwdth%2Cwght%5D.ttf',
        
        # Arabic
        'NotoSansArabic-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/notosansarabic/NotoSansArabic%5Bwdth%2Cwght%5D.ttf',
        
        # Korean
        'NotoSansKR-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR%5Bwght%5D.ttf',
        
        # Chinese Simplified
        'NotoSansSC-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf',
        
        # Japanese
        'NotoSansJP-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf',
        
        # Thai
        'NotoSansThai-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/notosansthai/NotoSansThai%5Bwdth%2Cwght%5D.ttf',
        
        # Hebrew
        'NotoSansHebrew-Regular.ttf': 'https://github.com/google/fonts/raw/main/ofl/notosanshebrew/NotoSansHebrew%5Bwdth%2Cwght%5D.ttf',
    }
    
    downloaded_fonts = {}
    
    for font_name, url in font_urls.items():
        font_path = os.path.join(fonts_dir, font_name)
        
        # Skip if already downloaded
        if os.path.exists(font_path) and os.path.getsize(font_path) > 0:
            print(f"✅ {font_name} already exists")
            downloaded_fonts[font_name] = font_path
            continue
        
        # Download font
        try:
            print(f"📥 Downloading {font_name}...")
            
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                font_data = response.read()
                
                if len(font_data) < 1000:
                    print(f"⚠️  {font_name} download too small, skipping")
                    continue
                
                with open(font_path, 'wb') as f:
                    f.write(font_data)
                
                print(f"✅ Downloaded {font_name} ({len(font_data) // 1024} KB)")
                downloaded_fonts[font_name] = font_path
        
        except Exception as e:
            print(f"⚠️  Failed to download {font_name}: {e}")
    
    if downloaded_fonts:
        print(f"\n✅ Successfully downloaded {len(downloaded_fonts)} fonts")
    else:
        print("\n⚠️  No fonts downloaded - will use system fonts")
    
    return downloaded_fonts


def setup_multilingual_fonts():
    """
    Setup fonts with Gujarati support added
    """
    
    # Try to download Noto fonts
    try:
        noto_fonts = download_noto_fonts()
        
        if noto_fonts:
            registered_count = 0
            
            # Register base Latin font
            if 'NotoSans-Regular.ttf' in noto_fonts:
                try:
                    pdfmetrics.registerFont(TTFont('MultiLang', noto_fonts['NotoSans-Regular.ttf']))
                    pdfmetrics.registerFont(TTFont('MultiLang-Bold', noto_fonts['NotoSans-Regular.ttf']))
                    registered_count += 1
                    print("✅ Registered: Base Latin font")
                except Exception as e:
                    print(f"⚠️  Failed to register base font: {e}")
            
            # Register Hindi (Devanagari)
            if 'NotoSansDevanagari-Regular.ttf' in noto_fonts:
                try:
                    pdfmetrics.registerFont(TTFont('MultiLang-Hindi', noto_fonts['NotoSansDevanagari-Regular.ttf']))
                    registered_count += 1
                    print("✅ Registered: Hindi (Devanagari)")
                except Exception as e:
                    print(f"⚠️  Failed to register Hindi font: {e}")
            
            # ✅ NEW: Register Gujarati (critical fix!)
            if 'NotoSansGujarati-Regular.ttf' in noto_fonts:
                try:
                    pdfmetrics.registerFont(TTFont('MultiLang-Gujarati', noto_fonts['NotoSansGujarati-Regular.ttf']))
                    registered_count += 1
                    print("✅ Registered: Gujarati")
                except Exception as e:
                    print(f"⚠️  Failed to register Gujarati font: {e}")
            
            # Register Arabic
            if 'NotoSansArabic-Regular.ttf' in noto_fonts:
                try:
                    pdfmetrics.registerFont(TTFont('MultiLang-Arabic', noto_fonts['NotoSansArabic-Regular.ttf']))
                    registered_count += 1
                    print("✅ Registered: Arabic")
                except Exception as e:
                    print(f"⚠️  Failed to register Arabic font: {e}")
            
            # Register Korean
            if 'NotoSansKR-Regular.ttf' in noto_fonts:
                try:
                    pdfmetrics.registerFont(TTFont('MultiLang-Korean', noto_fonts['NotoSansKR-Regular.ttf']))
                    registered_count += 1
                    print("✅ Registered: Korean")
                except Exception as e:
                    print(f"⚠️  Failed to register Korean font: {e}")
            
            # Register Chinese
            if 'NotoSansSC-Regular.ttf' in noto_fonts:
                try:
                    pdfmetrics.registerFont(TTFont('MultiLang-Chinese', noto_fonts['NotoSansSC-Regular.ttf']))
                    registered_count += 1
                    print("✅ Registered: Chinese (Simplified)")
                except Exception as e:
                    print(f"⚠️  Failed to register Chinese font: {e}")
            
            # Register Japanese
            if 'NotoSansJP-Regular.ttf' in noto_fonts:
                try:
                    pdfmetrics.registerFont(TTFont('MultiLang-Japanese', noto_fonts['NotoSansJP-Regular.ttf']))
                    registered_count += 1
                    print("✅ Registered: Japanese")
                except Exception as e:
                    print(f"⚠️  Failed to register Japanese font: {e}")
            
            # Register Thai
            if 'NotoSansThai-Regular.ttf' in noto_fonts:
                try:
                    pdfmetrics.registerFont(TTFont('MultiLang-Thai', noto_fonts['NotoSansThai-Regular.ttf']))
                    registered_count += 1
                    print("✅ Registered: Thai")
                except Exception as e:
                    print(f"⚠️  Failed to register Thai font: {e}")
            
            # Register Hebrew
            if 'NotoSansHebrew-Regular.ttf' in noto_fonts:
                try:
                    pdfmetrics.registerFont(TTFont('MultiLang-Hebrew', noto_fonts['NotoSansHebrew-Regular.ttf']))
                    registered_count += 1
                    print("✅ Registered: Hebrew")
                except Exception as e:
                    print(f"⚠️  Failed to register Hebrew font: {e}")
            
            if registered_count > 0:
                print(f"\n✅ Successfully registered {registered_count} fonts!")
                return True, 'MultiLang', 'MultiLang-Bold'
    
    except Exception as e:
        print(f"⚠️  Font download/registration failed: {e}")
    
    # Fallback to system fonts
    print("\n🔄 Trying system fonts...")
    
    system_fonts = [
        # Windows
        {
            'name': 'Arial Unicode MS',
            'regular': [
                'C:\\Windows\\Fonts\\ARIALUNI.TTF',
                'C:\\Windows\\Fonts\\arialuni.ttf',
            ]
        },
        # Linux
        {
            'name': 'Noto Sans',
            'regular': [
                '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
                '/usr/share/fonts/noto/NotoSans-Regular.ttf',
            ]
        },
        # Mac
        {
            'name': 'Arial Unicode MS',
            'regular': [
                '/Library/Fonts/Arial Unicode.ttf',
                '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
            ]
        },
    ]
    
    for font_info in system_fonts:
        for path in font_info['regular']:
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont('MultiLang', path))
                    pdfmetrics.registerFont(TTFont('MultiLang-Bold', path))
                    print(f"✅ Using system font: {font_info['name']}")
                    return True, 'MultiLang', 'MultiLang-Bold'
                except Exception as e:
                    continue
    
    print("⚠️  Using Helvetica (limited Unicode support)")
    return False, 'Helvetica', 'Helvetica-Bold'


def detect_script(text):
    """
    ✅ FIXED: Now properly detects Gujarati separately from Hindi
    """
    if not text:
        return 'latin'
    
    script_counts = {
        'arabic': 0, 'hindi': 0, 'gujarati': 0, 'korean': 0, 'chinese': 0,
        'japanese': 0, 'thai': 0, 'hebrew': 0, 'latin': 0
    }
    
    for char in str(text):
        code = ord(char)
        
        # Arabic
        if 0x0600 <= code <= 0x06FF or 0xFB50 <= code <= 0xFDFF or 0xFE70 <= code <= 0xFEFF:
            script_counts['arabic'] += 1
        
        # ✅ CRITICAL FIX: Gujarati BEFORE Devanagari (more specific range)
        # Gujarati Unicode range: U+0A80 to U+0AFF
        elif 0x0A80 <= code <= 0x0AFF:
            script_counts['gujarati'] += 1
        
        # Devanagari (Hindi, Marathi, Sanskrit) - U+0900 to U+097F
        elif 0x0900 <= code <= 0x097F:
            script_counts['hindi'] += 1
        
        # Korean (Hangul)
        elif 0xAC00 <= code <= 0xD7AF or 0x1100 <= code <= 0x11FF:
            script_counts['korean'] += 1
        
        # Chinese (CJK Unified Ideographs)
        elif 0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF:
            script_counts['chinese'] += 1
        
        # Japanese (Hiragana, Katakana)
        elif 0x3040 <= code <= 0x309F or 0x30A0 <= code <= 0x30FF:
            script_counts['japanese'] += 1
        
        # Thai
        elif 0x0E00 <= code <= 0x0E7F:
            script_counts['thai'] += 1
        
        # Hebrew
        elif 0x0590 <= code <= 0x05FF:
            script_counts['hebrew'] += 1
        
        # Latin
        elif (0x0041 <= code <= 0x005A) or (0x0061 <= code <= 0x007A):
            script_counts['latin'] += 1
    
    # Return script with highest count
    max_script = max(script_counts, key=script_counts.get)
    
    if script_counts[max_script] == 0:
        return 'latin'
    
    return max_script


def is_rtl_text(text):
    """Check if text is Right-to-Left"""
    script = detect_script(text)
    return script in ['arabic', 'hebrew']


def get_font_for_text(text, is_bold=False):
    """
    ✅ FIXED: Now properly selects Gujarati font
    """
    script = detect_script(text)
    
    # Map scripts to fonts
    font_map = {
        'arabic': 'MultiLang-Arabic',
        'hindi': 'MultiLang-Hindi',
        'gujarati': 'MultiLang-Gujarati',  # ✅ NEW: Separate Gujarati font
        'korean': 'MultiLang-Korean',
        'chinese': 'MultiLang-Chinese',
        'japanese': 'MultiLang-Japanese',
        'thai': 'MultiLang-Thai',
        'hebrew': 'MultiLang-Hebrew',
        'latin': 'MultiLang-Bold' if is_bold else 'MultiLang',
    }
    
    selected_font = font_map.get(script, 'MultiLang')
    
    # Check if font is registered
    try:
        pdfmetrics.getFont(selected_font)
        return selected_font
    except:
        try:
            pdfmetrics.getFont('MultiLang')
            return 'MultiLang-Bold' if is_bold else 'MultiLang'
        except:
            return 'Helvetica-Bold' if is_bold else 'Helvetica'


def reshape_arabic_text(text):
    """Reshape Arabic text for proper display"""
    if not text:
        return text
    
    try:
        if not is_rtl_text(text):
            return text
        
        import arabic_reshaper
        from bidi.algorithm import get_display
        
        reshaped = arabic_reshaper.reshape(str(text))
        bidi_text = get_display(reshaped)
        return bidi_text
    
    except ImportError:
        print("⚠️  arabic-reshaper/python-bidi not installed")
        return text
    except Exception as e:
        print(f"⚠️  Arabic reshaping error: {e}")
        return text


def create_multilingual_paragraph(text, style, is_bold=False, has_font=True):
    """
    Create paragraph with automatic font selection (now includes Gujarati)
    """
    if not text:
        return Paragraph("", style)
    
    # Process RTL text
    processed_text = reshape_arabic_text(str(text))
    
    # Detect script and select font
    font_name = get_font_for_text(text, is_bold)
    alignment = TA_RIGHT if is_rtl_text(text) else TA_LEFT
    
    if has_font:
        custom_style = ParagraphStyle(
            name='CustomMultilang',
            parent=style,
            fontName=font_name,
            fontSize=getattr(style, 'fontSize', 10),
            wordWrap='CJK',
            alignment=alignment,
            leading=getattr(style, 'leading', 12),
        )
        
        return Paragraph(processed_text, custom_style)
    else:
        fallback_style = ParagraphStyle(
            name='Fallback',
            parent=style,
            alignment=alignment,
        )
        return Paragraph(processed_text, fallback_style)


def create_safe_filename(original_name: str, fallback: str = "Patient") -> tuple:
    """Create both Unicode filename AND ASCII fallback"""
    import re
    
    # Clean the original name
    unicode_filename = re.sub(r'[<>:"/\\|?*]', '', original_name)
    unicode_filename = unicode_filename.strip() or fallback
    
    # Create ASCII fallback
    ascii_filename = create_ascii_fallback(unicode_filename, fallback)
    
    return unicode_filename, ascii_filename


def create_ascii_fallback(text: str, fallback: str = "Patient") -> str:
    """Create ASCII-safe filename with intelligent transliteration"""
    import unicodedata
    import re
    
    # Unicode normalization
    try:
        nfd = unicodedata.normalize('NFD', text)
        ascii_text = ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
        ascii_text = re.sub(r'[^a-zA-Z0-9\s]', '', ascii_text)
        ascii_text = re.sub(r'\s+', '_', ascii_text.strip())
        
        if ascii_text and len(ascii_text) >= 2:
            return ascii_text
    except:
        pass
    
    # Try Unidecode
    try:
        from unidecode import unidecode
        transliterated = unidecode(text)
        transliterated = re.sub(r'[^a-zA-Z0-9\s]', '', transliterated)
        transliterated = re.sub(r'\s+', '_', transliterated.strip())
        
        if transliterated and len(transliterated) >= 2:
            return transliterated
    except:
        pass
    
    # Extract Latin characters
    latin_chars = re.findall(r'[a-zA-Z0-9]+', text)
    if latin_chars:
        extracted = '_'.join(latin_chars)
        if len(extracted) >= 2:
            return extracted
    
    return fallback


def generate_patient_pdf(patient_data):
    """
    Generate PDF with full multilingual support including Gujarati
    """
    from urllib.parse import quote
    
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
    
    # Setup fonts
    has_font, font_regular, font_bold = setup_multilingual_fonts()
    
    # Get styles
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
    
    # Title
    title = create_multilingual_paragraph(
        "PATIENT HEALTH ASSESSMENT REPORT",
        header_style,
        is_bold=True,
        has_font=has_font
    )
    story.append(title)
    story.append(Spacer(1, 0.2 * inch))
    
    # Date
    date_str = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    date_para = create_multilingual_paragraph(
        f"<i>Generated on: {date_str}</i>",
        normal_style,
        has_font=has_font
    )
    story.append(date_para)
    story.append(Spacer(1, 0.3 * inch))
    
    # Patient Information
    story.append(create_multilingual_paragraph(
        "Patient Information",
        subheader_style,
        is_bold=True,
        has_font=has_font
    ))
    
    demo_data = [[
        create_multilingual_paragraph("<b>Field</b>", normal_style, True, has_font),
        create_multilingual_paragraph("<b>Information</b>", normal_style, True, has_font)
    ]]
    
    for field, value in patient_data.get("demographic", {}).items():
        if field.lower() not in ["password", "pwd"]:
            demo_data.append([
                create_multilingual_paragraph(f"<b>{field.capitalize()}</b>", normal_style, True, has_font),
                create_multilingual_paragraph(str(value), normal_style, False, has_font)
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
    
    # Clinical Summary
    if "summary" in patient_data and patient_data["summary"]:
        story.append(create_multilingual_paragraph(
            "Clinical Summary",
            subheader_style,
            is_bold=True,
            has_font=has_font
        ))
        
        summary_para = create_multilingual_paragraph(
            str(patient_data["summary"]),
            normal_style,
            has_font=has_font
        )
        story.append(summary_para)
        story.append(Spacer(1, 0.3 * inch))
    
    # Symptoms
    story.append(create_multilingual_paragraph(
        "Reported Symptoms",
        subheader_style,
        is_bold=True,
        has_font=has_font
    ))
    
    symptoms_data = [[
        create_multilingual_paragraph("<b>Symptom</b>", normal_style, True, has_font),
        create_multilingual_paragraph("<b>Duration</b>", normal_style, True, has_font),
        create_multilingual_paragraph("<b>Severity</b>", normal_style, True, has_font),
        create_multilingual_paragraph("<b>Frequency</b>", normal_style, True, has_font),
        create_multilingual_paragraph("<b>Additional Notes</b>", normal_style, True, has_font)
    ]]
    
    for symptom, details in patient_data.get("per_symptom", {}).items():
        row = [
            create_multilingual_paragraph(f"<b>{symptom.upper()}</b>", normal_style, True, has_font),
            create_multilingual_paragraph(str(details.get("Duration", "N/A")), normal_style, False, has_font),
            create_multilingual_paragraph(str(details.get("Severity", "N/A")), normal_style, False, has_font),
            create_multilingual_paragraph(str(details.get("Frequency", "N/A")), normal_style, False, has_font),
            create_multilingual_paragraph(str(details.get("Additional Notes", "N/A")), normal_style, False, has_font)
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
    
    # Health Information
    story.append(create_multilingual_paragraph(
        "General Health Information",
        subheader_style,
        is_bold=True,
        has_font=has_font
    ))
    
    health_data = [[
        create_multilingual_paragraph("<b>Question</b>", normal_style, True, has_font),
        create_multilingual_paragraph("<b>Answer</b>", normal_style, True, has_font)
    ]]
    
    for question, answer in patient_data.get("Gen_questions", {}).items():
        health_data.append([
            create_multilingual_paragraph(f"<b>{question}</b>", normal_style, True, has_font),
            create_multilingual_paragraph(str(answer), normal_style, False, has_font)
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
    disclaimer_text = (
        "<i><b>Disclaimer:</b> This report is for informational purposes only and does not "
        "constitute medical advice. Please consult with a qualified healthcare professional "
        "for proper diagnosis and treatment.</i>"
    )
    disclaimer = create_multilingual_paragraph(disclaimer_text, normal_style, has_font=has_font)
    story.append(disclaimer)
    
    # === BUILD PDF ===
    try:
        doc.build(story)
        print("✅ PDF generated successfully with multilingual support!")
    except Exception as e:
        print(f"❌ PDF generation error: {e}")
        import traceback
        traceback.print_exc()
        
        # Create error PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = [
            Paragraph("PATIENT HEALTH ASSESSMENT REPORT", styles['Heading1']),
            Paragraph(f"<i>Error: Could not render some characters. Missing fonts for: {detect_script(str(patient_data))}</i>", styles['Normal']),
        ]
        doc.build(story)
    
    buffer.seek(0)
    return buffer