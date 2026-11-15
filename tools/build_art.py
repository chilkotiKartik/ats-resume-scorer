"""
Builds the app's original illustrations into frontend/static/art/.

Scout is the scorer's mascot: a sheet of resume paper with a highlighter.
Every pose is a standalone animated SVG (CSS keyframes inside the file), so
it animates anywhere it's shown with a plain <img>. Animations switch off
under prefers-reduced-motion.

    python tools/build_art.py
"""

from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "frontend" / "static" / "art"

INK = "#1E1B3A"
PAPER = "#FFFFFF"
LINE = "#C9CEDB"
MARKER = "#FFD23F"
CHEEK = "#FF9DB0"
SHOE = "#FF5A4E"
MINT = "#3DDC97"
SKY = "#4DA3FF"
GRAPE = "#7B5CFF"

BASE_CSS = f"""
.ink {{ stroke: {INK}; stroke-width: 5; stroke-linecap: round; stroke-linejoin: round; }}
.thin {{ stroke: {INK}; stroke-width: 3.5; stroke-linecap: round; stroke-linejoin: round; fill: none; }}
.v {{ transform-box: view-box; }}
@media (prefers-reduced-motion: no-preference) {{
  .bob {{ animation: bob 2.6s ease-in-out infinite; }}
  .shadow {{ animation: shadow 2.6s ease-in-out infinite; transform-origin: 120px 246px; }}
  .eyes {{ animation: blink 4.2s infinite; transform-origin: 120px 98px; }}
  .wave {{ animation: wave 1.1s ease-in-out infinite alternate; transform-origin: 178px 132px; }}
  .tw {{ animation: twinkle 1.8s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
  .tw2 {{ animation: twinkle 1.8s ease-in-out .6s infinite; transform-box: fill-box; transform-origin: center; }}
  .tw3 {{ animation: twinkle 1.8s ease-in-out 1.2s infinite; transform-box: fill-box; transform-origin: center; }}
  .jump {{ animation: jump 1s cubic-bezier(.3,.0,.3,1) infinite; }}
  .cheerL {{ animation: cheerL .5s ease-in-out infinite alternate; transform-origin: 62px 132px; }}
  .cheerR {{ animation: cheerR .5s ease-in-out infinite alternate; transform-origin: 178px 132px; }}
  .dot1 {{ animation: dot 1.5s ease-in-out infinite; }}
  .dot2 {{ animation: dot 1.5s ease-in-out .25s infinite; }}
  .dot3 {{ animation: dot 1.5s ease-in-out .5s infinite; }}
  .drop {{ animation: drop 1.6s ease-in infinite; }}
  .shiver {{ animation: shiver .18s linear infinite alternate; transform-origin: 120px 200px; }}
  .stroke {{ stroke-dasharray: 60; animation: swipe 2.2s ease-in-out infinite; }}
  .look {{ animation: look 3.4s ease-in-out infinite; }}
  .conf {{ animation: fall 1.6s linear infinite; }}
}}
@keyframes bob {{ 0%,100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-7px); }} }}
@keyframes shadow {{ 0%,100% {{ transform: scaleX(1); opacity:.18; }} 50% {{ transform: scaleX(.86); opacity:.12; }} }}
@keyframes blink {{ 0%,90%,100% {{ transform: scaleY(1); }} 94% {{ transform: scaleY(.08); }} }}
@keyframes wave {{ from {{ transform: rotate(-12deg); }} to {{ transform: rotate(22deg); }} }}
@keyframes twinkle {{ 0%,100% {{ transform: scale(.6) rotate(0deg); opacity:.5; }} 50% {{ transform: scale(1.1) rotate(20deg); opacity:1; }} }}
@keyframes jump {{ 0%,100% {{ transform: translateY(0); }} 40% {{ transform: translateY(-22px); }} 60% {{ transform: translateY(-22px); }} }}
@keyframes cheerL {{ from {{ transform: rotate(-8deg); }} to {{ transform: rotate(10deg); }} }}
@keyframes cheerR {{ from {{ transform: rotate(8deg); }} to {{ transform: rotate(-10deg); }} }}
@keyframes dot {{ 0%,100% {{ opacity:.15; transform: translateY(0); }} 40% {{ opacity:1; transform: translateY(-5px); }} }}
@keyframes drop {{ 0% {{ transform: translateY(-6px); opacity:0; }} 20% {{ opacity:1; }} 100% {{ transform: translateY(16px); opacity:0; }} }}
@keyframes shiver {{ from {{ transform: rotate(-1.2deg); }} to {{ transform: rotate(1.2deg); }} }}
@keyframes swipe {{ 0% {{ stroke-dashoffset: 60; }} 45%,80% {{ stroke-dashoffset: 0; }} 100% {{ stroke-dashoffset: -60; }} }}
@keyframes look {{ 0%,40%,100% {{ transform: translate(0,0); }} 50%,90% {{ transform: translate(4px,-3px); }} }}
@keyframes fall {{ from {{ transform: translateY(-30px) rotate(0); }} to {{ transform: translateY(260px) rotate(320deg); }} }}
"""


def sparkle(x, y, s, color, cls):
    p = (f"M{x},{y - s} Q{x + s * .18},{y - s * .18} {x + s},{y} Q{x + s * .18},{y + s * .18} {x},{y + s} "
         f"Q{x - s * .18},{y + s * .18} {x - s},{y} Q{x - s * .18},{y - s * .18} {x},{y - s} Z")
    return f'<path class="{cls}" d="{p}" fill="{color}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'


def body(mouth: str, brows: str = "", eyes_extra: str = "", lines_hl: bool = True) -> str:
    """The sheet: outline, folded corner, face, resume lines, legs."""
    hl = (f'<path class="stroke" d="M92 172 H150" stroke="{MARKER}" stroke-width="11" stroke-linecap="round" '
          'opacity=".95"/>' if lines_hl else "")
    return f"""
  <g>
    <!-- legs -->
    <path class="ink" d="M100 206 V228" fill="none"/>
    <path class="ink" d="M140 206 V228" fill="none"/>
    <ellipse cx="96" cy="232" rx="13" ry="8" fill="{SHOE}" class="ink"/>
    <ellipse cx="144" cy="232" rx="13" ry="8" fill="{SHOE}" class="ink"/>
    <!-- sheet -->
    <path class="ink" d="M68 40 H150 L176 66 V200 Q176 210 166 210 H74 Q64 210 64 200 V50 Q64 40 74 40 Z" fill="{PAPER}"/>
    <path class="ink" d="M150 40 V60 Q150 66 156 66 H176" fill="#EEF1F8"/>
    <!-- resume lines -->
    {hl}
    <path d="M92 172 H150" stroke="{LINE}" stroke-width="5" stroke-linecap="round"/>
    <path d="M92 188 H140" stroke="{LINE}" stroke-width="5" stroke-linecap="round"/>
    <path d="M92 156 H128" stroke="{LINE}" stroke-width="5" stroke-linecap="round"/>
    <!-- face -->
    <ellipse cx="91" cy="120" rx="9" ry="6" fill="{CHEEK}" opacity=".85"/>
    <ellipse cx="149" cy="120" rx="9" ry="6" fill="{CHEEK}" opacity=".85"/>
    <g class="eyes">
      <circle cx="102" cy="98" r="13" fill="{PAPER}" class="ink" stroke-width="4"/>
      <circle cx="138" cy="98" r="13" fill="{PAPER}" class="ink" stroke-width="4"/>
      <g class="look">
        <circle cx="104" cy="100" r="6.5" fill="{INK}"/><circle cx="140" cy="100" r="6.5" fill="{INK}"/>
        <circle cx="106.5" cy="97" r="2.2" fill="{PAPER}"/><circle cx="142.5" cy="97" r="2.2" fill="{PAPER}"/>
      </g>
      {eyes_extra}
    </g>
    {brows}
    {mouth}
  </g>"""


SMILE = f'<path class="thin" d="M108 122 Q120 134 132 122"/>'
BIG_SMILE = f'<path class="ink" d="M104 119 Q120 142 136 119 Z" fill="{SHOE}" stroke-width="4"/>'
OPEN_O = f'<ellipse cx="120" cy="126" rx="6" ry="7" fill="{INK}"/>'
WOBBLE = f'<path class="thin" d="M106 128 Q111 122 116 128 T126 128 T136 126"/>'
FLAT = f'<path class="thin" d="M110 126 H130"/>'

HIGHLIGHTER = (
    f'<g transform="rotate(-35 196 112)">'
    f'<rect x="188" y="78" width="16" height="44" rx="4" fill="{MARKER}" class="ink" stroke-width="4"/>'
    f'<rect x="188" y="70" width="16" height="12" rx="3" fill="{INK}"/>'
    f'<path d="M190 122 L196 132 L202 122 Z" fill="{INK}"/></g>'
)


def arms(left: str, right: str, right_cls: str = "", left_cls: str = "", hand_extra_right: str = "") -> str:
    return (
        f'<g class="v {left_cls}"><path class="ink" d="{left}" fill="none"/></g>'
        f'<g class="v {right_cls}"><path class="ink" d="{right}" fill="none"/>{hand_extra_right}</g>'
    )


def svg(inner: str, label: str, extra_css: str = "", w: int = 240, h: int = 260) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="{label}">'
        f"<title>{label}</title><style>{BASE_CSS}{extra_css}</style>{inner}</svg>"
    )


def shadow() -> str:
    return f'<ellipse class="shadow" cx="120" cy="246" rx="62" ry="8" fill="{INK}" opacity=".18"/>'


def hand(x, y) -> str:
    return f'<circle cx="{x}" cy="{y}" r="9" fill="{PAPER}" class="ink" stroke-width="4"/>'


def pose_wave():
    inner = (
        shadow()
        + '<g class="bob">'
        + arms("M64 136 Q44 150 46 176", "M176 132 Q200 118 206 92", right_cls="wave",
               hand_extra_right=hand(206, 90))
        + hand(46, 178)
        + body(SMILE)
        + "</g>"
        + sparkle(30, 60, 12, MARKER, "tw") + sparkle(214, 196, 9, MINT, "tw2") + sparkle(24, 210, 7, SKY, "tw3")
    )
    return svg(inner, "Scout, the resume mascot, waving hello")


def pose_highlight():
    """Hero pose: holding a highlighter up, about to mark the page."""
    inner = (
        shadow()
        + '<g class="bob">'
        + arms("M64 136 Q44 150 46 176", "M176 132 Q196 122 196 108", right_cls="wave")
        + hand(46, 178)
        + body(BIG_SMILE)
        + f'<g class="v wave">{HIGHLIGHTER}{hand(196, 110)}</g>'
        + "</g>"
        + sparkle(28, 58, 12, MARKER, "tw") + sparkle(222, 40, 9, MINT, "tw2") + sparkle(20, 200, 8, GRAPE, "tw3")
    )
    return svg(inner, "Scout, the resume mascot, holding a highlighter")


def pose_think():
    dots = (
        f'<circle class="dot1" cx="190" cy="48" r="6" fill="{INK}"/>'
        f'<circle class="dot2" cx="208" cy="40" r="6" fill="{INK}"/>'
        f'<circle class="dot3" cx="226" cy="32" r="6" fill="{INK}"/>'
    )
    brows = f'<path class="thin" d="M92 80 Q100 74 110 78"/><path class="thin" d="M130 76 Q140 72 148 78"/>'
    inner = (
        shadow()
        + '<g class="bob">'
        + arms("M64 136 Q44 150 46 176", "M176 150 Q176 150 176 150")
        + hand(46, 178)
        + body(FLAT, brows)
        + f'<path class="ink" d="M176 156 Q158 158 136 142" fill="none"/>' + hand(134, 140)
        + "</g>"
        + dots
    )
    return svg(inner, "Scout is reading your resume")


def pose_cheer():
    conf = ""
    for i, (x, c, d) in enumerate([(20, MARKER, 0), (60, MINT, .3), (110, SHOE, .7), (170, SKY, .2),
                                   (210, GRAPE, .5), (140, MARKER, 1.0), (40, SHOE, 1.2), (190, MINT, .9)]):
        conf += (f'<rect class="conf" style="animation-delay:{d}s" x="{x}" y="0" width="9" height="14" rx="2" '
                 f'fill="{c}" stroke="{INK}" stroke-width="2"/>')
    inner = (
        conf + shadow()
        + '<g class="jump">'
        + arms("M64 132 Q40 110 36 82", "M176 132 Q200 110 204 82", right_cls="cheerR", left_cls="cheerL")
        + f'<g class="v cheerL">{hand(36, 80)}</g><g class="v cheerR">{hand(204, 80)}</g>'
        + body(BIG_SMILE)
        + "</g>"
        + sparkle(24, 150, 10, MARKER, "tw") + sparkle(218, 160, 10, MARKER, "tw2")
    )
    return svg(inner, "Scout is celebrating a great score")


def pose_okay():
    thumb = (f'<g><rect x="199" y="90" width="10" height="20" rx="5" fill="{PAPER}" class="ink" stroke-width="3.5"/>'
             f'<rect x="192" y="104" width="22" height="20" rx="8" fill="{PAPER}" class="ink" stroke-width="4"/></g>')
    inner = (
        shadow()
        + '<g class="bob">'
        + arms("M64 136 Q44 150 46 176", "M176 132 Q192 128 200 120")
        + hand(46, 178) + thumb
        + body(SMILE)
        + "</g>"
        + sparkle(30, 56, 10, MARKER, "tw")
    )
    return svg(inner, "Scout gives a thumbs up")


def pose_worried():
    brows = f'<path class="thin" d="M92 84 Q100 78 112 82"/><path class="thin" d="M128 82 Q140 78 148 84"/>'
    drop = (f'<path class="drop" d="M168 70 Q174 82 168 88 Q162 82 168 70 Z" fill="{SKY}" '
            f'stroke="{INK}" stroke-width="2.5"/>')
    inner = (
        shadow()
        + '<g class="shiver">'
        + body(WOBBLE, brows, lines_hl=False)
        + f'<path class="ink" d="M64 150 Q54 140 80 128" fill="none"/><path class="ink" d="M176 150 Q186 140 160 128" fill="none"/>'
        + hand(82, 126) + hand(158, 126)
        + drop
        + "</g>"
    )
    return svg(inner, "Scout looks worried but ready to help")


def pose_search():
    """Empty states: looking through a magnifying glass."""
    glass = (f'<g class="v wave"><path d="M194 106 L180 124" stroke="{INK}" stroke-width="9" stroke-linecap="round"/>'
             f'<circle cx="204" cy="88" r="19" fill="#E6F2FF" class="ink" stroke-width="5"/>'
             f'<path d="M195 81 Q200 74 209 75" stroke="{PAPER}" stroke-width="4" fill="none" stroke-linecap="round"/></g>')
    inner = (
        shadow()
        + '<g class="bob">'
        + arms("M64 136 Q44 150 46 176", "M176 132 Q184 130 180 126")
        + hand(46, 178)
        + body(OPEN_O)
        + glass + hand(179, 126)
        + "</g>"
        + sparkle(24, 70, 9, MINT, "tw")
    )
    return svg(inner, "Scout is looking for something")


# --------------------------------------------------------------------------
# Doodles for the Toon theme
# --------------------------------------------------------------------------

def doodle_star():
    pts = []
    import math
    for i in range(10):
        r = 34 if i % 2 == 0 else 15
        a = math.pi / 2 + i * math.pi / 5
        pts.append(f"{50 + r * math.cos(a):.1f},{50 - r * math.sin(a):.1f}")
    return svg(
        f'<g class="tw"><polygon points="{" ".join(pts)}" fill="{MARKER}" stroke="{INK}" stroke-width="4" '
        'stroke-linejoin="round"/></g>', "", w=100, h=100)


def doodle_plane():
    return svg(
        '<g class="bob">'
        f'<path d="M10 52 L92 14 L66 88 L48 62 Z" fill="{PAPER}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
        f'<path d="M48 62 L92 14" stroke="{INK}" stroke-width="3.5" fill="none"/>'
        f'<path d="M48 62 L52 80 L60 70" fill="#E3E8F5" stroke="{INK}" stroke-width="3.5" stroke-linejoin="round"/>'
        "</g>", "", w=100, h=100)


def doodle_squiggle():
    return svg(
        f'<path class="stroke" d="M8 40 Q22 10 36 40 T64 40 T92 40" stroke="{SHOE}" stroke-width="7" '
        'fill="none" stroke-linecap="round" style="stroke-dasharray:120"/>', "", w=100, h=60)


def doodle_burst():
    """Starburst used behind the score in the Toon theme."""
    import math
    pts = []
    for i in range(32):
        r = 118 if i % 2 == 0 else 98
        a = i * math.pi / 16
        pts.append(f"{125 + r * math.cos(a):.1f},{125 + r * math.sin(a):.1f}")
    css = ("@media (prefers-reduced-motion: no-preference){.spin{animation:spin 24s linear infinite;"
           "transform-origin:125px 125px}} @keyframes spin{to{transform:rotate(360deg)}}")
    return svg(
        f'<g class="spin"><polygon points="{" ".join(pts)}" fill="{MARKER}" stroke="{INK}" stroke-width="5" '
        'stroke-linejoin="round"/></g>', "", extra_css=css, w=250, h=250)




# --------------------------------------------------------------------------
# Clarity theme: logo, banner illustration, resource icons
# --------------------------------------------------------------------------

BLUE = "#2563EB"
BLUE_D = "#1E40AF"
BLUE_L = "#DBEAFE"
NAVY = "#0F1B3D"


def logo_robot():
    """Original robot-head mark for the app."""
    return svg(
        f'<g class="bob">'
        f'<path d="M50 14 V24" stroke="{BLUE}" stroke-width="5" stroke-linecap="round"/>'
        f'<circle cx="50" cy="11" r="6" fill="{MARKER}" stroke="{BLUE}" stroke-width="3"/>'
        f'<rect x="10" y="40" width="8" height="22" rx="4" fill="{BLUE_D}"/>'
        f'<rect x="82" y="40" width="8" height="22" rx="4" fill="{BLUE_D}"/>'
        f'<rect x="16" y="24" width="68" height="56" rx="18" fill="{BLUE}"/>'
        f'<rect x="24" y="34" width="52" height="34" rx="12" fill="#EFF6FF"/>'
        f'<g class="eyes"><circle cx="40" cy="50" r="6" fill="{NAVY}"/><circle cx="60" cy="50" r="6" fill="{NAVY}"/>'
        f'<circle cx="42" cy="48" r="2" fill="#fff"/><circle cx="62" cy="48" r="2" fill="#fff"/></g>'
        f'<path d="M42 60 Q50 65 58 60" stroke="{NAVY}" stroke-width="3" fill="none" stroke-linecap="round"/>'
        f'<rect x="34" y="84" width="32" height="8" rx="4" fill="{BLUE_D}"/>'
        f'</g>',
        "AI Resume ATS Scorer", extra_css=".eyes{transform-origin:50px 50px}", w=100, h=100)


def banner_art():
    """Greeting-banner illustration: a resume card, a target and an arrow."""
    css = (
        "@media (prefers-reduced-motion: no-preference){"
        ".doc{animation:bob 4s ease-in-out infinite}"
        ".arrow{animation:hit 3.2s cubic-bezier(.3,.7,.2,1) infinite}"
        ".ring{animation:pulse 3.2s ease-out infinite;transform-origin:118px 112px}}"
        "@keyframes hit{0%{transform:translate(40px,-34px);opacity:0}25%{opacity:1}40%,100%{transform:translate(0,0);opacity:1}}"
        "@keyframes pulse{0%,38%{transform:scale(1);opacity:0}42%{opacity:.6}70%,100%{transform:scale(1.35);opacity:0}}"
    )
    doc = (
        f'<g class="doc">'
        f'<rect x="168" y="22" width="112" height="140" rx="14" fill="#fff" stroke="{BLUE_L}" stroke-width="3"/>'
        f'<circle cx="196" cy="54" r="14" fill="{BLUE_L}"/><circle cx="196" cy="50" r="5" fill="{BLUE}"/>'
        f'<path d="M187 63 Q196 55 205 63" fill="{BLUE}"/>'
        f'<rect x="218" y="44" width="46" height="7" rx="3.5" fill="{BLUE}"/>'
        f'<rect x="218" y="58" width="32" height="6" rx="3" fill="#BFD3F8"/>'
        f'<rect x="184" y="84" width="80" height="6" rx="3" fill="#D6E2F8"/>'
        f'<rect x="184" y="98" width="68" height="6" rx="3" fill="#D6E2F8"/>'
        f'<rect x="184" y="112" width="74" height="6" rx="3" fill="{MARKER}" opacity=".9"/>'
        f'<rect x="184" y="126" width="56" height="6" rx="3" fill="#D6E2F8"/>'
        f'<circle cx="270" cy="150" r="15" fill="#22C55E"/>'
        f'<path d="M263 150 L268 155 L278 144" stroke="#fff" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        f'</g>'
    )
    target = (
        f'<circle cx="118" cy="112" r="50" fill="{BLUE}"/>'
        f'<circle cx="118" cy="112" r="37" fill="#fff"/>'
        f'<circle cx="118" cy="112" r="25" fill="{BLUE}"/>'
        f'<circle cx="118" cy="112" r="12" fill="#fff"/>'
        f'<circle cx="118" cy="112" r="5" fill="{BLUE_D}"/>'
        f'<circle class="ring" cx="118" cy="112" r="50" fill="none" stroke="{BLUE}" stroke-width="3"/>'
    )
    arrow = (
        f'<g class="arrow"><path d="M118 112 L164 66" stroke="{NAVY}" stroke-width="6" stroke-linecap="round"/>'
        f'<path d="M160 58 L176 54 L172 70 Z" fill="{MARKER}" stroke="{NAVY}" stroke-width="3" stroke-linejoin="round"/>'
        f'<path d="M156 62 L172 58" stroke="{NAVY}" stroke-width="3" stroke-linecap="round"/></g>'
    )
    blobs = (
        f'<path d="M30 150 Q20 90 70 70 Q120 40 150 80 Q190 130 150 165 Q90 200 30 150 Z" fill="#C7DBFF" opacity=".55"/>'
    )
    sparkles = sparkle(58, 40, 9, MARKER, "tw") + sparkle(296, 18, 7, BLUE, "tw2") + sparkle(40, 120, 6, "#93B4F5", "tw3")
    return svg(blobs + target + doc + arrow + sparkles, "Resume and target illustration", extra_css=css, w=320, h=180)


ICON_PATHS = {
    "tips": ('#FDE68A', '<path d="M50 20 a20 20 0 0 1 12 36 v8 h-24 v-8 a20 20 0 0 1 12-36z" fill="#FBBF24" stroke="#92400E" stroke-width="3.5" stroke-linejoin="round"/><path d="M41 72 h18 M43 80 h14" stroke="#92400E" stroke-width="4" stroke-linecap="round"/>'),
    "guide": ('#BFDBFE', '<path d="M32 18 h26 l14 14 v50 a4 4 0 0 1-4 4 h-36 a4 4 0 0 1-4-4 v-60 a4 4 0 0 1 4-4z" fill="#fff" stroke="#1E40AF" stroke-width="3.5" stroke-linejoin="round"/><path d="M58 18 v14 h14" fill="none" stroke="#1E40AF" stroke-width="3.5" stroke-linejoin="round"/><path d="M38 48 h24 M38 58 h24 M38 68 h16" stroke="#2563EB" stroke-width="4" stroke-linecap="round"/>'),
    "interview": ('#BBF7D0', '<circle cx="38" cy="38" r="11" fill="#16A34A"/><circle cx="64" cy="40" r="9" fill="#22C55E"/><path d="M18 76 a20 20 0 0 1 40 0z" fill="#16A34A"/><path d="M50 76 a16 16 0 0 1 32 0z" fill="#22C55E"/>'),
    "career": ('#FECACA', '<path d="M50 14 C66 26 70 46 62 64 H38 C30 46 34 26 50 14z" fill="#fff" stroke="#B91C1C" stroke-width="3.5" stroke-linejoin="round"/><circle cx="50" cy="38" r="7" fill="#EF4444"/><path d="M38 56 L26 70 L40 68 M62 56 L74 70 L60 68" fill="#EF4444" stroke="#B91C1C" stroke-width="3" stroke-linejoin="round"/><path d="M44 70 Q50 86 56 70" fill="#F59E0B"/>'),
    "templates": ('#A7F3D0', '<rect x="26" y="16" width="48" height="66" rx="6" fill="#fff" stroke="#047857" stroke-width="3.5"/><rect x="34" y="26" width="32" height="10" rx="3" fill="#10B981"/><path d="M34 46 h32 M34 56 h32 M34 66 h20" stroke="#047857" stroke-width="4" stroke-linecap="round"/>'),
    "learning": ('#DDD6FE', '<path d="M50 24 L86 40 L50 56 L14 40z" fill="#4C1D95"/><path d="M28 47 v16 c0 8 44 8 44 0 v-16 L50 57z" fill="#6D28D9"/><path d="M82 42 v20" stroke="#4C1D95" stroke-width="3.5" stroke-linecap="round"/><circle cx="82" cy="65" r="4" fill="#F59E0B"/>'),
}


def resource_icon(name):
    bg, inner = ICON_PATHS[name]
    return svg(f'<rect x="0" y="0" width="100" height="100" rx="26" fill="{bg}"/>{inner}', "", w=100, h=100)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files = {
        "scout-wave.svg": pose_wave(),
        "scout-highlight.svg": pose_highlight(),
        "scout-think.svg": pose_think(),
        "scout-cheer.svg": pose_cheer(),
        "scout-okay.svg": pose_okay(),
        "scout-worried.svg": pose_worried(),
        "scout-search.svg": pose_search(),
        "doodle-star.svg": doodle_star(),
        "doodle-plane.svg": doodle_plane(),
        "doodle-squiggle.svg": doodle_squiggle(),
        "burst.svg": doodle_burst(),
        "logo-robot.svg": logo_robot(),
        "banner.svg": banner_art(),
    }
    for icon in ICON_PATHS:
        files[f"icon-{icon}.svg"] = resource_icon(icon)
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8")
        print("wrote", name)


if __name__ == "__main__":
    main()
