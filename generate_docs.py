# generate_docs.py
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Canvas class to automatically generate professional running headers and page numbers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            return  # Suppress running header/footer on Cover Page
        
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#858D99"))
        
        # Header text and dividing accent line
        self.drawString(54, 750, "NATIVE CAPITAL — Quantitative Forecasting System Documentation")
        self.setStrokeColor(colors.HexColor("#2A2E39"))
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742)
        
        # Footer text and dynamic page counts
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 40, page_str)
        self.drawString(54, 40, "CONFIDENTIAL — QUANTITATIVE RESEARCH PLATFORM")
        self.restoreState()


def create_project_pdf(filename="Native_Capital_Architecture_Documentation.pdf"):
    # Target Document Setup
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=72,
        bottomMargin=72
    )
    
    # Color Palette Specifications
    PRIMARY = colors.HexColor("#0B0E14")    
    ACCENT = colors.HexColor("#00ffcc")     
    TEXT_DARK = colors.HexColor("#1E222D")  
    MUTED_GREY = colors.HexColor("#545B66") 
    
    # Styles Setup
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=32,
        leading=38,
        textColor=PRIMARY,
        spaceAfter=10
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=14,
        leading=18,
        textColor=MUTED_GREY,
        spaceAfter=30
    )
    
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=PRIMARY,
        spaceBefore=15,
        spaceAfter=12,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=16,
        textColor=TEXT_DARK,
        spaceAfter=10
    )
    
    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=20,
        firstLineIndent=-10,
        spaceAfter=6
    )

    story = []

    # -------------------------------------------------------------------------
    # COVER PAGE
    # -------------------------------------------------------------------------
    story.append(Spacer(1, 150))
    story.append(Paragraph("NATIVE CAPITAL", title_style))
    story.append(Paragraph("Local-First Production Quantitative Forecasting Platform & Architecture", subtitle_style))
    
    # Decorative colored layout divider block
    divider_table = Table([[""]], colWidths=[504], rowHeights=[4])
    divider_table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), ACCENT)]))
    story.append(divider_table)
    story.append(Spacer(1, 200))
    
    meta_text = """
    <b>Prepared By:</b> Quantitative Platform Engineer<br/>
    <b>Deployment Framework:</b> Render Cloud Web Service Backend + Vercel Static Frontend<br/>
    <b>Data Engine State:</b> Local Relational CSV Engine (Automated File Systems Layer)
    """
    story.append(Paragraph(meta_text, body_style))
    story.append(PageBreak())

    # -------------------------------------------------------------------------
    # SECTION 1: SYSTEM OVERVIEW & WHAT WAS USED
    # -------------------------------------------------------------------------
    story.append(Paragraph("1. System Overview & Technology Stack", h1_style))
    story.append(Paragraph(
        "Native Capital is an interactive, regime-aware quantitative asset management dashboard. "
        "The system calculates historical risk dynamics, monitors benchmark trends, and utilizes statistical "
        "and machine learning sequence engines to simulate portfolio outcomes. The ecosystem components include:", 
        body_style
    ))
    
    tech_stack_data = [
        [Paragraph("<b>Component Layer</b>", body_style), Paragraph("<b>Technology Applied</b>", body_style), Paragraph("<b>Engineering Purpose</b>", body_style)],
        [Paragraph("Frontend UI", body_style), Paragraph("React.js, Tailwind CSS, Recharts", body_style), Paragraph("Renders visual interactive confidence cones, metrics, and SHAP impacts.", body_style)],
        [Paragraph("Backend API", body_style), Paragraph("FastAPI (Python), Uvicorn Server", body_style), Paragraph("Asynchronous gateway exposing analysis, metrics, and simulation hooks.", body_style)],
        [Paragraph("Data Storage", body_style), Paragraph("Local Structured CSV Datasets", body_style), Paragraph("Tracks historical records, metrics, and backtest frames locally.", body_style)],
        [Paragraph("Modeling Layer", body_style), Paragraph("XGBoost Regressor, Hidden Markov Models", body_style), Paragraph("Detects market structural regimes and generates path drifts.", body_style)],
        [Paragraph("Data Engine", body_style), Paragraph("yfinance API, Pandas, NumPy", body_style), Paragraph("Automates real-time indexing, calculation changes, and asset syncing.", body_style)]
    ]
    
    t1 = Table(tech_stack_data, colWidths=[100, 150, 254])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F4F5F7")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t1)
    story.append(Spacer(1, 15))

    # -------------------------------------------------------------------------
    # SECTION 2: HOW THE SYSTEM ARCHITECTURE WORKS
    # -------------------------------------------------------------------------
    story.append(Paragraph("2. Architectural Implementations & Execution Flows", h1_style))
    story.append(Paragraph("<b>2.1 File System Data Loops</b>", body_style))
    story.append(Paragraph(
        "The core data flow relies on an automated flat-file file system structure. This guarantees high "
        "portability and allows rapid deployment updates across containerized nodes without database dependency overhead:", body_style
    ))
    story.append(Paragraph("&bull; <b>Data Feed Retrieval:</b> Request endpoints pull historical logs and tracking frames directly from local directory outputs via specialized Pandas pipelines.", bullet_style))
    story.append(Paragraph("&bull; <b>Market Synchronization Automation (data_sync.py):</b> Activating market synchronization triggers background fetches against live Yahoo Finance data pools (^NSEI ticker). The engine calculates missing periods, extracts relative performance tracking parameters, and appends the calculations securely onto your tracking data.", bullet_style))
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>2.2 Simulation & Machine Learning Signals</b>", body_style))
    story.append(Paragraph(
        "Whenever interactive adjustments trigger on the client dashboard dashboard interface, "
        "the application communicates parameter settings to the backend simulation engine. The calculations process via:", body_style
    ))
    story.append(Paragraph("&bull; <b>Hidden Markov Models (hmmlearn):</b> Analyzes standard tracking variances to categorize market sequences into distinct regimes (such as Bull vs Bear conditions).", bullet_style))
    story.append(Paragraph("&bull; <b>XGBoost Forecast Layer (forecast_model.py):</b> Evaluates future drift metrics based on trailing portfolio ratio parameters, drawdowns, and relative benchmark index dynamics.", bullet_style))
    story.append(Paragraph("&bull; <b>Geometric Brownian Motion (Monte Carlo Paths):</b> Executes 100 random lookahead pathways over defined forecasting horizons to render custom visualization boundaries.", bullet_style))
    
    story.append(PageBreak())

    # -------------------------------------------------------------------------
    # SECTION 3: THE DEPLOYMENT CONFIGURATIONS
    # -------------------------------------------------------------------------
    story.append(Paragraph("3. Production Infrastructure & Deployment Blueprint", h1_style))
    story.append(Paragraph(
        "The application architecture isolates the computational engine from client visual render engines. "
        "The configuration layout uses these target settings:", body_style
    ))
    
    story.append(Paragraph("<b>3.1 GitHub Source Code Strategy</b>", body_style))
    story.append(Paragraph(
        "To avoid package bloat and deployment timeout barriers, local environment structures (venv/) and "
        "heavy localized sequence weights (.pkl, .h5) are ignored using optimized gitignore criteria. "
        "This maintains a minimal footprint on your production container builds.", body_style
    ))
    
    story.append(Paragraph("<b>3.2 Render Web Service Core Setup</b>", body_style))
    story.append(Paragraph("The backend API service deploys on an isolated cloud service container using these parameters:", body_style))
    
    config_data = [
        [Paragraph("<b>Configuration Variable</b>", body_style), Paragraph("<b>Production Applied Value</b>", body_style)],
        [Paragraph("Runtime Target Environment", body_style), Paragraph("Python 3.10+ Production Container", body_style)],
        [Paragraph("Dependency Assembly Command", body_style), Paragraph("<b>pip install -r requirements.txt</b>", body_style)],
        [Paragraph("Server Startup Engine Hook", body_style), Paragraph("<b>uvicorn server:app --host 0.0.0.0 --port $PORT</b>", body_style)]
    ]
    t2 = Table(config_data, colWidths=[180, 324])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F4F5F7")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t2)
    
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>3.3 Vercel Client Distribution</b>", body_style))
    story.append(Paragraph(
        "The frontend client compiles static chunks via Vercel. It accesses your analytical layer "
        "by communicating securely with your public Web Service URL via configured client API environment handles.", body_style
    ))
    
    # Final sign-off block decoration
    story.append(Spacer(1, 40))
    story.append(Paragraph("<b>[ End of Document — System Architecture Verified Live ]</b>", ParagraphStyle('Muted', parent=body_style, alignment=1, textColor=MUTED_GREY)))

    # Compile the final document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Success! Project Documentation PDF saved as '{filename}'")

if __name__ == "__main__":
    create_project_pdf()