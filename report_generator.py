"""
PDF Report Generator for Life Care Pathology Lab
Uses ReportLab for PDF generation. Matches new Navy Blue theme.
"""
import os
import io
import qrcode
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Theme Colors
THEME_DARK = colors.HexColor('#1a1a2e')
THEME_LIGHT = colors.HexColor('#f0f4ff')
THEME_ACCENT = colors.HexColor('#3B82F6')
TEXT_DARK = colors.HexColor('#0F172A')

def generate_qr_code(url, size=25):
    """Generate a QR code image from a URL."""
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=0)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return Image(buffer, width=size * mm, height=size * mm)


def generate_report_pdf(report_data, output_path, download_url=""):
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=10 * mm, bottomMargin=15 * mm,
        leftMargin=10 * mm, rightMargin=10 * mm
    )

    styles = getSampleStyleSheet()
    elements = []

    # Custom styles
    header_style = ParagraphStyle('LabHeader', parent=styles['Title'],
                                   fontSize=24, textColor=THEME_DARK,
                                   fontName='Helvetica-Bold',
                                   spaceAfter=2 * mm, leading=28, alignment=TA_CENTER)
    
    sub_header = ParagraphStyle('SubHeader', parent=styles['Normal'],
                                 fontSize=11, textColor=colors.HexColor('#64748B'),
                                 alignment=TA_CENTER, spaceAfter=2 * mm)
    
    section_title = ParagraphStyle('SectionTitle', parent=styles['Normal'],
                                    fontSize=12, textColor=colors.white,
                                    backColor=THEME_DARK,
                                    spaceBefore=4 * mm, spaceAfter=2 * mm,
                                    leading=18, alignment=TA_CENTER,
                                    borderPadding=6, textTransform='uppercase')
                                    
    normal_style = ParagraphStyle('NormalCustom', parent=styles['Normal'],
                                   fontSize=10, leading=14, textColor=TEXT_DARK)
                                   
    bold_style = ParagraphStyle('BoldText', parent=styles['Normal'],
                                 fontSize=10, leading=14, textColor=TEXT_DARK,
                                 fontName='Helvetica-Bold')

    # ── Lab Header ──
    elements.append(Paragraph("LIFE CARE PATHOLOGY LAB", header_style))
    elements.append(Paragraph(
        "Near Rickshaw Stand, Vill. Asara (Baghpat) 250623 | Phone: +91 9058275073",
        sub_header
    ))
    elements.append(HRFlowable(width="100%", thickness=2, color=THEME_DARK,
                                spaceAfter=5 * mm, spaceBefore=2 * mm))

    # ── Patient Info ──
    elements.append(Paragraph("PATIENT INFORMATION", section_title))

    report_date = datetime.utcnow().strftime('%d/%m/%Y %I:%M %p')
    
    # Grid layout for patient info
    p_data = [
        [Paragraph("<b>Patient Name</b>", bold_style), Paragraph(report_data.get('patient_name', 'N/A'), normal_style),
         Paragraph("<b>Report ID</b>", bold_style), Paragraph(report_data.get('report_id', 'N/A'), normal_style)],
        
        [Paragraph("<b>Age / Gender</b>", bold_style), Paragraph(f"{report_data.get('age', 'N/A')} Yrs / {report_data.get('gender', 'N/A')}", normal_style),
         Paragraph("<b>Date</b>", bold_style), Paragraph(report_date, normal_style)],
         
        [Paragraph("<b>Ref. Doctor</b>", bold_style), Paragraph(report_data.get('doctor_name', 'Self'), normal_style),
         Paragraph("<b>Sample ID</b>", bold_style), Paragraph(report_data.get('token_number', 'N/A'), normal_style)],
         
        [Paragraph("<b>Test Name</b>", bold_style), Paragraph(f"<b>{report_data.get('test_name', 'N/A')}</b>", normal_style),
         Paragraph("", normal_style), Paragraph("", normal_style)]
    ]

    p_table = Table(p_data, colWidths=[35*mm, 60*mm, 30*mm, 60*mm])
    p_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), THEME_DARK), # Label col 1
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('BACKGROUND', (2, 0), (2, -1), THEME_DARK), # Label col 2
        ('TEXTCOLOR', (2, 0), (2, -1), colors.white),
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (3, 0), (3, -1), colors.HexColor('#F8FAFC')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(p_table)
    elements.append(Spacer(1, 5 * mm))

    # ── Test Results ──
    elements.append(Paragraph(f"TEST RESULTS — {report_data.get('test_name', '').upper()}", section_title))

    test_results = report_data.get('test_results', [])
    if test_results:
        # Header
        t_data = [[
            Paragraph("<b>#</b>", ParagraphStyle('TH', parent=bold_style, textColor=colors.white)),
            Paragraph("<b>Parameter</b>", ParagraphStyle('TH', parent=bold_style, textColor=colors.white)),
            Paragraph("<b>Result</b>", ParagraphStyle('TH', parent=bold_style, textColor=colors.white)),
            Paragraph("<b>Unit</b>", ParagraphStyle('TH', parent=bold_style, textColor=colors.white)),
            Paragraph("<b>Normal Range</b>", ParagraphStyle('TH', parent=bold_style, textColor=colors.white))
        ]]

        for idx, result in enumerate(test_results, 1):
            val = str(result.get('value', ''))
            rng = str(result.get('normal_range', ''))
            
            # Logic for abnormal
            is_abnormal = False
            try:
                v = float(val)
                if '-' in rng:
                    parts = rng.split('-')
                    if len(parts) == 2:
                        lo, hi = float(parts[0]), float(parts[1])
                        if v < lo or v > hi:
                            is_abnormal = True
            except:
                pass
            
            val_style = ParagraphStyle('Abnormal', parent=bold_style, textColor=colors.HexColor('#DC2626')) if is_abnormal else normal_style
            val_txt = f"{val} *" if is_abnormal else val

            t_data.append([
                str(idx),
                Paragraph(str(result.get('parameter', '')), normal_style),
                Paragraph(val_txt, val_style),
                Paragraph(str(result.get('unit', '')), normal_style),
                Paragraph(rng, normal_style),
            ])

        # Column widths matching preview approx
        r_table = Table(t_data, colWidths=[15*mm, 70*mm, 35*mm, 25*mm, 45*mm], repeatRows=1)
        r_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), THEME_DARK),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, THEME_LIGHT]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'), # Parameters left align
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(r_table)
    else:
        elements.append(Paragraph("No results recorded.", normal_style))

    elements.append(Spacer(1, 5 * mm))

    # ── Remarks ──
    if report_data.get('remarks'):
        elements.append(Paragraph(f"<b>Remarks:</b> {report_data['remarks']}", normal_style))
        elements.append(Spacer(1, 5 * mm))

    # ── Disclaimer & Footer ──
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceBefore=10*mm, spaceAfter=2*mm))
    
    footer_text = "This is a computer-generated report. Results are indicative."
    elements.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.gray, alignment=TA_CENTER)))

    # QR Code at very bottom if URL present
    if download_url:
        qr = generate_qr_code(download_url, size=20)
        # Put in a small table to align right or center
        qr_table = Table([[Paragraph("Scan to Download", ParagraphStyle('Tiny', fontSize=7, alignment=TA_RIGHT)), qr]], colWidths=[160*mm, 25*mm])
        qr_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (1,0), (1,0), 'RIGHT')]))
        elements.append(qr_table)

    # Build
    # Build
    if os.path.dirname(output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.build(elements)
    return output_path
