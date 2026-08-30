import os
import subprocess
import sys
from pathlib import Path

def convert_svg_to_png():
    root = Path(__file__).resolve().parent.parent
    pitch_dir = root / "pitch"
    png_dir = pitch_dir / "pngs"
    png_dir.mkdir(parents=True, exist_ok=True)

    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome_path):
        chrome_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

    svg_files = [
        ("architecture.svg", "architecture.png", 2800, 1960),
        ("dataflow.svg", "dataflow.png", 2800, 2040),
        ("responsibility_flow.svg", "responsibility_flow.png", 2800, 1920),
    ]

    for svg_name, png_name, width, height in svg_files:
        svg_path = pitch_dir / svg_name
        png_path = png_dir / png_name

        if not svg_path.exists():
            print(f"Error: {svg_path} not found")
            continue

        # Create temporary HTML file
        svg_content = svg_path.read_text(encoding="utf-8")
        html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: #080e1a; width: {width // 2}px; height: {height // 2}px; overflow: hidden; display: flex; }}
  svg {{ width: 100%; height: 100%; display: block; }}
</style>
</head>
<body>
{svg_content}
</body>
</html>"""

        temp_html = pitch_dir / f"temp_{svg_name}.html"
        temp_html.write_text(html_content, encoding="utf-8")

        # Run headless browser screenshot with device scale factor 2
        cmd = [
            chrome_path,
            "--headless",
            "--disable-gpu",
            "--hide-scrollbars",
            f"--window-size={width // 2},{height // 2}",
            "--force-device-scale-factor=2",
            f"--screenshot={str(png_path)}",
            f"file:///{str(temp_html).replace('\\', '/')}"
        ]

        print(f"Rendering {svg_name} -> {png_name} ({width}x{height})...")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and png_path.exists():
            print(f"Successfully generated {png_path} ({os.path.getsize(png_path):,} bytes)")
        else:
            print(f"Failed to generate {png_path}: {res.stderr}")

        if temp_html.exists():
            temp_html.unlink()

if __name__ == "__main__":
    convert_svg_to_png()
