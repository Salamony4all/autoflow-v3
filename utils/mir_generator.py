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


class MIRGenerator:
    """Generate Material Inspection Report (MIR) with Alshaya branded template"""

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
        """Setup custom Alshaya-branded styles for MIR"""
        self.title_style = ParagraphStyle(
            'MIRTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor(self.DARK_NAVY),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )

        self.subtitle_style = ParagraphStyle(
            'MIRSubtitle',
            fontSize=12,
            textColor=colors.HexColor(self.GOLD),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceAfter=8
        )

        self.header_style = ParagraphStyle(
            'MIRHeader',
            fontSize=11,
            textColor=colors.HexColor(self.DARK_NAVY),
            fontName='Helvetica-Bold',
            spaceAfter=6
        )

        self.normal_style = ParagraphStyle(
            'MIRNormal',
            fontSize=9,
            textColor=colors.black,
            leading=11,
            wordWrap='CJK'
        )

        self.small_style = ParagraphStyle(
            'MIRSmall',
            fontSize=7,
            textColor=colors.black,
            leading=9,
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

        # Logo centered in header
        logo_path = self._get_logo_path()
        if logo_path and os.path.exists(logo_path):
            try:
                w, h = 140, 50
                x = (page_width - w) / 2
                y = page_height - 60
                canv.drawImage(logo_path, x, y, width=w, height=h, preserveAspectRatio=True, mask='auto')
            except Exception:
                pass

        # Gold header line
        canv.setStrokeColor(gold)
        canv.setLineWidth(2)
        canv.line(doc.leftMargin, page_height - 70, page_width - doc.rightMargin, page_height - 70)

        # Footer gold line and website
        canv.setStrokeColor(gold)
        canv.setLineWidth(2)
        canv.line(doc.leftMargin, doc.bottomMargin + 15, page_width - doc.rightMargin, doc.bottomMargin + 15)

        canv.setFillColor(dark)
        canv.setFont('Helvetica', 10)
        canv.drawCentredString(page_width / 2, doc.bottomMargin + 5, 'https://alshayaenterprises.com')

    def generate(self, file_id, session, project_settings=None):
        """
        Generate Material Inspection Report
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

        # Create output directory
        output_dir = os.path.join('outputs', session_id, 'mir')
        os.makedirs(output_dir, exist_ok=True)

        output_file = os.path.join(output_dir, f'mir_{file_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf')

        doc = SimpleDocTemplate(output_file, pagesize=A4,
                                topMargin=0.9 * inch, bottomMargin=0.7 * inch,
                                leftMargin=0.6 * inch, rightMargin=0.6 * inch)
        story = []

        # Create MIR page for each item
        for idx, item in enumerate(items):
            if idx > 0:
                story.append(PageBreak())
            story.extend(self._create_mir_page(item, idx + 1, len(items)))

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
        """Parse items from various data sources - reuses MAS parser logic"""
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

    def _create_mir_page(self, item, item_num, total_items):
        """Create a branded MIR page for one item"""
        story = []
        gold = colors.HexColor(self.GOLD)
        dark = colors.HexColor(self.DARK_NAVY)
        light_gray = colors.HexColor(self.LIGHT_GRAY)
        medium_gray = colors.HexColor(self.MEDIUM_GRAY)

        # Title
        header_data = [
            ['MATERIAL INSPECTION REPORT', f'Item {item_num} of {total_items}']
        ]
        header_table = Table(header_data, colWidths=[5.5 * inch, 1.5 * inch])
        header_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 14),
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
        story.append(Spacer(1, 0.08 * inch))

        # Report Info - use project settings if provided
        ps = getattr(self, 'project_settings', {}) or {}
        report_data = [
            ['Project:', ps.get('project_name', '[Project Name]'), 'MIR No:', f'MIR-{str(item_num).zfill(3)}'],
            ['Contractor:', ps.get('contractor', 'Al Shaya Enterprises'), 'Location/Zone:', ps.get('location', '[Location/Zone]')],
            ['Consultant:', ps.get('consultant', '[Consultant Name]'), 'Date:', datetime.now().strftime('%d/%m/%Y')],
        ]
        report_table = Table(report_data, colWidths=[1.0 * inch, 3.0 * inch, 0.8 * inch, 2.2 * inch])
        report_table.setStyle(TableStyle([
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
        story.append(report_table)
        story.append(Spacer(1, 0.05 * inch))

        # MATERIAL DESCRIPTION Section
        story.append(Paragraph('<b>MATERIAL DESCRIPTION</b>', self.header_style))
        story.append(Spacer(1, 0.02 * inch))

        description_text = item.get('description', 'N/A')
        if len(description_text) > 350:
            description_text = description_text[:347] + '...'

        desc_style = ParagraphStyle('DescCompact', parent=self.normal_style, fontSize=7, leading=9)

        details_data = [
            ['Material:', Paragraph(description_text, desc_style)],
            ['Brand/Manufacturer:', item.get('brand', 'To be specified')],
            ['Quantity:', f"{item.get('qty', 'N/A')} {item.get('unit', '')}"],
            ['MAS Reference:', f'MAS-{str(item_num).zfill(3)}'],
            ['Origin:', item.get('origin', 'As per approved submittal')],
        ]
        details_table = Table(details_data, colWidths=[1.5 * inch, 5.5 * inch])
        details_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), light_gray),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(details_table)
        story.append(Spacer(1, 0.1 * inch))

        # Product image
        self._add_product_image(story, item)
        story.append(Spacer(1, 0.04 * inch))

        # INSPECTION CHECKLIST
        story.append(Paragraph('<b>INSPECTION CHECKLIST</b>', self.header_style))
        story.append(Spacer(1, 0.02 * inch))

        checklist_data = [
            ['#', 'Inspection Item', 'Comply', 'N/A', 'Remarks'],
            ['1', 'Material matches approved MAS submittal', '☐', '☐', ''],
            ['2', 'Quantity delivered as per order', '☐', '☐', ''],
            ['3', 'Material condition (no damage/defects)', '☐', '☐', ''],
            ['4', 'Packaging and labeling correct', '☐', '☐', ''],
            ['5', 'Certificates/test reports provided', '☐', '☐', ''],
            ['6', 'Color/finish matches approved sample', '☐', '☐', ''],
            ['7', 'Dimensions within tolerance', '☐', '☐', ''],
        ]
        checklist_table = Table(checklist_data, colWidths=[0.4 * inch, 3.0 * inch, 0.7 * inch, 0.7 * inch, 2.2 * inch])
        checklist_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), dark),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor(self.GOLD)),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (2, 0), (3, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(checklist_table)
        story.append(Spacer(1, 0.05 * inch))

        # INSPECTION RESULT
        story.append(Paragraph('<b>INSPECTION RESULT</b>', self.header_style))
        story.append(Spacer(1, 0.02 * inch))

        result_data = [
            ['☐  APPROVED — Material accepted for use in the project'],
            ['☐  APPROVED WITH COMMENTS — See remarks below'],
            ['☐  REJECTED — Material does not comply with specifications'],
        ]
        result_table = Table(result_data, colWidths=[7 * inch])
        result_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LINEBELOW', (0, 0), (0, 1), 0.5, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(result_table)
        story.append(Spacer(1, 0.04 * inch))

        # SIGNATURES
        story.append(Paragraph('<b>SIGNATURES</b>', self.header_style))
        story.append(Spacer(1, 0.02 * inch))

        sig_data = [
            ['Site Engineer:', ps.get('site_engineer', '[Site Engineer Name]'), 'QA/QC Engineer:', '[QA/QC Name]'],
            ['Signature:', '', 'Signature:', ''],
            ['Consultant Rep:', '[Consultant Rep Name]', 'Date:', ''],
            ['Signature:', '', '', ''],
        ]
        sig_table = Table(sig_data, colWidths=[1.2 * inch, 2.5 * inch, 0.7 * inch, 2.6 * inch])
        sig_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('LINEBELOW', (1, 1), (1, 1), 1, colors.black),
            ('LINEBELOW', (3, 1), (3, 1), 1, colors.black),
            ('LINEBELOW', (1, 3), (1, 3), 1, colors.black),
            ('LINEBELOW', (3, 3), (3, 3), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(sig_table)
        story.append(Spacer(1, 0.02 * inch))

        # Remarks
        remarks = Paragraph(
            '<b>Remarks:</b> _______________________________________________',
            ParagraphStyle('RemarksCompact', parent=self.normal_style, fontSize=7)
        )
        story.append(remarks)

        return story

    def _add_product_image(self, story, item):
        """Add product image with proper handling"""
        image_paths = item.get('image_paths', [])
        if not image_paths and item.get('image_path'):
            image_paths = [item.get('image_path')]

        if not image_paths:
            return

        from PIL import Image as PILImage
        import tempfile

        for img_path in image_paths[:2]:  # Max 2 images for MIR
            if not img_path:
                continue

            if str(img_path).startswith('http'):
                from utils.image_helper import download_image
                cached = download_image(img_path)
                if cached:
                    img_path = cached

            if img_path and os.path.exists(img_path):
                try:
                    with PILImage.open(img_path) as pil_img:
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                        pil_img.convert('RGB').save(tmp.name, 'PNG')
                        self.temp_files.append(tmp.name)

                        img_width, img_height = pil_img.size
                        aspect = img_height / img_width
                        target_w = 2.0 * inch
                        target_h = target_w * aspect
                        if target_h > 1.5 * inch:
                            target_h = 1.5 * inch
                            target_w = target_h / aspect

                        img = RLImage(tmp.name, width=target_w, height=target_h)
                        img.hAlign = 'CENTER'
                        story.append(img)
                except Exception as e:
                    logger.warning(f"Failed to add image to MIR: {e}")
