import os
import re
import logging
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime

logger = logging.getLogger(__name__)


class DeliveryNoteGenerator:
    """Generate Delivery Note with Alshaya branded template"""

    # Alshaya brand colors
    GOLD = '#d4af37'
    DARK_NAVY = '#1a365d'
    LIGHT_GRAY = '#f8f9fa'
    MEDIUM_GRAY = '#e2e8f0'
    WHITE = '#ffffff'

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        self.temp_files = []

    def setup_custom_styles(self):
        """Setup custom Alshaya-branded styles"""
        self.title_style = ParagraphStyle(
            'DNTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor(self.DARK_NAVY),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )

        self.header_style = ParagraphStyle(
            'DNHeader',
            fontSize=11,
            textColor=colors.HexColor(self.DARK_NAVY),
            fontName='Helvetica-Bold',
            spaceAfter=6
        )

        self.normal_style = ParagraphStyle(
            'DNNormal',
            fontSize=9,
            textColor=colors.black,
            leading=11,
            wordWrap='CJK'
        )

    def _get_logo_path(self):
        candidates = [
            os.path.join('static', 'images', 'AlShaya-Logo-color@2x.png'),
            os.path.join('static', 'images', 'LOGO.png'),
            os.path.join('static', 'images', 'al-shaya-logo-white@2x.png')
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        return None

    def _draw_header_footer(self, canv: canvas.Canvas, doc):
        """Draw Alshaya branded header and footer"""
        page_width, page_height = doc.pagesize
        gold = colors.HexColor(self.GOLD)
        dark = colors.HexColor(self.DARK_NAVY)

        logo_path = self._get_logo_path()
        if logo_path and os.path.exists(logo_path):
            try:
                w, h = 140, 50
                x = (page_width - w) / 2
                y = page_height - 60
                canv.drawImage(logo_path, x, y, width=w, height=h, preserveAspectRatio=True, mask='auto')
            except Exception:
                pass

        canv.setStrokeColor(gold)
        canv.setLineWidth(2)
        canv.line(doc.leftMargin, page_height - 70, page_width - doc.rightMargin, page_height - 70)

        canv.setStrokeColor(gold)
        canv.setLineWidth(2)
        canv.line(doc.leftMargin, doc.bottomMargin + 15, page_width - doc.rightMargin, doc.bottomMargin + 15)

        canv.setFillColor(dark)
        canv.setFont('Helvetica', 10)
        canv.drawCentredString(page_width / 2, doc.bottomMargin + 5, 'https://alshayaenterprises.com')

    def generate(self, file_id, session, project_settings=None):
        """
        Generate Delivery Note - ALL items on a SINGLE document (summary table)
        Returns: path to generated PDF
        """
        self.project_settings = project_settings or {}
        uploaded_files = session.get('uploaded_files', [])
        file_info = None

        for f in uploaded_files:
            if f['id'] == file_id:
                file_info = f
                break

        if not file_info:
            raise Exception('File not found')

        is_multibudget = file_info.get('multibudget', False)
        product_selections = file_info.get('product_selections', []) if is_multibudget else []
        tier = file_info.get('tier', 'budgetary') if is_multibudget else None

        items = []
        session_id = session.get('session_id', '')

        if 'costed_data' in file_info:
            items = self._parse_items(file_info['costed_data'], session, file_id, 'costed',
                                      is_multibudget, product_selections, tier)
        elif 'stitched_table' in file_info:
            items = self._parse_items(file_info['stitched_table'], session, file_id, 'stitched',
                                      is_multibudget, product_selections, tier)
        elif 'extraction_result' in file_info:
            items = self._parse_items(file_info['extraction_result'], session, file_id, 'extraction')
        else:
            raise Exception('No data available. Please extract tables first.')

        if not items:
            raise Exception('No items found in the table.')

        output_dir = os.path.join('outputs', session_id, 'delivery_note')
        os.makedirs(output_dir, exist_ok=True)

        output_file = os.path.join(output_dir, f'delivery_note_{file_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf')

        doc = SimpleDocTemplate(output_file, pagesize=A4,
                                topMargin=0.9 * inch, bottomMargin=0.7 * inch,
                                leftMargin=0.6 * inch, rightMargin=0.6 * inch)
        story = self._create_delivery_note(items)

        try:
            doc.build(story, onFirstPage=self._draw_header_footer, onLaterPages=self._draw_header_footer)
        finally:
            for f in self.temp_files:
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except:
                    pass
            self.temp_files = []

        return output_file

    def _parse_items(self, data, session, file_id, source_type,
                     is_multibudget=False, product_selections=None, tier=None):
        """Parse items from data sources - reuses MAS parser"""
        from utils.mas_generator import MASGenerator
        mas = MASGenerator()

        if source_type == 'costed':
            return mas.parse_items_from_costed_data(data, session, file_id,
                                                    is_multibudget, product_selections, tier)
        elif source_type == 'stitched':
            return mas.parse_items_from_stitched_table(data, session, file_id,
                                                      is_multibudget, product_selections, tier)
        elif source_type == 'extraction':
            return mas.parse_items_from_extraction(data, session, file_id)
        return []

    def _create_delivery_note(self, items):
        """Create the complete delivery note document"""
        story = []
        gold = colors.HexColor(self.GOLD)
        dark = colors.HexColor(self.DARK_NAVY)
        light_gray = colors.HexColor(self.LIGHT_GRAY)

        # Title
        header_data = [
            ['DELIVERY NOTE', f'{len(items)} Item(s)']
        ]
        header_table = Table(header_data, colWidths=[5.5 * inch, 1.5 * inch])
        header_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 16),
            ('TEXTCOLOR', (0, 0), (0, 0), dark),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica'),
            ('FONTSIZE', (1, 0), (1, 0), 9),
            ('TEXTCOLOR', (1, 0), (1, 0), gold),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(header_table)

        # Gold line
        line_data = [['']]
        line_table = Table(line_data, colWidths=[7 * inch])
        line_table.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, -1), 2, gold),
        ]))
        story.append(line_table)
        story.append(Spacer(1, 0.1 * inch))

        # Delivery Info (FROM / TO) - use project settings if provided
        ps = getattr(self, 'project_settings', {}) or {}
        delivery_info = [
            ['FROM:', '', 'TO:', ''],
            ['Company:', ps.get('contractor', 'Al Shaya Enterprises LLC'), 'Project:', ps.get('project_name', '[Project Name]')],
            ['Address:', 'Muscat, Sultanate of Oman', 'Location:', ps.get('location', '[Delivery Location]')],
            ['Contact:', ps.get('site_engineer', '[Contact Person]'), 'Attn:', ps.get('client_name', '[Site Engineer]')],
            ['Phone:', '[Phone Number]', 'Phone:', '[Site Phone]'],
        ]
        delivery_table = Table(delivery_info, colWidths=[0.9 * inch, 2.6 * inch, 0.9 * inch, 2.6 * inch])
        delivery_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 1), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (1, 0), dark),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.HexColor(self.GOLD)),
            ('BACKGROUND', (2, 0), (3, 0), dark),
            ('TEXTCOLOR', (2, 0), (3, 0), colors.HexColor(self.GOLD)),
            ('BACKGROUND', (0, 1), (0, -1), light_gray),
            ('BACKGROUND', (2, 1), (2, -1), light_gray),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(delivery_table)
        story.append(Spacer(1, 0.08 * inch))

        # Document Reference
        ref_data = [
            ['DN Number:', f'DN-{datetime.now().strftime("%Y%m%d")}-001',
             'Date:', datetime.now().strftime('%d/%m/%Y')],
            ['PO Reference:', ps.get('po_reference', '[Purchase Order No.]'),
             'Vehicle No:', '[Vehicle Registration]'],
            ['Driver Name:', '[Driver Name]',
             'Delivery Type:', '☐ Full  ☐ Partial'],
        ]
        ref_table = Table(ref_data, colWidths=[1.1 * inch, 2.4 * inch, 1.1 * inch, 2.4 * inch])
        ref_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), light_gray),
            ('BACKGROUND', (2, 0), (2, -1), light_gray),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(ref_table)
        story.append(Spacer(1, 0.12 * inch))

        # ITEMS TABLE
        story.append(Paragraph('<b>ITEMS DELIVERED</b>', self.header_style))
        story.append(Spacer(1, 0.05 * inch))

        # Table header
        items_header = ['#', 'Description', 'Brand', 'Qty', 'Unit', 'Condition', 'Remarks']
        col_widths = [0.35 * inch, 2.5 * inch, 1.0 * inch, 0.5 * inch, 0.5 * inch, 0.8 * inch, 1.35 * inch]

        items_data = [items_header]

        for idx, item in enumerate(items):
            description = item.get('description', 'N/A')
            if len(description) > 80:
                description = description[:77] + '...'

            desc_para = Paragraph(description, ParagraphStyle('ItemDesc', fontSize=6.5, leading=8, wordWrap='CJK'))

            items_data.append([
                str(idx + 1),
                desc_para,
                item.get('brand', '-'),
                item.get('qty', '-'),
                item.get('unit', '-'),
                '☐ Good\n☐ Damaged',
                ''
            ])

        items_table = Table(items_data, colWidths=col_widths, repeatRows=1)
        items_table.setStyle(TableStyle([
            # Header
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 0), (-1, 0), dark),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor(self.GOLD)),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            # Body
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (3, 1), (4, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            # Alternating row colors
            *[('BACKGROUND', (0, i), (-1, i), light_gray) for i in range(2, len(items_data), 2)],
        ]))
        story.append(items_table)
        story.append(Spacer(1, 0.12 * inch))

        # DELIVERY SUMMARY
        story.append(Paragraph('<b>DELIVERY SUMMARY</b>', self.header_style))
        story.append(Spacer(1, 0.04 * inch))

        summary_data = [
            ['Total Items:', str(len(items)), 'Items Received:', ''],
            ['Items Damaged:', '', 'Items Missing:', ''],
        ]
        summary_table = Table(summary_data, colWidths=[1.2 * inch, 2.3 * inch, 1.2 * inch, 2.3 * inch])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), light_gray),
            ('BACKGROUND', (2, 0), (2, -1), light_gray),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.1 * inch))

        # ACKNOWLEDGEMENT & SIGNATURES
        story.append(Paragraph('<b>ACKNOWLEDGEMENT</b>', self.header_style))
        story.append(Spacer(1, 0.04 * inch))

        ack_text = Paragraph(
            'I hereby acknowledge receipt of the above-listed materials in the condition stated. '
            'Any discrepancies or damages are noted in the remarks column above.',
            ParagraphStyle('AckText', parent=self.normal_style, fontSize=7, leading=9)
        )
        story.append(ack_text)
        story.append(Spacer(1, 0.08 * inch))

        sig_data = [
            ['Delivered By:', '', 'Received By:', ''],
            ['Name:', '', 'Name:', ''],
            ['Signature:', '', 'Signature:', ''],
            ['Date:', '', 'Date:', ''],
        ]
        sig_table = Table(sig_data, colWidths=[1.2 * inch, 2.3 * inch, 1.2 * inch, 2.3 * inch])
        sig_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (1, 1), (1, 1), 1, colors.black),
            ('LINEBELOW', (3, 1), (3, 1), 1, colors.black),
            ('LINEBELOW', (1, 2), (1, 2), 1, colors.black),
            ('LINEBELOW', (3, 2), (3, 2), 1, colors.black),
            ('LINEBELOW', (1, 3), (1, 3), 1, colors.black),
            ('LINEBELOW', (3, 3), (3, 3), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(sig_table)
        story.append(Spacer(1, 0.06 * inch))

        # Stamp area
        stamp_data = [
            ["Company Stamp:", '', "Company Stamp:", ''],
        ]
        stamp_table = Table(stamp_data, colWidths=[1.2 * inch, 2.3 * inch, 1.2 * inch, 2.3 * inch])
        stamp_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('BOX', (1, 0), (1, 0), 0.5, colors.grey),
            ('BOX', (3, 0), (3, 0), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
        ]))
        story.append(stamp_table)

        return story
