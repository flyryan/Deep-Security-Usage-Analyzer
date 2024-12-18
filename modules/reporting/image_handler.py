"""
Image handling functionality for Deep Security Usage Analyzer reports.
"""
import base64
import re
import logging
from pathlib import Path
from typing import Dict
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

def embed_images_in_html(html_content: str, output_dir: Path, visualizations: Dict[str, plt.Figure]) -> str:
    """
    Embed existing PNG files from the output directory into the HTML content as base64 strings.

    Args:
        html_content (str): The HTML content to embed images into
        output_dir (Path): Directory containing the PNG files
        visualizations (Dict[str, plt.Figure]): Dictionary of visualization names

    Returns:
        str: The HTML content with embedded images
    """
    for name in visualizations.keys():
        try:
            # Get the path to the existing PNG file
            png_path = output_dir / f'{name}.png'
            
            if png_path.exists():
                # Read the existing PNG file
                with open(png_path, 'rb') as img_file:
                    img_data = img_file.read()
                
                # Encode the image as base64
                img_str = base64.b64encode(img_data).decode('utf-8')
                img_tag = f'data:image/png;base64,{img_str}'
                
                logger.debug(f"Embedding existing PNG for {name}")

                # Replace image source with embedded base64 string
                html_content = re.sub(
                    rf'<img\s+src=["\']{re.escape(name)}\.png["\']\s+alt=["\'].*?["\']\s*/?>',
                    f'<img src="{img_tag}" alt="{name.replace("_", " ").title()}">',
                    html_content,
                    flags=re.IGNORECASE
                )
            else:
                logger.warning(f"PNG file not found for {name}: {png_path}")
                
        except Exception as e:
            logger.error(f"Error embedding image {name}: {str(e)}")
            continue

    return html_content
