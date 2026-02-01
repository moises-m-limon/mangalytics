import os
import resend
from typing import List, Dict, Any
from dotenv import load_dotenv
import base64

load_dotenv()


class ResendService:
    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY")
        if not self.api_key:
            raise ValueError("Missing RESEND_API_KEY")

        resend.api_key = self.api_key

        # Get from email from env or use default
        # For production, verify a domain at resend.com/domains
        self.from_email = os.getenv("RESEND_FROM_EMAIL", "mangalytics <onboarding@resend.dev>")

    async def send_manga_email(
        self,
        to_email: str,
        topic: str,
        manga_narrative: str,
        panels: List[Dict[str, str]],
        figure_images: List[Dict[str, Any]] = None,
        corgi_avatar_path: str = None,
        panel_images: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send manga panel narrative via email using Resend

        Args:
            to_email: Recipient email address
            topic: Research topic
            manga_narrative: Full narrative text
            panels: List of panel dicts with structured content
            figure_images: Optional list of figure dicts with 'image_data' and 'figure_content'

        Returns:
            Resend response dict with email_id
        """
        try:
            # Load corgi avatar from repo root
            if corgi_avatar_path is None:
                import os
                corgi_avatar_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "corgis.png")

            corgi_image_base64 = None
            try:
                with open(corgi_avatar_path, 'rb') as f:
                    corgi_bytes = f.read()
                    corgi_image_base64 = base64.b64encode(corgi_bytes).decode('utf-8')
            except Exception as e:
                print(f"Warning: Could not load corgi avatar: {e}")

            # Prepare panel images base64 if provided
            panel_images_base64 = []
            if panel_images:
                for panel_img in panel_images:
                    img_base64 = base64.b64encode(panel_img['image_data']).decode('utf-8')
                    panel_images_base64.append({
                        "panel_number": panel_img['panel_number'],
                        "base64": img_base64,
                        "url": panel_img.get('url', '')
                    })

            # Build HTML email content
            html_content = self._build_manga_html(
                topic=topic,
                manga_narrative=manga_narrative,
                panels=panels,
                corgi_avatar_base64=corgi_image_base64,
                panel_images_base64=panel_images_base64
            )

            # Prepare attachments if figures are provided
            attachments = []

            # Add corgi avatar as attachment with CID for embedding
            if corgi_image_base64:
                attachments.append({
                    "filename": "corgi_avatar.png",
                    "content": corgi_image_base64,
                })

            if figure_images:
                for i, fig in enumerate(figure_images, 1):
                    # Convert image bytes to base64
                    image_base64 = base64.b64encode(fig['image_data']).decode('utf-8')
                    attachments.append({
                        "filename": f"figure_{i}.png",
                        "content": image_base64,
                    })

            # Send email via Resend
            email_data = {
                "from": self.from_email,
                "to": [to_email],
                "subject": f"your manga research digest: {topic}",
                "html": html_content,
            }

            if attachments:
                email_data["attachments"] = attachments

            response = resend.Emails.send(email_data)

            return {
                "success": True,
                "email_id": response.get("id"),
                "message": "Manga digest sent successfully"
            }

        except Exception as e:
            print(f"Error sending email: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _build_manga_html(
        self,
        topic: str,
        manga_narrative: str,
        panels: List[Dict[str, str]],
        corgi_avatar_base64: str = None,
        panel_images_base64: List[Dict[str, str]] = None
    ) -> str:
        """Build HTML email content with black and white manga styling"""

        # Load logo for footer
        logo_base64 = None
        try:
            logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logo.png")
            with open(logo_path, 'rb') as f:
                logo_bytes = f.read()
                logo_base64 = base64.b64encode(logo_bytes).decode('utf-8')
        except Exception as e:
            print(f"Warning: Could not load logo: {e}")

        # Build corgi avatar HTML with black and white styling
        corgi_html = ""
        if corgi_avatar_base64:
            corgi_html = f"""
            <div style="text-align: center; margin: 30px 0;">
                <img src="data:image/png;base64,{corgi_avatar_base64}"
                     alt="corgi guide"
                     style="
                         width: 200px;
                         height: auto;
                         border: 6px solid #000;
                         background: #fff;
                         padding: 10px;
                         filter: grayscale(100%);
                     ">
                <p style="
                     margin: 15px 0 0 0;
                     font-size: 16px;
                     color: #000;
                     font-weight: bold;
                     font-family: monospace;
                     text-transform: lowercase;
                 ">
                    your friendly research guide
                </p>
            </div>
            """

        # Build panels HTML with black and white manga styling
        panels_html = ""

        # If we have panel images, display them from Supabase public URLs
        if panel_images_base64 and len(panel_images_base64) > 0:
            for i, panel_img in enumerate(panel_images_base64, 1):
                # Use Supabase public URL for the panel image
                img_url = panel_img.get('url', '')
                panels_html += f"""
                <div style="
                    margin: 40px 0;
                    padding: 0;
                    background: #fff;
                    border: 6px solid #000;
                    box-sizing: border-box;
                ">
                    <img src="{img_url}"
                         alt="Manga Panel {i}"
                         style="
                            width: 100%;
                            height: auto;
                            display: block;
                            margin: 0;
                            padding: 0;
                            filter: grayscale(100%) contrast(110%);
                         ">
                </div>
                """
        else:
            # Fallback to text-based panels if no images (black and white styling)
            for i, panel in enumerate(panels, 1):
                title = panel.get('title', f'Panel {i}')
                description = panel.get('description', '')
                dialogue = panel.get('dialogue', '')

                panels_html += f"""
                <div style="
                    margin: 30px 0;
                    padding: 20px;
                    border: 6px solid #000;
                    background: #fff;
                ">
                    <h3 style="
                        margin: 0 0 15px 0;
                        font-size: 24px;
                        font-weight: bold;
                        color: #000;
                        text-transform: uppercase;
                        font-family: monospace;
                        border-bottom: 3px solid #000;
                        padding-bottom: 10px;
                    ">panel {i}: {title}</h3>
                    <p style="
                        font-size: 16px;
                        line-height: 1.6;
                        margin: 15px 0;
                        color: #000;
                        font-family: monospace;
                    "><strong>scene:</strong> {description}</p>
                    {f'<div style="margin: 15px 0; padding: 15px; background: #fff; border: 3px solid #000;"><div style="font-size: 12px; color: #000; font-weight: bold; margin-bottom: 5px; font-family: monospace;">corgi says:</div><p style="font-size: 16px; margin: 0; color: #000; font-style: italic; line-height: 1.5; font-family: monospace;">{dialogue}</p></div>' if dialogue else ''}
                </div>
                """

        # Build logo section for footer
        logo_html = ""
        if logo_base64:
            logo_html = f"""
            <div style="text-align: center; margin: 40px 0 20px 0;">
                <img src="data:image/png;base64,{logo_base64}"
                     alt="mangalytics logo"
                     style="
                         width: 150px;
                         height: auto;
                         filter: grayscale(100%);
                         border: 4px solid #000;
                         background: #fff;
                         padding: 10px;
                     ">
            </div>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: monospace, 'Courier New', Arial, sans-serif;
                    background: #fff;
                    padding: 20px;
                    margin: 0;
                }}
                .container {{
                    max-width: 900px;
                    margin: 0 auto;
                    background: #fff;
                    border: 8px solid #000;
                    padding: 0;
                }}
                .header {{
                    background: #000;
                    color: #fff;
                    padding: 30px;
                    text-align: center;
                    border-bottom: 6px solid #000;
                }}
                .content {{
                    padding: 30px;
                    background: #fff;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div style="
                        display: inline-block;
                        background: #fff;
                        color: #000;
                        padding: 8px 20px;
                        font-size: 14px;
                        font-weight: bold;
                        margin-bottom: 15px;
                        border: 3px solid #fff;
                    ">manga digest</div>
                    <h1 style="
                        margin: 10px 0;
                        font-size: 36px;
                        text-transform: lowercase;
                        letter-spacing: 2px;
                    ">mangalytics</h1>
                    <p style="
                        margin: 5px 0 0 0;
                        font-size: 16px;
                        text-transform: lowercase;
                    ">topic: {topic}</p>
                </div>

                <div class="content">
                    {corgi_html}

                    <div style="margin: 40px 0 20px 0;">
                        <h2 style="
                            color: #000;
                            border-bottom: 4px solid #000;
                            padding-bottom: 10px;
                            font-size: 24px;
                            text-transform: lowercase;
                            font-weight: bold;
                        ">your manga story</h2>
                    </div>

                    {panels_html}

                    {logo_html}

                    <div style="
                        margin-top: 40px;
                        padding: 25px;
                        background: #000;
                        color: #fff;
                        text-align: center;
                        border: 6px solid #000;
                    ">
                        <p style="
                            margin: 0 0 15px 0;
                            font-size: 14px;
                            text-transform: lowercase;
                            font-weight: bold;
                        ">
                            special thanks to:
                        </p>
                        <p style="
                            margin: 5px 0;
                            font-size: 13px;
                            text-transform: lowercase;
                        ">
                            • reducto • firecrawl • lovable • resend •
                        </p>
                        <p style="
                            margin: 20px 0 0 0;
                            font-size: 12px;
                            text-transform: lowercase;
                            opacity: 0.8;
                        ">
                            generated by mangalytics • powered by gemini ai
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        return html


resend_service = ResendService()
