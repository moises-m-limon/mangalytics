import os
from PIL import Image, ImageDraw, ImageFont
import textwrap
from typing import List, Dict, Any
from io import BytesIO


class PanelGenerator:
    """Generate visual manga panel images from text descriptions"""

    def __init__(self):
        self.panel_width = 1200
        self.panel_height = 800
        self.bg_color = "#FFFFFF"
        self.border_color = "#000000"
        self.border_width = 8
        self.title_color = "#E74C3C"
        self.text_color = "#2C3E50"
        self.dialogue_bg = "#FFF3CD"
        self.dialogue_border = "#FFC107"

    def create_panel_image(
        self,
        panel_number: str,
        title: str,
        description: str,
        dialogue: str = None,
        corgi_image_path: str = None
    ) -> bytes:
        """
        Create a visual manga panel image

        Args:
            panel_number: Panel identifier (e.g., "[PANEL 1]")
            title: Panel title
            description: Scene description
            dialogue: Corgi dialogue
            corgi_image_path: Optional path to corgi avatar

        Returns:
            PNG image as bytes
        """
        # Create image with white background
        img = Image.new('RGB', (self.panel_width, self.panel_height), self.bg_color)
        draw = ImageDraw.Draw(img)

        # Try to load fonts (fallback to default if not available)
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 48)
            header_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 32)
            text_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 28)
            dialogue_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 26)
        except:
            # Fallback to default font
            title_font = ImageFont.load_default()
            header_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            dialogue_font = ImageFont.load_default()

        # Draw border
        draw.rectangle(
            [0, 0, self.panel_width - 1, self.panel_height - 1],
            outline=self.border_color,
            width=self.border_width
        )

        y_position = 40

        # Draw panel number
        draw.text(
            (40, y_position),
            panel_number,
            fill="#95A5A6",
            font=header_font
        )
        y_position += 60

        # Draw title
        draw.text(
            (40, y_position),
            title.upper(),
            fill=self.title_color,
            font=title_font
        )
        y_position += 80

        # Draw horizontal line
        draw.rectangle(
            [40, y_position, self.panel_width - 40, y_position + 3],
            fill="#3498DB"
        )
        y_position += 30

        # Load and place corgi avatar if provided
        if corgi_image_path and os.path.exists(corgi_image_path):
            try:
                corgi = Image.open(corgi_image_path)
                # Resize corgi to fit
                corgi_size = 200
                corgi = corgi.resize((corgi_size, corgi_size), Image.Resampling.LANCZOS)
                # Place in top right
                img.paste(corgi, (self.panel_width - corgi_size - 40, 40), corgi if corgi.mode == 'RGBA' else None)
            except Exception as e:
                print(f"Could not load corgi image: {e}")

        # Draw description with word wrap
        description_lines = textwrap.wrap(description, width=80)
        for line in description_lines[:8]:  # Limit to 8 lines
            draw.text(
                (40, y_position),
                line,
                fill=self.text_color,
                font=text_font
            )
            y_position += 40

        # Draw dialogue box if present
        if dialogue:
            y_position += 20
            dialogue_box_y = y_position

            # Wrap dialogue text
            dialogue_lines = textwrap.wrap(dialogue, width=70)

            # Calculate dialogue box height
            dialogue_height = len(dialogue_lines) * 35 + 60
            dialogue_box_width = self.panel_width - 80

            # Draw dialogue background
            draw.rectangle(
                [40, dialogue_box_y, 40 + dialogue_box_width, dialogue_box_y + dialogue_height],
                fill=self.dialogue_bg,
                outline=self.dialogue_border,
                width=4
            )

            # Draw "CORGI SAYS:" label
            draw.text(
                (60, dialogue_box_y + 15),
                "CORGI SAYS:",
                fill="#856404",
                font=header_font
            )

            # Draw dialogue text
            dialogue_y = dialogue_box_y + 55
            for line in dialogue_lines:
                draw.text(
                    (60, dialogue_y),
                    line,
                    fill="#856404",
                    font=dialogue_font
                )
                dialogue_y += 35

        # Convert to bytes
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr.getvalue()

    def create_all_panels(
        self,
        panels: List[Dict[str, str]],
        corgi_image_path: str = None
    ) -> List[Dict[str, Any]]:
        """
        Create PNG images for all panels

        Args:
            panels: List of panel dicts with panel_number, title, description, dialogue
            corgi_image_path: Optional path to corgi avatar

        Returns:
            List of dicts with panel info and image_data (bytes)
        """
        panel_images = []

        for i, panel in enumerate(panels, 1):
            try:
                image_bytes = self.create_panel_image(
                    panel_number=panel.get("panel_number", f"[PANEL {i}]"),
                    title=panel.get("title", f"Panel {i}"),
                    description=panel.get("description", ""),
                    dialogue=panel.get("dialogue"),
                    corgi_image_path=corgi_image_path
                )

                panel_images.append({
                    "panel_number": i,
                    "title": panel.get("title"),
                    "image_data": image_bytes
                })

                print(f"✓ Generated panel image {i}")

            except Exception as e:
                print(f"✗ Failed to generate panel {i}: {str(e)}")
                continue

        return panel_images


panel_generator = PanelGenerator()
