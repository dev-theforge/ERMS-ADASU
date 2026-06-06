"""PDF generation for result slips and transcripts using ReportLab."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from django.utils import timezone

NAVY = colors.HexColor('#1B2B5A')
TEAL = colors.HexColor('#0D7377')
LIGHT_GREY = colors.HexColor('#F5F7FA')
MID_GREY = colors.HexColor('#CBD5E0')
WHITE = colors.white
BLACK = colors.black


def _get_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('UnivTitle', fontName='Helvetica-Bold', fontSize=14, textColor=NAVY, alignment=TA_CENTER, spaceAfter=2))
    styles.add(ParagraphStyle('UnivSub', fontName='Helvetica', fontSize=9, textColor=TEAL, alignment=TA_CENTER, spaceAfter=8))
    styles.add(ParagraphStyle('DocTitle', fontName='Helvetica-Bold', fontSize=12, textColor=NAVY, alignment=TA_CENTER, spaceAfter=6))
    styles.add(ParagraphStyle('Label', fontName='Helvetica-Bold', fontSize=9, textColor=NAVY))
    styles.add(ParagraphStyle('Value', fontName='Helvetica', fontSize=9, textColor=BLACK))
    styles.add(ParagraphStyle('Small', fontName='Helvetica', fontSize=8, textColor=colors.grey))
    styles.add(ParagraphStyle('Footer', fontName='Helvetica-Oblique', fontSize=7, textColor=colors.grey, alignment=TA_CENTER))
    return styles


def generate_result_slip(buffer, student, semester, results, gpa_obj):
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm, leftMargin=2*cm, rightMargin=2*cm)
    styles = _get_styles()
    story = []

    # Header
    story.append(Paragraph("REV. FR. MOSES ORSHIO ADASU UNIVERSITY", styles['UnivTitle']))
    story.append(Paragraph("Makurdi, Benue State, Nigeria", styles['UnivSub']))
    story.append(Paragraph("EXAMINATION RESULT SLIP", styles['DocTitle']))
    story.append(HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=8))

    # Student info table
    info_data = [
        [Paragraph('<b>Student Name:</b>', styles['Label']), Paragraph(student.user.get_full_name(), styles['Value']),
         Paragraph('<b>Matric No:</b>', styles['Label']), Paragraph(student.matric_number, styles['Value'])],
        [Paragraph('<b>Department:</b>', styles['Label']), Paragraph(str(student.department), styles['Value']),
         Paragraph('<b>Level:</b>', styles['Label']), Paragraph(f"{student.level} Level", styles['Value'])],
        [Paragraph('<b>Faculty:</b>', styles['Label']), Paragraph(str(student.department.faculty), styles['Value']),
         Paragraph('<b>Semester:</b>', styles['Label']), Paragraph(str(semester), styles['Value'])],
    ]
    info_table = Table(info_data, colWidths=[3.5*cm, 6*cm, 3*cm, 4.5*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_GREY),
        ('BOX', (0,0), (-1,-1), 0.5, MID_GREY),
        ('INNERGRID', (0,0), (-1,-1), 0.25, MID_GREY),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.4*cm))

    # Results table
    headers = ['Course Code', 'Course Title', 'Credit Units', 'Score', 'Grade', 'Grade Point', 'Quality Points']
    header_row = [Paragraph(f'<b>{h}</b>', ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=8, textColor=WHITE, alignment=TA_CENTER)) for h in headers]
    table_data = [header_row]

    total_cu = 0
    total_qp = 0
    for r in results:
        table_data.append([
            Paragraph(r.course.code, styles['Value']),
            Paragraph(r.course.title, styles['Value']),
            Paragraph(str(r.course.credit_units), ParagraphStyle('Center', fontName='Helvetica', fontSize=9, alignment=TA_CENTER)),
            Paragraph(str(r.score), ParagraphStyle('Center', fontName='Helvetica', fontSize=9, alignment=TA_CENTER)),
            Paragraph(r.grade, ParagraphStyle('Center', fontName='Helvetica-Bold', fontSize=9, alignment=TA_CENTER)),
            Paragraph(str(r.grade_point), ParagraphStyle('Center', fontName='Helvetica', fontSize=9, alignment=TA_CENTER)),
            Paragraph(str(r.quality_points), ParagraphStyle('Center', fontName='Helvetica', fontSize=9, alignment=TA_CENTER)),
        ])
        total_cu += r.course.credit_units
        total_qp += float(r.quality_points)

    results_table = Table(table_data, colWidths=[2.5*cm, 6.5*cm, 2*cm, 1.8*cm, 1.5*cm, 2.2*cm, 2.5*cm])
    results_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT_GREY]),
        ('BOX', (0,0), (-1,-1), 0.5, MID_GREY),
        ('INNERGRID', (0,0), (-1,-1), 0.25, MID_GREY),
        ('PADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(results_table)
    story.append(Spacer(1, 0.4*cm))

    # GPA Summary
    gpa = gpa_obj.gpa if gpa_obj else 0
    summary_data = [
        [Paragraph('<b>Total Credit Units</b>', styles['Label']), Paragraph(str(total_cu), styles['Value']),
         Paragraph('<b>Total Quality Points</b>', styles['Label']), Paragraph(f"{total_qp:.2f}", styles['Value']),
         Paragraph('<b>GPA</b>', styles['Label']), Paragraph(f"<b>{gpa:.2f}</b>", ParagraphStyle('GPA', fontName='Helvetica-Bold', fontSize=11, textColor=TEAL))],
    ]
    summary_table = Table(summary_data, colWidths=[4*cm, 2.5*cm, 4*cm, 2.5*cm, 2*cm, 2*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EEF2FF')),
        ('BOX', (0,0), (-1,-1), 1, NAVY),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=MID_GREY))
    story.append(Paragraph(f"Generated on {timezone.now().strftime('%d %B %Y at %H:%M')} | Official Result Slip — Rev. Fr. Moses Orshio Adasu University", styles['Footer']))
    doc.build(story)


def generate_transcript(buffer, student, all_results, gpa_records, cgpa_obj):
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm, leftMargin=2*cm, rightMargin=2*cm)
    styles = _get_styles()
    story = []

    story.append(Paragraph("REV. FR. MOSES ORSHIO ADASU UNIVERSITY", styles['UnivTitle']))
    story.append(Paragraph("Makurdi, Benue State, Nigeria", styles['UnivSub']))
    story.append(Paragraph("OFFICIAL ACADEMIC TRANSCRIPT", styles['DocTitle']))
    story.append(HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=8))

    # Student info
    cgpa = cgpa_obj.cgpa if cgpa_obj else 0
    info_data = [
        [Paragraph('<b>Full Name:</b>', styles['Label']), Paragraph(student.user.get_full_name(), styles['Value']),
         Paragraph('<b>Matric No:</b>', styles['Label']), Paragraph(student.matric_number, styles['Value'])],
        [Paragraph('<b>Department:</b>', styles['Label']), Paragraph(str(student.department), styles['Value']),
         Paragraph('<b>Faculty:</b>', styles['Label']), Paragraph(str(student.department.faculty), styles['Value'])],
        [Paragraph('<b>Entry Year:</b>', styles['Label']), Paragraph(str(student.admission_year), styles['Value']),
         Paragraph('<b>CGPA:</b>', styles['Label']), Paragraph(f"<b>{cgpa:.2f}</b>", ParagraphStyle('CGPA', fontName='Helvetica-Bold', fontSize=10, textColor=TEAL))],
    ]
    info_table = Table(info_data, colWidths=[3.5*cm, 6*cm, 3*cm, 4.5*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_GREY),
        ('BOX', (0,0), (-1,-1), 0.5, MID_GREY),
        ('INNERGRID', (0,0), (-1,-1), 0.25, MID_GREY),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.5*cm))

    # Group results by semester
    from itertools import groupby
    results_by_sem = {}
    for r in all_results:
        key = str(r.semester)
        if key not in results_by_sem:
            results_by_sem[key] = {'semester': r.semester, 'results': []}
        results_by_sem[key]['results'].append(r)

    for sem_key, data in results_by_sem.items():
        sem = data['semester']
        gpa_r = next((g for g in gpa_records if g.semester_id == sem.pk), None)
        story.append(Paragraph(f"<b>{sem_key}</b>", ParagraphStyle('SemHeader', fontName='Helvetica-Bold', fontSize=10, textColor=NAVY, backColor=LIGHT_GREY, borderPad=4)))
        story.append(Spacer(1, 0.1*cm))

        headers = ['Course Code', 'Course Title', 'CU', 'Score', 'Grade', 'GP', 'QP']
        hrow = [Paragraph(f'<b>{h}</b>', ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=8, textColor=WHITE, alignment=TA_CENTER)) for h in headers]
        tdata = [hrow]
        for r in data['results']:
            tdata.append([r.course.code, r.course.title, str(r.course.credit_units), str(r.score), r.grade, str(r.grade_point), str(r.quality_points)])

        sem_gpa = gpa_r.gpa if gpa_r else 0
        tdata.append(['', Paragraph('<b>Semester GPA</b>', styles['Label']), '', '', '', '', Paragraph(f'<b>{sem_gpa:.2f}</b>', ParagraphStyle('GPA2', fontName='Helvetica-Bold', fontSize=9, textColor=TEAL))])

        t = Table(tdata, colWidths=[2.5*cm, 7*cm, 1.5*cm, 1.8*cm, 1.5*cm, 1.5*cm, 1.7*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), NAVY),
            ('ROWBACKGROUNDS', (0,1), (-1,-2), [WHITE, LIGHT_GREY]),
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#EEF2FF')),
            ('BOX', (0,0), (-1,-1), 0.5, MID_GREY),
            ('INNERGRID', (0,0), (-1,-1), 0.25, MID_GREY),
            ('PADDING', (0,0), (-1,-1), 4),
            ('FONTSIZE', (0,1), (-1,-1), 8),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.3*cm))

    story.append(Spacer(1, 0.5*cm))
    # CGPA summary
    summary = Table([[
        Paragraph('<b>Cumulative Credit Units:</b>', styles['Label']),
        Paragraph(str(cgpa_obj.total_accumulated_credit_units if cgpa_obj else 0), styles['Value']),
        Paragraph('<b>Cumulative Quality Points:</b>', styles['Label']),
        Paragraph(str(cgpa_obj.total_accumulated_quality_points if cgpa_obj else 0), styles['Value']),
        Paragraph('<b>CGPA:</b>', styles['Label']),
        Paragraph(f"<b>{cgpa:.2f}</b>", ParagraphStyle('CGPA2', fontName='Helvetica-Bold', fontSize=12, textColor=TEAL)),
    ]], colWidths=[4.5*cm, 2*cm, 4.5*cm, 2*cm, 2*cm, 2*cm])
    summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EEF2FF')),
        ('BOX', (0,0), (-1,-1), 1.5, NAVY),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(summary)
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=MID_GREY))
    story.append(Paragraph(f"This is an official transcript issued by Rev. Fr. Moses Orshio Adasu University, Makurdi. Generated: {timezone.now().strftime('%d %B %Y')}", styles['Footer']))
    doc.build(story)
