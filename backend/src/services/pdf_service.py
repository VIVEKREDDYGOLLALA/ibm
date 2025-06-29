# src/services/pdf_service.py
import os
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from src.core.config import settings

logger = logging.getLogger(__name__)

class PDFService:
    def __init__(self):
        self.output_dir = settings.PDF_OUTPUT_DIR
        self.temp_dir = settings.TEMP_DIR
        
        # Create directories if they don't exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        
        logger.info(f"PDF service initialized - Output: {self.output_dir}")
    
    async def generate_report(self, report_data: Dict[str, Any]) -> str:
        """Generate PDF report from data"""
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"jira_analysis_report_{timestamp}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            # Create PDF document
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._create_pdf_document(filepath, report_data)
            )
            
            logger.info(f"PDF report generated: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}")
            raise Exception(f"PDF generation failed: {str(e)}")
    
    def _create_pdf_document(self, filepath: str, data: Dict[str, Any]):
        """Create the actual PDF document"""
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        title = Paragraph("Jira Ticket Analysis Report", title_style)
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Report metadata
        story.append(Paragraph("<b>Report Generated:</b> " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"), styles['Normal']))
        story.append(Paragraph("<b>Project:</b> " + data.get('project_key', 'Unknown'), styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Ticket information
        if 'ticket' in data:
            ticket = data['ticket']
            story.append(Paragraph("Ticket Information", styles['Heading2']))
            
            ticket_data = [
                ['Field', 'Value'],
                ['Key', ticket.get('key', 'N/A')],
                ['Summary', ticket.get('summary', 'N/A')],
                ['Status', ticket.get('status', 'N/A')],
                ['Assignee', ticket.get('assignee', 'Unassigned')],
                ['Priority', ticket.get('priority', 'Medium')]
            ]
            
            ticket_table = Table(ticket_data, colWidths=[2*inch, 4*inch])
            ticket_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(ticket_table)
            story.append(Spacer(1, 20))
            
            # Description
            if ticket.get('description'):
                story.append(Paragraph("Description", styles['Heading3']))
                story.append(Paragraph(ticket['description'], styles['Normal']))
                story.append(Spacer(1, 20))
        
        # Analysis results
        if 'analysis' in data:
            analysis = data['analysis']
            story.append(Paragraph("Analysis Results", styles['Heading2']))
            
            if isinstance(analysis, dict):
                for key, value in analysis.items():
                    if isinstance(value, (str, int, float)):
                        story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b> {value}", styles['Normal']))
                    elif isinstance(value, list):
                        story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b>", styles['Normal']))
                        for item in value:
                            story.append(Paragraph(f"• {item}", styles['Normal']))
            else:
                story.append(Paragraph(str(analysis), styles['Normal']))
            
            story.append(Spacer(1, 20))
        
        # Implementation suggestions
        if 'implementation_plan' in data:
            story.append(Paragraph("Implementation Plan", styles['Heading2']))
            plan = data['implementation_plan']
            
            if isinstance(plan, dict):
                for step, details in plan.items():
                    story.append(Paragraph(f"<b>{step}:</b> {details}", styles['Normal']))
            elif isinstance(plan, list):
                for i, step in enumerate(plan, 1):
                    story.append(Paragraph(f"{i}. {step}", styles['Normal']))
            else:
                story.append(Paragraph(str(plan), styles['Normal']))
        
        # Build PDF
        doc.build(story)
    
    async def generate_project_summary(self, project_data: Dict[str, Any]) -> str:
        """Generate a project summary PDF"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"project_summary_{project_data.get('project_key', 'unknown')}_{timestamp}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._create_project_summary_pdf(filepath, project_data)
            )
            
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to generate project summary: {e}")
            raise Exception(f"Project summary generation failed: {str(e)}")
    
    def _create_project_summary_pdf(self, filepath: str, data: Dict[str, Any]):
        """Create project summary PDF"""
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title = Paragraph(f"Project Summary: {data.get('project_key', 'Unknown')}", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Summary statistics
        if 'statistics' in data:
            stats = data['statistics']
            story.append(Paragraph("Project Statistics", styles['Heading2']))
            
            stats_data = [
                ['Metric', 'Value'],
                ['Total Tickets', str(stats.get('total_tickets', 0))],
                ['Open Tickets', str(stats.get('open_tickets', 0))],
                ['In Progress', str(stats.get('in_progress', 0))],
                ['Completed', str(stats.get('completed', 0))],
                ['Average Story Points', str(stats.get('avg_story_points', 'N/A'))]
            ]
            
            stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(stats_table)
            story.append(Spacer(1, 20))
        
        # Top issues
        if 'top_issues' in data:
            story.append(Paragraph("Recent Issues", styles['Heading2']))
            for issue in data['top_issues'][:10]:  # Limit to top 10
                story.append(Paragraph(f"<b>{issue.get('key', 'N/A')}:</b> {issue.get('summary', 'No summary')}", styles['Normal']))
                story.append(Paragraph(f"Status: {issue.get('status', 'Unknown')} | Assignee: {issue.get('assignee', 'Unassigned')}", styles['Normal']))
                story.append(Spacer(1, 10))
        
        # Build PDF
        doc.build(story)