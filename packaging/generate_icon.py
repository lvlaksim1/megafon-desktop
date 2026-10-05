from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in ("arialbd.ttf", "segoeuib.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def main() -> None:
    size = 256
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    margin = 15
    draw.rounded_rectangle(
        (margin, margin, size - margin, size - margin),
        radius=50,
        fill=(0, 185, 86, 255),
    )
    draw.ellipse((177, 33, 223, 79), fill=(110, 53, 200, 255))

    font = _font(138)
    box = draw.textbbox((0, 0), "M", font=font)
    width = box[2] - box[0]
    height = box[3] - box[1]
    draw.text(
        ((size - width) / 2, (size - height) / 2 - 10),
        "M",
        font=font,
        fill=(255, 255, 255, 255),
    )

    output = Path("build/icon/megafon-desktop.ico")
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(
        output,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )


if __name__ == "__main__":
    main()
