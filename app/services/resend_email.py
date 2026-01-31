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
                "from": "mangalytics <onboarding@resend.dev>",  # Update with your verified domain
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
        """Build HTML email content with manga styling and corgi avatar"""

        # Build corgi avatar HTML
        corgi_html = ""
        if corgi_avatar_base64:
            corgi_html = f"""
            <div style="text-align: center; margin: 20px 0;">
                <img src="data:image/png;base64,{corgi_avatar_base64}"
                     alt="corgi guide"
                     style="width: 150px; height: auto; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <p style="margin: 10px 0 0 0; font-size: 14px; color: #7f8c8d; font-style: italic;">
                    your friendly research guide
                </p>
            </div>
            """

        # Build panels HTML
        panels_html = ""

        # If we have panel images, display them as images
        if panel_images_base64 and len(panel_images_base64) > 0:
            for i, panel_img in enumerate(panel_images_base64, 1):
                img_base64 = panel_img['base64']
                panels_html += f"""
                <div style="
                    margin: 30px 0;
                    text-align: center;
                ">
                    <img src="data:image/png;base64,{img_base64}"
                         alt="Panel {i}"
                         style="
                            max-width: 100%;
                            height: auto;
                            border: 8px solid #000;
                            border-radius: 10px;
                            box-shadow: 10px 10px 0px rgba(0,0,0,0.3);
                         ">
                </div>
                """
        else:
            # Fallback to text-based panels if no images
            for i, panel in enumerate(panels, 1):
                title = panel.get('title', f'Panel {i}')
                description = panel.get('description', '')
                dialogue = panel.get('dialogue', '')

                panels_html += f"""
                <div style="
                    margin: 20px 0;
                    padding: 20px;
                    border: 3px solid #000;
                    border-radius: 10px;
                    background: #fff;
                    box-shadow: 5px 5px 0px #000;
                ">
                    <h3 style="
                        margin: 0 0 10px 0;
                        font-size: 24px;
                        font-weight: bold;
                        color: #e74c3c;
                        text-transform: uppercase;
                    ">Panel {i}: {title}</h3>
                    <p style="
                        font-size: 16px;
                        line-height: 1.6;
                        margin: 10px 0;
                        color: #333;
                    "><strong>Scene:</strong> {description}</p>
                    {f'<div style="margin: 15px 0; padding: 15px; background: #fff3cd; border: 2px solid #ffc107; border-radius: 8px; position: relative;"><div style="font-size: 12px; color: #856404; font-weight: bold; margin-bottom: 5px;">CORGI SAYS:</div><p style="font-size: 16px; margin: 0; color: #856404; font-style: italic; line-height: 1.5;">{dialogue}</p></div>' if dialogue else ''}
                </div>
                """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Arial', 'Comic Sans MS', sans-serif;
                    background: #f9f9f9;
                    padding: 20px;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    padding: 30px;
                    border-radius: 15px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                    text-align: center;
                }}
                .manga-badge {{
                    display: inline-block;
                    background: #ff6b6b;
                    color: white;
                    padding: 5px 15px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="manga-badge">MANGA DIGEST</div>
                    <h1 style="margin: 10px 0; font-size: 32px;">mangalytics research</h1>
                    <p style="margin: 0; font-size: 18px; opacity: 0.9;">topic: {topic}</p>
                </div>

                {corgi_html}

                <div style="margin: 30px 0;">
                    <h2 style="
                        color: #2c3e50;
                        border-bottom: 3px solid #3498db;
                        padding-bottom: 10px;
                        font-size: 28px;
                    ">your manga story</h2>
                    {panels_html}
                </div>

                <div style="
                    margin-top: 40px;
                    padding: 20px;
                    background: #ecf0f1;
                    border-radius: 10px;
                    text-align: center;
                ">
                    <p style="margin: 0; color: #7f8c8d; font-size: 14px;">
                        generated by mangalytics • powered by gemini ai & reducto
                    </p>
                    <p style="margin: 10px 0 0 0; color: #95a5a6; font-size: 12px;">
                        check your attachments for the original research figures
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        return html


resend_service = ResendService()
