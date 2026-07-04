import os
import urllib.request
from typing import Dict, Any

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

class PDFGenerator:
    """
    Generates a PDF shopping list with CJK support.
    """
    def __init__(self, output_dir: str = "."):
        self.output_dir = output_dir
        self.font_name = "NotoSansCJK"
        if HAS_REPORTLAB:
            self._setup_fonts()

    def _setup_fonts(self):
        font_path = os.path.join(self.output_dir, "NotoSansSC-Regular.ttf")
        # Use official Google Fonts variable TTF
        font_url = "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf"
        
        if not os.path.exists(font_path):
            try:
                print("Downloading CJK Font for PDF generation...")
                urllib.request.urlretrieve(font_url, font_path)
            except Exception as e:
                print(f"Failed to download font: {e}")
                # Fallback to a known reliable link if first fails
                try:
                    alt_url = "https://github.com/adobe-fonts/source-han-sans/raw/release/OTF/SimplifiedChinese/SourceHanSansSC-Regular.otf"
                    # But reportlab requires TTF. Let's just pass.
                    pass
                except:
                    pass
                return # Fallback to default

        
        try:
            pdfmetrics.registerFont(TTFont(self.font_name, font_path))
        except Exception as e:
            print(f"Failed to register font: {e}")

    def generate_shopping_list(self, result_data: Dict[str, Any], filename: str = "shopping_list.pdf"):
        if not HAS_REPORTLAB:
            raise ImportError("Please run 'pip install reportlab' to use PDF Export.")
            
        filepath = os.path.join(self.output_dir, filename)
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        elements = []
        
        styles = getSampleStyleSheet()
        # Create a style that uses our CJK font
        try:
            normal_style = ParagraphStyle('CJKNormal', parent=styles['Normal'], fontName=self.font_name, fontSize=10)
            title_style = ParagraphStyle('CJKTitle', parent=styles['Title'], fontName=self.font_name, fontSize=16)
        except KeyError:
            normal_style = styles['Normal']
            title_style = styles['Title']

        # Header
        elements.append(Paragraph(f"Optimized Shopping List", title_style))
        elements.append(Spacer(1, 12))
        
        strategy = result_data.get("routing_strategy", "")
        total_cost = result_data.get("total_cost", 0.0)
        elements.append(Paragraph(f"Strategy: {strategy} | Total Cost: €{total_cost:.2f}", normal_style))
        elements.append(Spacer(1, 12))

        # Table Data
        data = [["Ingredient ID", "Product Name", "Total Price (€)", "Packages", "Supermarket", "Bonus?"]]
        
        for item in result_data.get("items", []):
            packages_needed = item.get("packages_needed", 1)
            total_price = item.get("total_price", item["price"] * packages_needed)
            
            data.append([
                item["ingredient_id"],
                item["name"],
                f"{total_price:.2f}",
                str(packages_needed),
                item["supermarket"],
                "Yes" if item["is_bonus"] else "No"
            ])

        if data[1:]: # Ensure we have items
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), self.font_name if self.font_name in pdfmetrics.getRegisteredFontNames() else 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
            
        # Missing items
        missing = result_data.get("missing_items", [])
        if missing:
            elements.append(Spacer(1, 20))
            elements.append(Paragraph("<b>Warning: Missing Items!</b>", normal_style))
            for m in missing:
                elements.append(Paragraph(f"- {m}", normal_style))

        doc.build(elements)
        return filepath

    def generate_recipe_pdf(self, recipe_text: str, filepath: str = "budget_recipe.pdf"):
        if not HAS_REPORTLAB:
            raise ImportError("Please run 'pip install reportlab' to use PDF Export.")
            
        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        elements = []
        
        styles = getSampleStyleSheet()
        try:
            normal_style = ParagraphStyle('CJKNormal', parent=styles['Normal'], fontName=self.font_name, fontSize=11, leading=16, textColor=colors.HexColor("#202124"))
            title_style = ParagraphStyle('CJKTitle', parent=styles['Title'], fontName=self.font_name, fontSize=24, leading=28, textColor=colors.HexColor("#1A73E8"), spaceAfter=20)
            h1_style = ParagraphStyle('CJKH1', parent=styles['Heading1'], fontName=self.font_name, fontSize=18, leading=22, textColor=colors.HexColor("#1A73E8"), spaceBefore=15, spaceAfter=10)
            h2_style = ParagraphStyle('CJKH2', parent=styles['Heading2'], fontName=self.font_name, fontSize=16, leading=20, textColor=colors.HexColor("#202124"), spaceBefore=12, spaceAfter=8)
            h3_style = ParagraphStyle('CJKH3', parent=styles['Heading3'], fontName=self.font_name, fontSize=14, leading=18, textColor=colors.HexColor("#5F6368"), spaceBefore=10, spaceAfter=6)
            bullet_style = ParagraphStyle('CJKBullet', parent=normal_style, leftIndent=20, firstLineIndent=-10)
        except KeyError:
            normal_style = styles['Normal']
            title_style = styles['Title']
            h1_style = styles['Heading1']
            h2_style = styles['Heading2']
            h3_style = styles['Heading3']
            bullet_style = styles['Normal']
            
        elements.append(Paragraph("<b>✨ AI Chef Recipe ✨</b>", title_style))
        
        import re
        
        for line in recipe_text.split('\n'):
            line = line.strip()
            if not line:
                elements.append(Spacer(1, 6))
                continue
                
            # Replace markdown
            line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
            line = re.sub(r'\*(.*?)\*', r'<i>\1</i>', line)
            
            # Process headers and bullets using proper ReportLab ParagraphStyles
            if line.startswith('### '):
                elements.append(Paragraph(f"<b>{line[4:]}</b>", h3_style))
            elif line.startswith('## '):
                elements.append(Paragraph(f"<b>{line[3:]}</b>", h2_style))
            elif line.startswith('# '):
                elements.append(Paragraph(f"<b>{line[2:]}</b>", h1_style))
            elif line.startswith('- ') or line.startswith('* '):
                elements.append(Paragraph(f"&bull; {line[2:]}", bullet_style))
            else:
                elements.append(Paragraph(line, normal_style))
            
        doc.build(elements)
        return filepath
