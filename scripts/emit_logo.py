import json
from pathlib import Path

d = json.load(open("/tmp/logo_paths.json"))
OUT = Path("static/img")
iw, ih = d["icon_vb"][2], d["icon_vb"][3]
lw, lh = d["lock_vb"][2], d["lock_vb"][3] + 1  # breathing room under the wordmark

HEADER = (
    "<!-- Mrentals brand guidelines v1.0. Two overlapping house silhouettes forming an\n"
    "     \"M\", topped by a diamond skylight at the point where the roof-lines meet.\n"
    "     Do not recolour outside the approved palette: #000000 / #1B9D80 / #FFFFFF. -->"
)


def paths(items, indent="    "):
    # One path with fill-rule="evenodd" so nested contours (the diamond's inner
    # window) punch through as holes instead of filling over each other.
    return f'{indent}<path d="{"".join(items)}"/>' 


def write(name, body):
    (OUT / name).write_text(body.rstrip() + "\n", encoding="utf-8")
    print("wrote", name)


# Icon only — black mark, for favicons, app icons and tight spaces.
write(
    "logo-icon.svg",
    f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {iw} {ih}" role="img" aria-label="Mrentals">
  <title>Mrentals</title>
  {HEADER}
  <g fill="currentColor" fill-rule="evenodd">
{paths(d["icon"])}
  </g>
</svg>''',
)

for name, mark_fill, word_fill in [
    ("logo-lockup.svg", "#000000", "#1B9D80"),
    ("logo-reversed.svg", "#FFFFFF", "#FFFFFF"),
    ("logo-mono.svg", "currentColor", "currentColor"),
]:
    write(
        name,
        f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {lw} {lh}" role="img" aria-label="Mrentals">
  <title>Mrentals</title>
  {HEADER}
  <g fill="{mark_fill}" fill-rule="evenodd">
{paths(d["lock_mark"])}
  </g>
  <g fill="{word_fill}" fill-rule="evenodd">
{paths(d["lock_word"])}
  </g>
</svg>''',
    )

# Favicon: rounded white tile so the mark keeps its clear space at 32px.
pad = 8
write(
    "favicon.svg",
    f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {iw + pad * 2} {iw + pad * 2}" role="img" aria-label="Mrentals">
  <title>Mrentals</title>
  <rect width="{iw + pad * 2}" height="{iw + pad * 2}" rx="18" fill="#FFFFFF"/>
  <g fill="#000000" fill-rule="evenodd" transform="translate({pad} {pad + (iw - ih) / 2:.1f})">
{paths(d["icon"], "    ")}
  </g>
</svg>''',
)
