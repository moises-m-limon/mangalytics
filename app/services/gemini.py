import os
import google.generativeai as genai
from typing import List, Dict, Any
from dotenv import load_dotenv
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import textwrap

load_dotenv()


class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Missing GEMINI_API_KEY")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    async def create_manga_panel_prompt(
        self,
        figures: List[Dict[str, Any]],
        context: str = ""
    ) -> str:
        """
        Generate a manga-style narrative prompt using the nano-banana technique

        The nano-banana technique uses structured prompting to create
        multi-panel manga layouts from academic figures

        Args:
            figures: List of figure dicts with 'figure_content' and 'image_data'
            context: Additional context about the paper/topic

        Returns:
            Generated manga panel narrative text
        """
        # Prepare the prompt using nano-banana technique
        # This creates a structured narrative flow from academic content

        prompt = f"""You are a manga artist converting academic research figures into an engaging manga story panel.

Context: {context}

Task: Create a 4-panel manga narrative that explains the research visually.

For each figure provided:
- Panel 1: Introduce the problem/concept with dramatic flair
- Panel 2: Show the methodology or approach
- Panel 3: Present the results or findings
- Panel 4: Conclude with the impact or implications

Use manga storytelling conventions:
- Action lines for emphasis
- Speech bubbles for explanations
- Thought bubbles for insights
- Sound effects (e.g., "ZOOM!", "FLASH!")
- Dramatic angles and perspectives

Generate a narrative description for each panel that can be used to create manga artwork.
Focus on making complex research accessible and exciting.

Number of figures to work with: {len(figures)}

Format your response as:
[PANEL 1]
Title: ...
Description: ...
Dialogue: ...

[PANEL 2]
...

Return ONLY the panel descriptions, ready to be illustrated."""

        # Generate content
        response = self.model.generate_content(prompt)

        return response.text

    async def generate_manga_from_figures(
        self,
        figures: List[Dict[str, Any]],
        paper_title: str = "",
        topic: str = ""
    ) -> Dict[str, Any]:
        """
        Generate manga panels from research figures using multimodal Gemini
        Features a friendly corgi character as the narrator/guide

        Args:
            figures: List of dicts with 'figure_content' (text) and 'image_data' (bytes)
            paper_title: Title of the paper
            topic: Research topic

        Returns:
            Dict with 'narrative' and 'panel_descriptions'
        """
        try:
            # Load the corgi avatar from repo root
            import os
            corgi_image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "corgis.png")
            corgi_image = None
            try:
                corgi_image = Image.open(corgi_image_path)
            except Exception as e:
                print(f"Warning: Could not load corgi avatar: {e}")

            # Prepare context
            context = f"Paper: {paper_title}\nTopic: {topic}\n\n"

            # Add figure descriptions to context
            for i, fig in enumerate(figures, 1):
                context += f"Figure {i}: {fig.get('figure_content', 'No description')}\n"

            # Build multimodal prompt with images and corgi character
            prompt_parts = [
                "You are creating a manga-style visual narrative from academic research figures.\n\n",
                "IMPORTANT: There is a friendly, enthusiastic corgi character who serves as the guide/narrator.\n",
                "The corgi is knowledgeable, excited about research, and explains complex concepts in an accessible way.\n",
                "The corgi should appear in the narrative as the one explaining and presenting the research.\n\n",
            ]

            # Add corgi image to the prompt
            if corgi_image:
                prompt_parts.append("Here is the corgi character that will be your narrator/guide:\n")
                prompt_parts.append(corgi_image)
                prompt_parts.append("\n\n")

            prompt_parts.extend([
                f"Research Topic: {topic}\n",
                f"Paper: {paper_title}\n\n",
                "Create a 4-panel manga story where the CORGI CHARACTER explains the research:\n",
                "1. The corgi should be the main character guiding readers through the research\n",
                "2. Use manga conventions (dramatic angles, action lines, speech bubbles)\n",
                "3. The corgi should speak directly to the reader, making complex ideas fun and accessible\n",
                "4. Include the corgi's enthusiastic personality and reactions\n",
                "5. The corgi can point to figures, gesture excitedly, and provide commentary\n\n",
                "Story structure:\n",
                "- Panel 1: Corgi introduces the research problem/topic with excitement\n",
                "- Panel 2: Corgi explains the approach or methodology\n",
                "- Panel 3: Corgi presents the key findings or results\n",
                "- Panel 4: Corgi concludes with impact and why it matters\n\n",
                "Analyze these research figures and create the manga narrative with the corgi as narrator:\n\n"
            ])

            # Add images to the prompt
            for i, fig in enumerate(figures, 1):
                prompt_parts.append(f"\n--- Figure {i} ---\n")
                prompt_parts.append(f"Description: {fig.get('figure_content', 'Research figure')}\n")

                # Convert image bytes to PIL Image for Gemini
                try:
                    image = Image.open(BytesIO(fig['image_data']))
                    prompt_parts.append(image)
                except Exception as e:
                    print(f"Warning: Could not load image {i}: {e}")
                    continue

            prompt_parts.append("\n\nNow generate the 4-panel manga narrative with the CORGI as the main character/narrator.\n")
            prompt_parts.append("Format each panel like this:\n\n")
            prompt_parts.append("[PANEL 1]\n")
            prompt_parts.append("Title: [Short, punchy title]\n")
            prompt_parts.append("Description: [Visual scene description with the corgi character present and active]\n")
            prompt_parts.append("Dialogue: [What the corgi says - make it enthusiastic, friendly, and educational]\n\n")
            prompt_parts.append("Remember: The corgi is the star! Every panel should feature the corgi explaining, pointing, gesturing, or reacting to the research.\n")
            prompt_parts.append("The corgi's dialogue should be conversational, excited, and break down complex ideas.\n\n")
            prompt_parts.append("Generate all 4 panels now:")

            # Generate with multimodal input
            response = self.model.generate_content(prompt_parts)

            narrative = response.text

            # Parse the response into structured panels
            panels = self._parse_manga_panels(narrative)

            return {
                "narrative": narrative,
                "panels": panels,
                "figures_used": len(figures)
            }

        except Exception as e:
            print(f"Error generating manga: {e}")
            raise

    def _parse_manga_panels(self, narrative: str) -> List[Dict[str, str]]:
        """Parse the generated narrative into structured panels"""
        panels = []
        current_panel = {}

        lines = narrative.split('\n')

        for line in lines:
            line = line.strip()

            if line.startswith('[PANEL'):
                if current_panel:
                    panels.append(current_panel)
                current_panel = {"panel_number": line}
            elif line.startswith('Title:'):
                current_panel['title'] = line.replace('Title:', '').strip()
            elif line.startswith('Description:'):
                current_panel['description'] = line.replace('Description:', '').strip()
            elif line.startswith('Dialogue:'):
                current_panel['dialogue'] = line.replace('Dialogue:', '').strip()

        # Add the last panel
        if current_panel:
            panels.append(current_panel)

        return panels


gemini_service = GeminiService()
