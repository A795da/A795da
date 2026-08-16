import json
import html as htmllib

with open('panels_layout_data.json', encoding='utf-8') as f:
    data = json.load(f)

MONO_FONT = "Consolas, 'Courier New', monospace"
SERIF_FONT = "Georgia, 'Times New Roman', serif"


def resolved_font(raw, size_override=None):
    """Swap the browser-measured font string's family for an explicit,
    portable stack, keeping style/weight/size (which the widths were
    measured against)."""
    is_prop = 'Terminal' in raw
    family = SERIF_FONT if is_prop else MONO_FONT
    weight = '700' if ' 700 ' in raw else '400'
    style = 'italic' if raw.startswith('italic') else 'normal'
    return family, weight, style


elements = [] 

for b in data['blocks']:
    if b['type'] == 'linkedin':
        elements.append({
            'kind': 'linkedin', 'href': b['href'], 'text': b['text'],
            'x': b['left'], 'y': b['top'], 'w': b['width'], 'h': b['height'],
        })
    elif b['type'] == 'styled-lines':
        for ln in b['lines']:
            family, weight, style = resolved_font(ln['font'])
            fs = float(ln['font'].split()[-2].replace('px', '')) if False else None
            # font string like "italic 400 18px Terminal" or "normal 700 18px Terminal"
            parts = ln['font'].split()
            fs = float(parts[-2].replace('px', ''))
            elements.append({
                'kind': 'text', 'x': ln['left'], 'y': ln['top'], 'font_size': fs,
                'family': family, 'weight': weight, 'style': style,
                'lines': [ln['text']], 'line_height': fs * 1.15,
                'right': ln['left'] + ln['width'], 'bottom': ln['top'] + ln['height'],
            })
    elif b['type'] == 'plain':
        family, weight, style = resolved_font(b['font'])
        elements.append({
            'kind': 'text', 'x': b['left'], 'y': b['top'], 'font_size': b['fontSize'],
            'family': family, 'weight': weight, 'style': style,
            'lines': b['lines'], 'line_height': b['lineHeight'],
            'right': b['left'] + b['widest'], 'bottom': b['top'] + b['lineCount'] * b['lineHeight'],
        })

avatar = data['avatar']
family, weight, style = resolved_font(avatar['font'])
elements.insert(0, {
    'kind': 'text', 'x': avatar['left'], 'y': avatar['top'], 'font_size': avatar['fontSize'],
    'family': family, 'weight': weight, 'style': style,
    'lines': avatar['lines'], 'line_height': avatar['lineHeight'],
    'right': avatar['left'] + avatar['widest'], 'bottom': avatar['top'] + avatar['lineCount'] * avatar['lineHeight'],
})

MARGIN = 12
max_right = max(
    (e.get('right', e.get('x', 0) + e.get('w', 0)) for e in elements), default=0
)
max_bottom = max(
    (e.get('bottom', e.get('y', 0) + e.get('h', 0)) for e in elements), default=0
)
min_left = min((e['x'] for e in elements), default=0)
min_top = min((e['y'] for e in elements), default=0)

shift_x = MARGIN - min_left if min_left < 0 else 0
shift_y = MARGIN - min_top if min_top < 0 else 0

canvas_w = int(max_right + shift_x + MARGIN)
canvas_h = int(max_bottom + shift_y + MARGIN)

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_w} {canvas_h}" '
    f'width="{canvas_w}" height="{canvas_h}">',
    f'<rect x="0" y="0" width="{canvas_w}" height="{canvas_h}" fill="#000"/>',
]

for e in elements:
    x = e['x'] + shift_x
    y = e['y'] + shift_y

    if e['kind'] == 'linkedin':
        w, h = e['w'], e['h']
        parts.append(f'<a href="{htmllib.escape(e["href"])}" target="_blank">')
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'fill="none" stroke="#fff" stroke-width="1.5"/>'
        )
        parts.append(
            f'<text x="{x + w/2:.1f}" y="{y + h/2 + 5:.1f}" text-anchor="middle" '
            f'font-family="{MONO_FONT}" font-size="14" fill="#fff">{htmllib.escape(e["text"])}</text>'
        )
        parts.append('</a>')
        continue

    weight_attr = f' font-weight="{e["weight"]}"' if e['weight'] == '700' else ''
    style_attr = f' font-style="{e["style"]}"' if e['style'] == 'italic' else ''
    parts.append(
        f'<text x="{x:.1f}" y="{y + e["font_size"]:.1f}" font-family="{e["family"]}" '
        f'font-size="{e["font_size"]}"{weight_attr}{style_attr} fill="#fff" xml:space="preserve">'
    )
    for i, line in enumerate(e['lines']):
        dy = 0 if i == 0 else e['line_height']
        safe = htmllib.escape(line) if line.strip() else ' '
        parts.append(f'<tspan x="{x:.1f}" dy="{dy:.2f}">{safe}</tspan>')
    parts.append('</text>')

parts.append('</svg>')

with open('panels.svg', 'w', encoding='utf-8') as f:
    f.write('\n'.join(parts))

print(f'Wrote panels.svg ({canvas_w}x{canvas_h}, {len(elements)} elements)')
