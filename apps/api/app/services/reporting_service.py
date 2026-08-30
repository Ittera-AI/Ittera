"""PDF Report Generation Service with white-label support.

Generates professional, branded PDF reports for:
- Analytics summaries
- Content performance reports
- Competitive intelligence reports
- Custom report builder outputs

Features:
- HTML template-based generation
- White-label branding support
- Multiple report types and layouts
- Chart/image embedding
- Async generation via Celery
"""

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.db.datetime_helpers import utc_now
from app.models.organization import Organization, Workspace
from app.models.user import User

logger = logging.getLogger(__name__)


def _html_to_pdf(html_content: str) -> bytes:
    """Render HTML to PDF. WeasyPrint is loaded lazily (requires native GTK on Windows)."""
    try:
        from weasyprint import HTML
    except OSError as exc:
        raise RuntimeError(
            "PDF generation requires WeasyPrint system libraries (GTK/Pango). "
            "Install them or run the API in Docker."
        ) from exc

    return HTML(string=html_content).write_pdf()


# HTML Templates for different report types
REPORT_TEMPLATES = {
    "analytics_summary": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ report_title }}</title>
    <style>
        @page {
            size: A4;
            margin: 2cm;
            @bottom-center {
                content: "{{ footer_text }} | Page " counter(page) " of " counter(pages);
                font-size: 9pt;
                color: #6B7280;
            }
        }
        
        * { box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #1F2937;
            margin: 0;
            padding: 0;
        }
        
        .header {
            border-bottom: 3px solid {{ brand_color }};
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        
        .logo {
            max-height: 60px;
            margin-bottom: 10px;
        }
        
        .report-title {
            font-size: 28pt;
            font-weight: 700;
            color: {{ brand_color }};
            margin: 0 0 10px 0;
        }
        
        .report-meta {
            font-size: 10pt;
            color: #6B7280;
        }
        
        .section {
            margin-bottom: 30px;
        }
        
        .section-title {
            font-size: 16pt;
            font-weight: 600;
            color: {{ brand_color }};
            border-left: 4px solid {{ brand_color }};
            padding-left: 12px;
            margin-bottom: 15px;
        }
        
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .metric-card {
            background: linear-gradient(135deg, {{ brand_color }}08 0%, {{ brand_color }}15 100%);
            border: 1px solid {{ brand_color }}30;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }
        
        .metric-value {
            font-size: 32pt;
            font-weight: 700;
            color: {{ brand_color }};
            margin: 0;
        }
        
        .metric-label {
            font-size: 10pt;
            color: #6B7280;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 5px;
        }
        
        .metric-change {
            font-size: 12pt;
            margin-top: 8px;
        }
        
        .metric-change.positive { color: #10B981; }
        .metric-change.negative { color: #EF4444; }
        .metric-change.neutral { color: #6B7280; }
        
        .chart-container {
            background: #F9FAFB;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .chart-title {
            font-size: 12pt;
            font-weight: 600;
            margin-bottom: 15px;
            color: #374151;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        
        th {
            background: {{ brand_color }}15;
            color: {{ brand_color }};
            font-weight: 600;
            text-align: left;
            padding: 12px;
            font-size: 10pt;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        td {
            padding: 12px;
            border-bottom: 1px solid #E5E7EB;
            font-size: 10pt;
        }
        
        tr:hover {
            background: #F9FAFB;
        }
        
        .insight-box {
            background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
            border-left: 4px solid #F59E0B;
            padding: 15px 20px;
            border-radius: 0 8px 8px 0;
            margin-bottom: 20px;
        }
        
        .insight-box h4 {
            margin: 0 0 8px 0;
            color: #92400E;
            font-size: 12pt;
        }
        
        .insight-box p {
            margin: 0;
            color: #78350F;
            font-size: 10pt;
        }
        
        .footer-branding {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #E5E7EB;
            font-size: 9pt;
            color: #9CA3AF;
            text-align: center;
        }
        
        .two-column {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }
        
        .disclaimer {
            background: #F3F4F6;
            border-radius: 6px;
            padding: 15px;
            font-size: 9pt;
            color: #6B7280;
            margin-top: 30px;
        }
    </style>
</head>
<body>
    <div class="header">
        {% if logo_url %}
        <img src="{{ logo_url }}" class="logo" alt="Logo">
        {% endif %}
        <h1 class="report-title">{{ report_title }}</h1>
        <div class="report-meta">
            Generated for {{ client_name }} | {{ report_period }} | {{ generated_at }}
        </div>
    </div>
    
    {{ content }}
    
    {% if show_powered_by %}
    <div class="footer-branding">
        Powered by Iterra AI | Professional Content Intelligence Platform
    </div>
    {% endif %}
    
    {% if disclaimer %}
    <div class="disclaimer">
        {{ disclaimer }}
    </div>
    {% endif %}
</body>
</html>
""",

    "competitive_report": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ report_title }}</title>
    <style>
        @page {
            size: A4;
            margin: 2cm;
            @bottom-center {
                content: "{{ footer_text }} | Page " counter(page) " of " counter(pages);
                font-size: 9pt;
                color: #6B7280;
            }
        }
        
        * { box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #1F2937;
        }
        
        .header {
            border-bottom: 3px solid {{ brand_color }};
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        
        .report-title {
            font-size: 24pt;
            font-weight: 700;
            color: {{ brand_color }};
            margin: 0 0 10px 0;
        }
        
        .competitor-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .competitor-card {
            background: #F9FAFB;
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            padding: 15px;
        }
        
        .competitor-name {
            font-weight: 600;
            font-size: 12pt;
            color: {{ brand_color }};
            margin: 0 0 8px 0;
        }
        
        .competitor-stats {
            font-size: 10pt;
            color: #6B7280;
        }
        
        .gap-item {
            background: #FEF2F2;
            border-left: 4px solid #EF4444;
            padding: 12px 15px;
            margin-bottom: 10px;
            border-radius: 0 8px 8px 0;
        }
        
        .opportunity-item {
            background: #ECFDF5;
            border-left: 4px solid #10B981;
            padding: 12px 15px;
            margin-bottom: 10px;
            border-radius: 0 8px 8px 0;
        }
        
        .score-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 10pt;
            font-weight: 600;
        }
        
        .score-high { background: #10B981; color: white; }
        .score-medium { background: #F59E0B; color: white; }
        .score-low { background: #EF4444; color: white; }
    </style>
</head>
<body>
    <div class="header">
        {% if logo_url %}
        <img src="{{ logo_url }}" style="max-height: 50px; margin-bottom: 10px;">
        {% endif %}
        <h1 class="report-title">{{ report_title }}</h1>
        <div style="font-size: 10pt; color: #6B7280;">
            {{ report_period }} | {{ generated_at }}
        </div>
    </div>
    
    {{ content }}
</body>
</html>
""",
}


def get_brand_settings(
    workspace: Workspace | None,
    organization: Organization | None,
) -> dict[str, Any]:
    """
    Extract brand settings from workspace/org for white-labeling.
    
    Returns dict with:
        - brand_color: Primary brand color (hex)
        - logo_url: Logo URL or None
        - client_name: Display name for the report
        - footer_text: Custom footer text
        - show_powered_by: Whether to show "Powered by Iterra"
        - disclaimer: Custom disclaimer text
    """
    defaults = {
        "brand_color": "#6366F1",  # Iterra indigo
        "logo_url": None,
        "client_name": "Client",
        "footer_text": "Iterra Analytics Report",
        "show_powered_by": True,
        "disclaimer": None,
    }
    
    if not workspace and not organization:
        return defaults
    
    # Get white-label settings from organization
    wl_settings = {}
    if organization and organization.white_label_settings:
        wl_settings = organization.white_label_settings
    
    # Check if white-labeling is enabled
    if wl_settings.get("enabled"):
        defaults["show_powered_by"] = not wl_settings.get("hide_powered_by", False)
        
        if wl_settings.get("logo_url"):
            defaults["logo_url"] = wl_settings.get("logo_url")
        
        if wl_settings.get("primary_color"):
            defaults["brand_color"] = wl_settings.get("primary_color")
        
        if wl_settings.get("custom_footer"):
            defaults["disclaimer"] = wl_settings.get("custom_footer")
    
    # Workspace branding overrides
    if workspace:
        if workspace.brand_colors and workspace.brand_colors.get("primary"):
            defaults["brand_color"] = workspace.brand_colors.get("primary")
        
        if workspace.logo_url:
            defaults["logo_url"] = workspace.logo_url
        
        if workspace.client_name:
            defaults["client_name"] = workspace.client_name
        elif workspace.name:
            defaults["client_name"] = workspace.name
    
    return defaults


def generate_analytics_report(
    db: Session,
    user: User,
    workspace: Workspace | None,
    period_days: int = 30,
    include_charts: bool = True,
) -> bytes:
    """
    Generate a comprehensive analytics PDF report.
    
    Args:
        db: Database session
        user: Report owner
        workspace: Workspace context (for white-labeling)
        period_days: Analysis period
        include_charts: Whether to include data visualizations
        
    Returns:
        PDF bytes ready for download or email
    """
    from app.services.analytics_service import analytics_summary, get_content_insights
    
    # Get analytics data
    summary = analytics_summary(db, user, period_days=period_days)
    insights = get_content_insights(db, user, period_days=period_days)
    
    # Get brand settings
    org = workspace.organization if workspace else None
    brand = get_brand_settings(workspace, org)
    
    # Build report content
    content_parts = []
    
    # Executive Summary Section
    content_parts.append(f"""
    <div class="section">
        <h2 class="section-title">Executive Summary</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value">{summary.get('posts_count', 0)}</div>
                <div class="metric-label">Posts Published</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{summary.get('avg_engagement_rate', 0):.2f}%</div>
                <div class="metric-label">Avg Engagement Rate</div>
                <div class="metric-change {summary.get('engagement_trend', {}).get('direction', 'neutral')}">
                    {summary.get('engagement_trend', {}).get('percent_change', 0):+.1f}% vs previous period
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{summary.get('total_engagements', 0):,}</div>
                <div class="metric-label">Total Engagements</div>
            </div>
        </div>
    </div>
    """)
    
    # Content Insights Section
    if insights.get('recommendations'):
        content_parts.append('<div class="section"><h2 class="section-title">AI-Generated Insights</h2>')
        for rec in insights.get('recommendations', [])[:3]:
            content_parts.append(f"""
            <div class="insight-box">
                <h4>💡 Strategic Insight</h4>
                <p>{rec}</p>
            </div>
            """)
        content_parts.append('</div>')
    
    # Top Performing Content
    if summary.get('top_performing_post'):
        top = summary.get('top_performing_post', {})
        content_parts.append(f"""
    <div class="section">
        <h2 class="section-title">Top Performing Content</h2>
        <div style="background: #F9FAFB; padding: 20px; border-radius: 8px;">
            <p style="font-style: italic; color: #374151; margin-bottom: 15px;">
                "{top.get('content_preview', 'N/A')[:200]}..."
            </p>
            <div style="display: flex; gap: 20px;">
                <div><strong>Engagement Rate:</strong> {top.get('engagement_rate', 0):.2f}%</div>
                <div><strong>Platform:</strong> {top.get('platform', 'N/A').capitalize()}</div>
                <div><strong>Published:</strong> {top.get('published_at', 'N/A')[:10]}</div>
            </div>
        </div>
    </div>
    """)
    
    # Performance Trends
    trends = summary.get('trends', {})
    if trends:
        content_parts.append('<div class="section"><h2 class="section-title">Performance Trends</h2>')
        content_parts.append('<table>')
        content_parts.append('<tr><th>Metric</th><th>Current</th><th>Previous</th><th>Change</th></tr>')
        
        for metric, trend in trends.items():
            direction = trend.get('direction', 'flat')
            arrow = '↑' if direction == 'up' else ('↓' if direction == 'down' else '→')
            content_parts.append(f"""
            <tr>
                <td>{metric.replace('_', ' ').title()}</td>
                <td>{trend.get('current', 'N/A')}</td>
                <td>{trend.get('previous', 'N/A')}</td>
                <td class="{direction}">{arrow} {trend.get('percent_change', 0):+.1f}%</td>
            </tr>
            """)
        
        content_parts.append('</table></div>')
    
    # Build final HTML
    template = REPORT_TEMPLATES["analytics_summary"]
    html_content = template.replace('{{ content }}', '\n'.join(content_parts))
    
    # Substitute variables
    report_period = f"Last {period_days} Days"
    if period_days == 7:
        report_period = "Last 7 Days"
    elif period_days == 30:
        report_period = "Last 30 Days"
    elif period_days == 90:
        report_period = "Last Quarter"
    
    html_content = html_content.replace('{{ report_title }}', 'Content Performance Report')
    html_content = html_content.replace('{{ client_name }}', brand.get('client_name', 'Client'))
    html_content = html_content.replace('{{ report_period }}', report_period)
    html_content = html_content.replace('{{ generated_at }}', utc_now().strftime('%B %d, %Y'))
    html_content = html_content.replace('{{ brand_color }}', brand.get('brand_color', '#6366F1'))
    html_content = html_content.replace('{{ logo_url }}', brand.get('logo_url') or '')
    html_content = html_content.replace('{{ footer_text }}', brand.get('footer_text', 'Analytics Report'))
    html_content = html_content.replace('{{ show_powered_by }}', str(brand.get('show_powered_by', True)))
    html_content = html_content.replace('{{ disclaimer }}', brand.get('disclaimer') or '')
    
    # Generate PDF
    try:
        pdf_bytes = _html_to_pdf(html_content)
        logger.info(f"Generated analytics report: {len(pdf_bytes)} bytes")
        return pdf_bytes
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise


def generate_competitive_report(
    db: Session,
    user: User,
    workspace: Workspace,
    analysis_id: str | None = None,
) -> bytes:
    """
    Generate a competitive intelligence PDF report.
    
    Args:
        db: Database session
        user: Report owner
        workspace: Workspace with competitor data
        analysis_id: Specific analysis to include, or None for latest
        
    Returns:
        PDF bytes
    """
    from app.models.organization import CompetitorAnalysis
    
    # Get latest competitive analysis
    query = db.query(CompetitorAnalysis).filter(
        CompetitorAnalysis.workspace_id == workspace.id,
    )
    
    if analysis_id:
        query = query.filter(CompetitorAnalysis.id == analysis_id)
    
    analysis = query.order_by(CompetitorAnalysis.created_at.desc()).first()
    
    if not analysis:
        # Generate empty report with instructions
        findings = {
            "message": "No competitive analysis data available. Run a competitor analysis first."
        }
    else:
        findings = analysis.findings or {}
    
    # Get brand settings
    brand = get_brand_settings(workspace, workspace.organization)
    
    # Build content
    content_parts = []
    
    if findings.get("message"):
        content_parts.append(f"""
        <div class="section">
            <p>{findings.get('message')}</p>
        </div>
        """)
    else:
        # Competitor Overview
        content_parts.append("""
        <div class="section">
            <h2 class="section-title">Competitive Landscape</h2>
            <p>Analysis of your content performance vs key competitors.</p>
        </div>
        """)
        
        # Content Gaps
        gap_analysis = findings.get('gap_analysis', {})
        if gap_analysis.get('gap_topics'):
            content_parts.append('''
            <div class="section">
                <h2 class="section-title">Content Gaps</h2>
                <p>Topics your competitors cover that you don't:</p>
            ''')
            
            for gap in gap_analysis.get('gap_topics', [])[:5]:
                content_parts.append(f"""
                <div class="gap-item">
                    <strong>{gap.get('topic', 'Unknown')}</strong>
                    <p style="margin: 5px 0 0 0; font-size: 9pt;">
                        Difficulty: {gap.get('difficulty', 'unknown')} | 
                        Opportunity Score: {gap.get('opportunity_score', 0):.0%}
                    </p>
                </div>
                """)
            
            content_parts.append('</div>')
        
        # Opportunities
        if gap_analysis.get('high_impact_opportunities'):
            content_parts.append('''
            <div class="section">
                <h2 class="section-title">High-Impact Opportunities</h2>
            ''')
            
            for opp in gap_analysis.get('high_impact_opportunities', [])[:5]:
                content_parts.append(f"""
                <div class="opportunity-item">
                    <strong>{opp.get('opportunity', 'Unknown')}</strong>
                    <p style="margin: 5px 0 0 0; font-size: 9pt;">
                        {opp.get('expected_impact', '')}
                    </p>
                </div>
                """)
            
            content_parts.append('</div>')
    
    # Build final HTML
    template = REPORT_TEMPLATES["competitive_report"]
    html_content = template.replace('{{ content }}', '\n'.join(content_parts))
    
    html_content = html_content.replace('{{ report_title }}', 'Competitive Intelligence Report')
    html_content = html_content.replace('{{ report_period }}', utc_now().strftime('%B %Y'))
    html_content = html_content.replace('{{ generated_at }}', utc_now().strftime('%B %d, %Y'))
    html_content = html_content.replace('{{ brand_color }}', brand.get('brand_color', '#6366F1'))
    html_content = html_content.replace('{{ logo_url }}', brand.get('logo_url') or '')
    
    try:
        return _html_to_pdf(html_content)
    except Exception as e:
        logger.error(f"Competitive report generation failed: {e}")
        raise


def generate_custom_report(
    title: str,
    sections: list[dict],
    workspace: Workspace | None = None,
    organization: Organization | None = None,
) -> bytes:
    """
    Generate a custom report from structured sections.
    
    Args:
        title: Report title
        sections: List of section dicts with 'type', 'title', 'data'
        workspace: For branding context
        organization: For white-label settings
        
    Returns:
        PDF bytes
    """
    brand = get_brand_settings(workspace, organization)
    
    content_parts = []
    
    for section in sections:
        section_type = section.get('type', 'text')
        section_title = section.get('title', '')
        data = section.get('data', {})
        
        content_parts.append(f'<div class="section"><h2 class="section-title">{section_title}</h2>')
        
        if section_type == 'metrics':
            content_parts.append('<div class="metric-grid">')
            for metric in data.get('items', []):
                content_parts.append(f"""
                <div class="metric-card">
                    <div class="metric-value">{metric.get('value', 0)}</div>
                    <div class="metric-label">{metric.get('label', '')}</div>
                </div>
                """)
            content_parts.append('</div>')
        
        elif section_type == 'table':
            content_parts.append('<table>')
            # Header
            if data.get('headers'):
                content_parts.append('<tr>' + ''.join(f'<th>{h}</th>' for h in data['headers']) + '</tr>')
            # Rows
            for row in data.get('rows', []):
                content_parts.append('<tr>' + ''.join(f'<td>{cell}</td>' for cell in row) + '</tr>')
            content_parts.append('</table>')
        
        elif section_type == 'text':
            content_parts.append(f'<p>{data.get("content", "")}</p>')
        
        elif section_type == 'insights':
            for insight in data.get('items', []):
                content_parts.append(f"""
                <div class="insight-box">
                    <h4>{insight.get('title', 'Insight')}</h4>
                    <p>{insight.get('description', '')}</p>
                </div>
                """)
        
        content_parts.append('</div>')
    
    # Build final HTML
    template = REPORT_TEMPLATES["analytics_summary"]
    html_content = template.replace('{{ content }}', '\n'.join(content_parts))
    
    html_content = html_content.replace('{{ report_title }}', title)
    html_content = html_content.replace('{{ client_name }}', brand.get('client_name', 'Client'))
    html_content = html_content.replace('{{ report_period }}', 'Custom Report')
    html_content = html_content.replace('{{ generated_at }}', utc_now().strftime('%B %d, %Y'))
    html_content = html_content.replace('{{ brand_color }}', brand.get('brand_color', '#6366F1'))
    html_content = html_content.replace('{{ logo_url }}', brand.get('logo_url') or '')
    html_content = html_content.replace('{{ footer_text }}', brand.get('footer_text', 'Custom Report'))
    html_content = html_content.replace('{{ show_powered_by }}', str(brand.get('show_powered_by', True)))
    html_content = html_content.replace('{{ disclaimer }}', brand.get('disclaimer') or '')
    
    try:
        return _html_to_pdf(html_content)
    except Exception as e:
        logger.error(f"Custom report generation failed: {e}")
        raise


def get_report_metadata(
    pdf_bytes: bytes,
    report_type: str,
    workspace: Workspace | None,
) -> dict:
    """
    Get metadata about a generated report.
    
    Returns dict with size, pages, type, etc.
    """
    # Simple size calculation - actual page count would require PDF parsing
    return {
        "size_bytes": len(pdf_bytes),
        "size_kb": round(len(pdf_bytes) / 1024, 1),
        "report_type": report_type,
        "workspace_id": workspace.id if workspace else None,
        "generated_at": utc_now().isoformat(),
    }
