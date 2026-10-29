#!/usr/bin/env python3
"""Generates icons, title-bar logos and 10 themes for the Noros fork.
Usage: python3 tools/gen_assets.py <out_dir>   (out_dir = Telegram/Resources/noros)"""
import colorsys, io, os, random, re, sys, zipfile
from PIL import Image, ImageDraw, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'src')
OUT = sys.argv[1] if len(sys.argv) > 1 else 'out'
os.makedirs(os.path.join(OUT, 'themes'), exist_ok=True)

# ---------------------------------------------------------------- helpers
def hx(c):
    c = c.lstrip('#')
    return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
def to_hex(rgb): return '#%02x%02x%02x' % tuple(max(0, min(255, round(v))) for v in rgb)
def mix(a, b, t):
    a, b = hx(a), hx(b)
    return to_hex([a[i]*(1-t)+b[i]*t for i in range(3)])
def with_alpha(c, a): return c + '%02x' % round(a*255)

# ---------------------------------------------------------------- Noros logo (pixel wordmark)
NOROS_PATHS = [
 ("M12.7018 8.51063H8.46777V6.38297V4.25531H12.7018V8.51063Z"),
 ("M12.7018 8.51063H16.9357V0H21.1697V12.7659H12.7018V8.51063Z"),
 ("M23.1753 12.7659H35.8772V0H23.1753V12.7659ZM31.6433 4.25531V8.51063H27.4093V4.25531H31.6433Z"),
 ("M52.5903 12.7659V0H65.2923V12.7659H52.5903ZM61.0583 8.51063V4.25531H56.8243V8.51063H61.0583Z"),
 ("M42.1168 12.7659V4.25531H50.5848V0H42.1168L42.1168 4.25531H37.8828V12.7659H42.1168Z"),
 ("M71.5318 8.51063H67.2978V12.7659H75.7658V4.25531H79.9998V0H71.5318V8.51063Z"),
 ("M0 0H4.23398L8.46798 1.7157e-05V4.25533L4.23398 4.25531L4.23399 12.766H1.02733e-05L0 4.25531V0Z"),
]
def parse_subpaths(d):
    toks = re.findall(r'[MHVLZ]|-?\d*\.?\d+(?:e-?\d+)?', d)
    subs, cur, x, y, i, cmd = [], [], 0, 0, 0, None
    while i < len(toks):
        t = toks[i]
        if t in 'MHVLZ':
            cmd = t; i += 1
            if cmd == 'Z':
                if cur: subs.append(cur); cur = []
                continue
        if cmd == 'M': x, y = float(toks[i]), float(toks[i+1]); i += 2; cur = [(x, y)]; cmd = 'L'
        elif cmd == 'L': x, y = float(toks[i]), float(toks[i+1]); i += 2; cur.append((x, y))
        elif cmd == 'H': x = float(toks[i]); i += 1; cur.append((x, y))
        elif cmd == 'V': y = float(toks[i]); i += 1; cur.append((x, y))
    if cur: subs.append(cur)
    return subs
def noros_mask(width, only=None):
    """Alpha mask of the wordmark (or of the N glyph if only='N')."""
    scale = width / 80.0
    big = 4
    W, H = int(80*scale*big), int(13*scale*big)
    mask = Image.new('L', (W, H), 0)
    idx = range(len(NOROS_PATHS)) if only is None else ([0, 1, 6] if only == 'N' else [])
    for pi in idx:
        pm = Image.new('L', (W, H), 0)
        for sp in parse_subpaths(NOROS_PATHS[pi]):
            sm = Image.new('L', (W, H), 0)
            ImageDraw.Draw(sm).polygon([(px*scale*big, py*scale*big) for px, py in sp], fill=255)
            pm = ImageChops.difference(pm, sm)  # even-odd
        mask = ImageChops.lighter(mask, pm)
    if only == 'N':
        bb = mask.getbbox(); mask = mask.crop(bb)
    return mask.resize((mask.width//big, mask.height//big), Image.LANCZOS)
def solid(mask, color, a=255):
    im = Image.new('RGBA', mask.size, hx(color) + (0,)); im.putalpha(mask.point(lambda v: v*a//255)); return im

# ---------------------------------------------------------------- icons
def squircle_mask(n, r=0.225):
    big = n*4
    m = Image.new('L', (big, big), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, big-1, big-1), radius=int(big*r), fill=255)
    return m.resize((n, n), Image.LANCZOS)
def radial(n, cx, cy, rad, color, a):
    g = Image.new('L', (n, n), 0); d = ImageDraw.Draw(g)
    steps = 60
    for s in range(steps, 0, -1):
        t = s/steps; v = int(255*a*(1-t)**1.6)
        rr = rad*t; d.ellipse((cx-rr, cy-rr, cx+rr, cy+rr), fill=v)
    g = g.filter(ImageFilter.GaussianBlur(n/60))
    im = Image.new('RGBA', (n, n), hx(color) + (0,)); im.putalpha(g); return im
def linear_grad(n, c1, c2):
    import numpy as np
    y, x = np.mgrid[0:n, 0:n].astype('float32') / (n-1)
    t = ((x + y) / 2)[..., None]
    a = np.array(hx(c1), 'float32'); b = np.array(hx(c2), 'float32')
    return Image.fromarray((a*(1-t) + b*t).astype('uint8'), 'RGB')
def finish_icon(base, n=1024):
    """Apply squircle mask, glass highlight, rim, soft shadow on transparent 1024 canvas."""
    pad = int(n*0.06); inner = n - 2*pad
    ic = base.resize((inner, inner), Image.LANCZOS).convert('RGBA')
    mk = squircle_mask(inner)
    # top glass highlight
    hi = Image.new('RGBA', (inner, inner), (0, 0, 0, 0)); d = ImageDraw.Draw(hi)
    d.ellipse((-inner*0.25, -inner*0.85, inner*1.25, inner*0.42), fill=(255, 255, 255, 30))
    ic = Image.alpha_composite(ic, hi.filter(ImageFilter.GaussianBlur(inner*0.02)))
    rim = Image.new('RGBA', (inner, inner), (0, 0, 0, 0))
    ImageDraw.Draw(rim).rounded_rectangle((1, 1, inner-2, inner-2), radius=int(inner*0.225), outline=(255, 255, 255, 60), width=max(2, inner//220))
    ic = Image.alpha_composite(ic, rim)
    ic.putalpha(ImageChops.multiply(ic.getchannel('A'), mk))
    out = Image.new('RGBA', (n, n), (0, 0, 0, 0))
    sh = Image.new('RGBA', (n, n), (0, 0, 0, 0)); sh.paste((0, 0, 0, 120), (pad, pad+int(n*0.015)), mk)
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(n*0.018)))
    out.alpha_composite(ic, (pad, pad))
    return out

def icon_noros(n=1024):
    base = linear_grad(n, '#8286ff', '#3338bd').convert('RGBA')
    base.alpha_composite(radial(n, n*0.25, n*0.15, n*0.7, '#c9cbff', 0.55))
    base.alpha_composite(radial(n, n*0.85, n*1.0, n*0.7, '#1b1e78', 0.7))
    g = noros_mask(int(n*0.5*80/21.2), 'N')
    h = int(g.height*0.0)  # keep aspect
    glyph = solid(g, '#ffffff')
    sh = solid(g, '#14166b', 120).filter(ImageFilter.GaussianBlur(n*0.012))
    pos = ((n-g.width)//2, (n-g.height)//2)
    base.alpha_composite(sh, (pos[0], pos[1]+int(n*0.02)))
    base.alpha_composite(glyph, pos)
    return finish_icon(base, n)
def icon_valutix(n=1024):
    base = Image.new('RGBA', (n, n), hx('#050807') + (255,))
    base.alpha_composite(radial(n, n*0.5, n*0.5, n*0.62, '#2fae4d', 0.55))
    base.alpha_composite(radial(n, n*0.9, n*0.05, n*0.5, '#4fd46b', 0.25))
    mark = Image.open(os.path.join(SRC, 'VX_ICON.png')).convert('RGBA')
    s = int(n*0.56); mark = mark.resize((int(mark.width*s/mark.height), s), Image.LANCZOS)
    pad = int(n*0.12)
    ga = Image.new('L', (mark.width+2*pad, mark.height+2*pad), 0); ga.paste(mark.getchannel('A'), (pad, pad))
    glow = Image.new('RGBA', ga.size, (79, 212, 107, 0)); glow.putalpha(ga.filter(ImageFilter.GaussianBlur(n*0.03)).point(lambda v: int(v*.8)))
    pos = ((n-mark.width)//2, (n-mark.height)//2)
    base.alpha_composite(glow, (pos[0]-pad, pos[1]-pad))
    base.alpha_composite(mark, pos)
    return finish_icon(base, n)
def icon_riopay(n=1024):
    base = linear_grad(n, '#1b1c33', '#090a14').convert('RGBA')
    base.alpha_composite(radial(n, n*0.2, n*0.1, n*0.7, '#f89aa4', 0.28))
    base.alpha_composite(radial(n, n*0.9, n*0.95, n*0.7, '#90c8f8', 0.30))
    logo = Image.open(os.path.join(SRC, 'RIO_LOGO.png')).convert('RGBA')
    r = logo.crop((0, 0, 60, 74))  # the pastel "R"
    r = r.crop(r.getbbox())
    s = int(n*0.52); r = r.resize((int(r.width*s/r.height), s), Image.LANCZOS)
    pos = ((n-r.width)//2, (n-r.height)//2)
    pad = int(n*0.12)
    ga = Image.new('RGBA', (r.width+2*pad, r.height+2*pad), (0, 0, 0, 0)); ga.paste(r, (pad, pad))
    base.alpha_composite(ga.filter(ImageFilter.GaussianBlur(n*0.035)), (pos[0]-pad, pos[1]-pad)); base.alpha_composite(r, pos)
    return finish_icon(base, n)

ICONS = {'noros': icon_noros, 'valutix': icon_valutix, 'riopay': icon_riopay}
for name, fn in ICONS.items():
    big = fn(1024)
    for s in (16, 32, 48, 64, 128, 256, 512):
        big.resize((s, s), Image.LANCZOS).save(os.path.join(OUT, f'icon_{name}_{s}.png'))
    big.save(os.path.join(OUT, f'icon_{name}.ico'), sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    big.resize((512, 512), Image.LANCZOS).save(os.path.join(OUT, f'icon_{name}.png'))

# ---------------------------------------------------------------- title-bar logos (for light and dark title)
LOGO_H = 96
def save_logo(name, light_title, im):
    im = im.convert('RGBA'); im = im.crop(im.getbbox())
    im = im.resize((int(im.width*LOGO_H/im.height), LOGO_H), Image.LANCZOS)
    im.save(os.path.join(OUT, f'logo_{name}_{"onlight" if light_title else "ondark"}.png'))
nm = noros_mask(640)
save_logo('noros', True, solid(nm, '#4f53e1'))
save_logo('noros', False, solid(nm, '#8e92ff'))
save_logo('valutix', False, Image.open(os.path.join(SRC, 'VX_LOGO.png')))
save_logo('valutix', True, Image.open(os.path.join(SRC, 'VX_LOGO_L.png')))
save_logo('riopay', False, Image.open(os.path.join(SRC, 'RIO_LOGO.png')))
save_logo('riopay', True, Image.open(os.path.join(SRC, 'RIO_LOGO_L.png')))

# ---------------------------------------------------------------- themes
class Pal:  # token set for one colour theme
    def __init__(s, **k): s.__dict__.update(k)
THEMES = {
 'light': Pal(base='day', title='Светлая', bg='#f4f5f7', surface='#ffffff', surface2='#eceef2', line='#e1e4ea', text='#111318', sub='#6b7280',
              primary='#2f6df6', ink='#ffffff', link='#2f6df6', blobs=['#9db8ff', '#c7d6ff', '#ffd6e5'], hue_bg=None),
 'dark':  Pal(base='night', title='Тёмная', bg='#111318', surface='#1a1d24', surface2='#242833', line='#2c303b', text='#eef0f5', sub='#8b93a7',
              primary='#5b8cff', ink='#ffffff', link='#7fa6ff', blobs=['#2d4fb8', '#5a3fb0', '#1c7a8c'], hue_bg=None),
 'noros': Pal(base='day', title='Noros', bg='#f3f4fb', surface='#ffffff', surface2='#eef0fa', line='#e1e4f2', text='#0d0e1a', sub='#6a6e8a',
              primary='#4f53e1', ink='#ffffff', link='#4f53e1', blobs=['#8a8dff', '#c4c6ff', '#e0d4ff'], hue_bg=None),
 'valutix': Pal(base='night', title='Valutix', bg='#000000', surface='#0c0c0c', surface2='#1e1e1e', line='#232323', text='#f3f3f3', sub='#8c8c8c',
              primary='#4fd46b', ink='#04140a', link='#4fd46b', blobs=['#1f7a3d', '#4fd46b', '#14503a'], hue_bg=None),
 'riopay': Pal(base='night', title='RioPay', bg='#0e0f1a', surface='#171829', surface2='#23253b', line='#33365a', text='#f4f5fb', sub='#9a9db8',
              primary='#f89aa4', ink='#1c0f1d', link='#90c8f8', blobs=['#c4586f', '#4f86c4', '#c49a52'], hue_bg=None),
}
def read_theme(name):
    d = {}; order = []
    for l in open(os.path.join(SRC, name + '.colors'), encoding='utf8'):
        m = re.match(r'(\w+):\s*([^;]+);', l)
        if m: d[m.group(1)] = m.group(2).strip(); order.append(m.group(1))
    return d, order
DAY, DAY_ORDER = read_theme('day-custom-base')
NIGHT, _ = read_theme('night-custom-base')
def hsl_of(c):
    r, g, b = [v/255 for v in hx(c[:7])]; h, l, s = colorsys.rgb_to_hls(r, g, b); return h*360, s, l
def invert_neutral(val):
    if not val.startswith('#'): return val
    h, s, l = hsl_of(val)
    if s < .25: l = 1-l*0.92
    r, g, b = colorsys.hls_to_rgb(h/360, l, s); return to_hex((r*255, g*255, b*255)) + val[7:]
def remap(val, T, dark):
    """Rotate Telegram's blue family to the brand hue, retint dark backgrounds."""
    if not val.startswith('#'): return val
    h, s, l = hsl_of(val); a = val[7:]
    if not (190 <= h <= 250 and s > .12): return val
    th, ts, tl = hsl_of(T.primary); bh, bs, bl = hsl_of(T.bg)
    if dark and l < .36:
        nh, ns = (bh, min(bs*1.4, .5)) if bs > .03 else (0, 0)
        if bs < .03: l = l*(0.0 if T.bg == '#000000' else 1)*(1 if T.bg != '#000000' else 1)
        if T.bg == '#000000': l *= .45
        ns = ns
    else:
        nh, ns = th, min(max(s, ts*.7), ts)
        if dark: l = max(l, .5)
    r, g, b = colorsys.hls_to_rgb(nh/360, l, ns); return to_hex((r*255, g*255, b*255)) + a

def build_palette(key, T, glass):
    dark = T.base == 'night'
    base = dict(NIGHT) if dark else dict(DAY)
    for k in DAY_ORDER:
        if k not in base: base[k] = invert_neutral(DAY[k]) if dark else DAY[k]
    pal = {k: remap(v, T, dark) for k, v in base.items()}
    S = T.surface; S2 = T.surface2; P = T.primary
    inbg = with_alpha(S, .66) if glass else S
    outbg = with_alpha(mix(S, P, .55 if dark else .32), .74) if glass else mix(S, P, .30 if dark else .16)
    chrome = mix(T.bg, '#ffffff', .05) if (glass and dark) else (mix(T.bg, '#ffffff', .6) if glass else T.bg)
    o = {
     'windowBg': S, 'windowFg': T.text, 'windowBgOver': S2, 'windowBgRipple': mix(S2, T.text, .06),
     'windowFgOver': T.text, 'windowSubTextFg': T.sub, 'windowSubTextFgOver': mix(T.sub, T.text, .2),
     'windowBoldFg': T.text, 'windowBoldFgOver': T.text, 'windowBgActive': P, 'windowFgActive': T.ink,
     'windowActiveTextFg': T.link, 'windowShadowFgFallback': T.bg,
     'activeButtonBg': P, 'activeButtonBgOver': mix(P, '#ffffff', .12), 'activeButtonBgRipple': mix(P, '#ffffff', .24),
     'activeButtonFg': T.ink, 'activeButtonFgOver': T.ink, 'activeButtonSecondaryFg': mix(T.ink, P, .3), 'activeLineFg': P,
     'lightButtonBg': S, 'lightButtonBgOver': S2, 'lightButtonBgRipple': mix(S2, T.text, .06), 'lightButtonFg': T.link, 'lightButtonFgOver': T.link,
     'menuBg': S, 'menuBgOver': S2, 'menuBgRipple': mix(S2, T.text, .06),
     'dialogsBg': chrome if glass else S, 'dialogsBgOver': S2, 'dialogsBgRipple': mix(S2, T.text, .06),
     'dialogsBgActive': P, 'dialogsNameFg': T.text, 'dialogsNameFgOver': T.text, 'dialogsNameFgActive': T.ink,
     'dialogsTextFg': T.sub, 'dialogsTextFgOver': T.sub, 'dialogsTextFgActive': mix(T.ink, P, .15),
     'dialogsDateFg': T.sub, 'dialogsDateFgActive': mix(T.ink, P, .15), 'dialogsUnreadBg': P, 'dialogsUnreadFg': T.ink,
     'dialogsUnreadBgActive': T.ink, 'dialogsUnreadFgActive': P,
     'historyComposeAreaBg': S, 'historyComposeAreaFg': T.text, 'historyComposeAreaFgService': T.sub,
     'msgInBg': inbg, 'msgInBgSelected': mix(S, P, .35), 'msgOutBg': outbg, 'msgOutBgSelected': mix(S, P, .5),
     'historyTextInFg': T.text, 'historyTextOutFg': T.text, 'msgInDateFg': T.sub, 'msgOutDateFg': mix(T.text, T.sub, .5),
     'historyLinkInFg': T.link, 'historyLinkOutFg': T.link, 'msgInServiceFg': T.link, 'msgOutServiceFg': T.link,
     'msgInReplyBarColor': P, 'msgOutReplyBarColor': P,
     'titleBg': T.bg, 'titleBgActive': T.bg, 'titleFg': T.sub, 'titleFgActive': T.text,
     'boxBg': S, 'boxTextFg': T.text, 'boxTitleFg': T.text, 'boxSubTitleFg': T.sub,
     'inputBorderFg': T.line, 'filterInputActiveBg': S2, 'filterInputInactiveBg': S2,
     'sliderBgActive': P, 'sliderBgInactive': T.line, 'checkboxFg': T.sub, 'radialFg': P,
     'profileVerifiedCheckBg': P, 'overviewCheckBgActive': P, 'emojiPanBg': S, 'emojiPanCategories': S,
     'historyScrollBarBg': with_alpha(T.sub, .35), 'historyScrollBarBgOver': with_alpha(T.sub, .55),
     'scrollBarBg': with_alpha(T.sub, .35), 'scrollBarBgOver': with_alpha(T.sub, .55), 'scrollBg': with_alpha(T.sub, .12), 'scrollBgOver': with_alpha(T.sub, .2),
     'shadowFg': '#00000030' if not dark else '#00000070',
     'historyToDownBg': S, 'historyToDownBgOver': S2, 'historyToDownFg': T.sub,
     'historyComposeIconFg': T.sub, 'historyComposeIconFgOver': T.link, 'historySendIconFg': P, 'historySendIconFgOver': mix(P, '#ffffff', .15),
    }
    if glass:
        o.update({'msgInShadow': '#ffffff22' if dark else '#ffffff99', 'msgOutShadow': '#ffffff22' if dark else '#ffffff99',
                  'msgServiceBg': with_alpha(S, .55), 'msgServiceBgSelected': with_alpha(S, .75), 'historyComposeAreaBg': with_alpha(S, .92)})
    o = {k: v for k, v in o.items() if k in pal}
    pal.update(o)
    return pal, [k for k in o if k not in pal]

def wallpaper(T, glass, size=(1600, 1000)):
    if not glass:
        return Image.new('RGB', (64, 64), hx(mix(T.bg, T.surface, .5) if T.bg != '#000000' else '#050505')), True
    rnd = random.Random(T.primary)
    W, H = size
    base = Image.new('RGB', size, hx(T.bg))
    layer = Image.new('RGB', size, hx(T.bg))
    d = ImageDraw.Draw(layer)
    pts = [(.15, .2, .42), (.8, .15, .38), (.55, .78, .5), (.1, .85, .3), (.92, .7, .32)]
    for i, (x, y, r) in enumerate(pts):
        c = T.blobs[i % len(T.blobs)]; rr = r*min(W, H)
        d.ellipse((x*W-rr, y*H-rr, x*W+rr, y*H+rr), fill=hx(c))
    layer = layer.filter(ImageFilter.GaussianBlur(min(W, H)*.16))
    dark = T.base == 'night'
    img = Image.blend(base, layer, .55 if dark else .75)
    # soft light "glass sheen" bands
    sh = Image.new('RGBA', size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    sd.polygon([(0, H*.55), (W, H*.15), (W, H*.3), (0, H*.75)], fill=(255, 255, 255, 14 if dark else 40))
    img = Image.alpha_composite(img.convert('RGBA'), sh.filter(ImageFilter.GaussianBlur(40))).convert('RGB')
    return img, False

def theme_text(pal):
    return '\n'.join(f'{k}: {v};' for k, v in pal.items()) + '\n'

report = []
for tkey, T in THEMES.items():
    for design in ('material', 'glass'):
        pal, miss = build_palette(tkey, T, design == 'glass')
        wp, tiled = wallpaper(T, design == 'glass')
        buf = io.BytesIO(); wp.save(buf, 'JPEG', quality=88)
        colors = theme_text(pal)
        if tiled: colors = '// tiled\n' + colors
        path = os.path.join(OUT, 'themes', f'{tkey}_{design}.tdesktop-theme')
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('colors.tdesktop-theme', colors)
            z.writestr('tiled.jpg' if tiled else 'background.jpg', buf.getvalue())
        report.append((tkey, design, len(pal), os.path.getsize(path)))
for r in report: print(r)
