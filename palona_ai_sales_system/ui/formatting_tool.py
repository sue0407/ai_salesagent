from agency_swarm.tools import BaseTool
from pydantic import Field
import re

class ReportFormattingTool(BaseTool):
    """
    A tool for formatting sales reports with beautiful styling and consistent formatting.
    It enhances readability by formatting sections, bullet points, numbered lists, and objection/counter-response pairs.
    """
    report_text: str = Field(
        ..., description="The raw report text to be formatted"
    )

    def run(self):
        """
        Formats the report text with consistent styling and visual hierarchy.
        """
        sections = self.report_text.split('\n\n')
        formatted_sections = []

        # Title formatting
        if sections and "Sales Call/Meeting Preparation Guide" in sections[0]:
            title = sections[0].strip()
            formatted_sections.append(f"""
<div class="report-title">
    <h1>{title}</h1>
</div>
""")
            sections = sections[1:]

        for section in sections:
            if not section.strip():
                continue
            # Section header
            if ':' in section and not section.startswith('-'):
                header, content = section.split(':', 1)
                formatted_header = f"""
<div class="section-header">
    <h2>{header.strip()}</h2>
</div>
"""
                content_lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
                # Numbered list detection
                if all(re.match(r'\d+\.', line) for line in content_lines):
                    formatted_content = [f"<li>{line[line.find('.')+1:].strip()}</li>" for line in content_lines]
                    formatted_section = formatted_header + f"<ol>{''.join(formatted_content)}</ol>"
                # Objection/Counter-Response special handling
                elif header.strip().lower().startswith("potential objections"):
                    items = []
                    i = 0
                    while i < len(content_lines):
                        if content_lines[i].startswith("Objection:"):
                            objection = content_lines[i][len("Objection:"):].strip()
                            counter = ""
                            if i+1 < len(content_lines) and content_lines[i+1].startswith("Counter:"):
                                counter = content_lines[i+1][len("Counter:"):].strip()
                                i += 1
                            items.append(f"<li><b>Objection:</b> {objection}<br><b>Counter:</b> {counter}</li>")
                        i += 1
                    formatted_section = formatted_header + f"<ul>{''.join(items)}</ul>"
                # Bullet points
                elif all(line.startswith('-') for line in content_lines):
                    formatted_content = [f"<li>{line[1:].strip()}</li>" for line in content_lines]
                    formatted_section = formatted_header + f"<ul>{''.join(formatted_content)}</ul>"
                else:
                    # Mixed or paragraph content
                    formatted_content = []
                    for line in content_lines:
                        if line.startswith('-'):
                            formatted_content.append(f"<ul><li>{line[1:].strip()}</li></ul>")
                        elif re.match(r'\d+\.', line):
                            formatted_content.append(f"<ol><li>{line[line.find('.')+1:].strip()}</li></ol>")
                        else:
                            formatted_content.append(f"<div class=\"section-content\">{line}</div>")
                    formatted_section = formatted_header + "".join(formatted_content)
            else:
                # No header, just content
                lines = [line.strip() for line in section.strip().split('\n') if line.strip()]
                formatted_lines = []
                for line in lines:
                    if line.startswith('-'):
                        formatted_lines.append(f"<ul><li>{line[1:].strip()}</li></ul>")
                    elif re.match(r'\d+\.', line):
                        formatted_lines.append(f"<ol><li>{line[line.find('.')+1:].strip()}</li></ol>")
                    else:
                        formatted_lines.append(f"<div class=\"section-content\">{line}</div>")
                formatted_section = "".join(formatted_lines)
            formatted_sections.append(formatted_section)

        formatted_report = "\n".join(formatted_sections)

        styled_report = f"""
<style>
    .report-container {{
        background-color: white;
        padding: 1.2rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        margin: 1.2rem 0;
    }}
    .report-title h1 {{
        font-size: 1.3rem;
        font-weight: 700;
        color: #222;
        margin-bottom: 1.2rem;
        text-align: center;
        line-height: 1.1;
        white-space: normal;
    }}
    .section-header h2 {{
        font-size: 1.15rem;
        font-weight: 600;
        color: #222;
        margin: 1.1rem 0 0.7rem 0;
    }}
    .section-content {{
        font-size: 1rem;
        line-height: 1.4;
        color: #333;
        margin: 0.2rem 0;
    }}
    ul, ol {{
        margin: 0.2rem 0 0.2rem 1.2rem;
        padding-left: 1.2rem;
    }}
    li {{
        font-size: 1rem;
        line-height: 1.4;
        color: #333;
        margin: 0.2rem 0;
    }}
</style>
<div class="report-container">
    {formatted_report}
</div>
"""
        return styled_report

if __name__ == "__main__":
    # Test the tool
    test_report = """
Sales Call/Meeting Preparation Guide for Sephora North America

Key Business Challenges and Opportunities:
- Maintaining market position
- Enhancing customer experience
- Expanding collaborations

Strategic Talking Points:
1. Congratulate Artemis on her recent appointment as Sephora's first female CEO and the recognition she has received for her leadership.
2. Discuss how Palona AI's emotionally intelligent agents can enhance Sephora's customer experience by providing personalized, empathetic interactions at scale.
3. Highlight the importance of maintaining a consistent brand voice across touchpoints and how Palona AI's customizable solutions ensure on-brand communication.

Potential Objections and Counter-Responses:
Objection: Sephora already has a strong online presence and digital platforms.
Counter: Palona AI's solutions can seamlessly integrate with Sephora's existing platforms, enhancing them with emotionally intelligent interactions and personalized recommendations.
Objection: Implementing new technology may disrupt current operations.
Counter: Palona AI's team of experts will work closely with Sephora to ensure a smooth integration process, minimizing disruption and maximizing results.
"""
    tool = ReportFormattingTool(report_text=test_report)
    print(tool.run()) 