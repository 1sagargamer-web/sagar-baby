"""Background themes for the reels. Each theme = sky css + three SVG layers (back, mid, front).
make_reel.py picks one per reel: `"scene": "night"` in script.json, otherwise it rotates by the title so
consecutive videos look different.  Themes: park, temple, night, city, room, beach.
"""

CLOUDS_WHITE = """<svg class="bg-svg" id="clouds" style="top:120px;height:420px" viewBox="0 0 1080 420"><g fill="#ffffff" opacity="0.95">
<ellipse cx="190" cy="120" rx="120" ry="48"/><ellipse cx="260" cy="95" rx="80" ry="55"/><ellipse cx="140" cy="100" rx="60" ry="40"/>
<ellipse cx="830" cy="230" rx="140" ry="52"/><ellipse cx="900" cy="200" rx="85" ry="58"/><ellipse cx="770" cy="210" rx="65" ry="42"/></g></svg>"""


def hills(c1, c2):
    return f"""<svg class="bg-svg" style="top:1080px;height:840px" viewBox="0 0 1080 840">
<path d="M0 220 C180 120 340 140 520 210 C700 120 900 110 1080 200 L1080 840 L0 840 Z" fill="{c1}"/>
<path d="M0 330 C240 270 520 290 1080 320 L1080 840 L0 840 Z" fill="{c2}"/></svg>"""


def bushes(fill, stroke):
    return f"""<svg class="bg-svg" style="top:1560px;height:360px" viewBox="0 0 1080 360">
<g fill="{fill}" stroke="{stroke}" stroke-width="6"><circle cx="40" cy="150" r="110"/><circle cx="210" cy="190" r="120"/>
<circle cx="400" cy="170" r="105"/><circle cx="600" cy="200" r="125"/><circle cx="800" cy="165" r="110"/><circle cx="1000" cy="185" r="125"/></g>
<rect x="0" y="230" width="1080" height="130" fill="{fill}"/></svg>"""


def stars(n=38):
    import random
    r = random.Random(5)
    pts = "".join(f'<circle cx="{r.randint(20,1060)}" cy="{r.randint(10,400)}" r="{r.choice([2,3,4])}"/>' for _ in range(n))
    return f'<svg class="bg-svg" id="clouds" style="top:100px;height:430px" viewBox="0 0 1080 430"><g fill="#fff8d6">{pts}</g></svg>'


THEMES = {
    "park": dict(
        sky="linear-gradient(#58bff2 0%, #a9e3ff 58%, #d8f3ff 70%)",
        back=CLOUDS_WHITE,
        mid=hills("#7fd36b", "#5cbf55"),
        front=bushes("#3fa34a", "#2a7a35"),
    ),
    "temple": dict(
        sky="linear-gradient(#ff9d4d 0%, #ffd08a 45%, #fff0c8 72%)",
        back="""<svg class="bg-svg" id="clouds" style="top:90px;height:700px" viewBox="0 0 1080 700">
<circle cx="540" cy="360" r="170" fill="#fff3c4" opacity="0.8"/>
<g fill="#c9772e"><path d="M300 640 L300 360 Q300 270 540 150 Q780 270 780 360 L780 640 Z"/>
<rect x="470" y="70" width="14" height="90"/><path d="M484 78 L560 98 L484 118 Z" fill="#e2453c"/></g>
<g fill="#a85e22"><rect x="340" y="420" width="60" height="220"/><rect x="680" y="420" width="60" height="220"/>
<path d="M470 640 L470 520 Q540 450 610 520 L610 640 Z" fill="#7a3f12"/></g></svg>""",
        mid="""<svg class="bg-svg" style="top:1180px;height:740px" viewBox="0 0 1080 740">
<rect y="0" width="1080" height="740" fill="#d9b88a"/><path d="M0 0 L1080 0 L1080 90 L0 90 Z" fill="#c79d6b"/>
<g stroke="#b08550" stroke-width="5"><path d="M0 200 H1080 M0 320 H1080 M0 460 H1080"/><path d="M180 90 V740 M540 90 V740 M900 90 V740"/></g></svg>""",
        front="""<svg class="bg-svg" style="top:1560px;height:360px" viewBox="0 0 1080 360"><rect y="170" width="1080" height="190" fill="#b88b58"/>
<g fill="#ffb02e"><ellipse cx="90" cy="150" rx="46" ry="22"/><ellipse cx="990" cy="150" rx="46" ry="22"/></g>
<g fill="#ffe27a"><path d="M90 130 C70 100 90 80 90 60 C110 80 110 100 90 130Z"/><path d="M990 130 C970 100 990 80 990 60 C1010 80 1010 100 990 130Z"/></g></svg>""",
    ),
    "night": dict(
        sky="linear-gradient(#0b1030 0%, #1b2559 55%, #3b3f86 80%)",
        back=stars() + """<svg class="bg-svg" style="top:150px;height:300px" viewBox="0 0 1080 300"><circle cx="840" cy="110" r="70" fill="#fff6cf"/>
<circle cx="812" cy="92" r="70" fill="#1b2559"/></svg>""",
        mid=hills("#1f3d4f", "#183142"),
        front=bushes("#10241f", "#0a1614"),
    ),
    "city": dict(
        sky="linear-gradient(#ff8fb1 0%, #ffc4a3 45%, #ffe9c6 75%)",
        back=CLOUDS_WHITE.replace("#ffffff", "#ffd6e0"),
        mid="""<svg class="bg-svg" style="top:900px;height:1020px" viewBox="0 0 1080 1020">
<g fill="#5b4a8a"><rect x="30" y="200" width="170" height="820"/><rect x="230" y="90" width="150" height="930"/><rect x="410" y="260" width="190" height="760"/>
<rect x="630" y="140" width="160" height="880"/><rect x="820" y="230" width="230" height="790"/></g>
<g fill="#ffe27a" opacity="0.9"><rect x="60" y="250" width="26" height="34"/><rect x="120" y="330" width="26" height="34"/><rect x="260" y="150" width="26" height="34"/>
<rect x="320" y="260" width="26" height="34"/><rect x="450" y="320" width="26" height="34"/><rect x="520" y="420" width="26" height="34"/>
<rect x="660" y="210" width="26" height="34"/><rect x="720" y="330" width="26" height="34"/><rect x="860" y="300" width="26" height="34"/><rect x="960" y="420" width="26" height="34"/></g></svg>""",
        front="""<svg class="bg-svg" style="top:1560px;height:360px" viewBox="0 0 1080 360"><rect y="150" width="1080" height="210" fill="#43405a"/>
<rect y="150" width="1080" height="24" fill="#8c88aa"/><g fill="#ffe27a"><rect x="60" y="250" width="120" height="10"/><rect x="330" y="250" width="120" height="10"/>
<rect x="600" y="250" width="120" height="10"/><rect x="870" y="250" width="120" height="10"/></g></svg>""",
    ),
    "room": dict(
        sky="linear-gradient(#ffd9e8 0%, #ffe9f2 60%, #fff4e8 100%)",
        back="""<svg class="bg-svg" id="clouds" style="top:120px;height:560px" viewBox="0 0 1080 560">
<rect x="360" y="40" width="360" height="300" rx="14" fill="#8fd6ff" stroke="#fff" stroke-width="18"/><path d="M540 40 V340 M360 190 H720" stroke="#fff" stroke-width="12"/>
<ellipse cx="450" cy="120" rx="60" ry="26" fill="#fff"/><rect x="60" y="120" width="150" height="190" rx="8" fill="#ffb3c7"/><circle cx="135" cy="200" r="42" fill="#fff"/>
<rect x="830" y="90" width="180" height="120" rx="8" fill="#c8b6ff"/></svg>""",
        mid="""<svg class="bg-svg" style="top:1150px;height:770px" viewBox="0 0 1080 770"><rect width="1080" height="770" fill="#e9c9a5"/>
<rect width="1080" height="40" fill="#d6b18a"/><g stroke="#d6b18a" stroke-width="4"><path d="M0 160 H1080 M0 300 H1080 M0 460 H1080 M0 640 H1080"/></g></svg>""",
        front="""<svg class="bg-svg" style="top:1580px;height:340px" viewBox="0 0 1080 340"><rect y="150" width="1080" height="190" fill="#e9c9a5"/>
<ellipse cx="540" cy="190" rx="520" ry="70" fill="#ff9bb5"/><g fill="#7ec8a4"><rect x="40" y="70" width="60" height="110" rx="12"/><path d="M70 70 C40 20 100 20 70 70Z"/></g></svg>""",
    ),
    "beach": dict(
        sky="linear-gradient(#35c4ff 0%, #8fe3ff 55%, #d8f7ff 74%)",
        back=CLOUDS_WHITE + """<svg class="bg-svg" style="top:140px;height:360px" viewBox="0 0 1080 360"><circle cx="900" cy="130" r="80" fill="#ffe27a"/></svg>""",
        mid="""<svg class="bg-svg" style="top:1100px;height:820px" viewBox="0 0 1080 820"><rect y="0" width="1080" height="260" fill="#2aa6d9"/>
<path d="M0 60 Q90 30 180 60 T360 60 T540 60 T720 60 T900 60 T1080 60 V120 H0Z" fill="#7ad7f5"/>
<path d="M0 240 Q270 200 540 240 T1080 230 V820 H0Z" fill="#f2d49b"/></svg>""",
        front="""<svg class="bg-svg" style="top:1500px;height:420px" viewBox="0 0 1080 420"><rect y="220" width="1080" height="200" fill="#e8c585"/>
<g stroke="#3b7a2a" stroke-width="14" fill="none"><path d="M960 400 Q990 250 940 100"/></g>
<g fill="#3fa34a"><path d="M940 100 Q860 50 800 110 Q880 100 940 100Z"/><path d="M940 100 Q1020 40 1070 100 Q1000 90 940 100Z"/><path d="M940 100 Q930 20 880 -10 Q920 40 940 100Z"/></g></svg>""",
    ),
}

def tree_kadamba(x, scale=1.0):
    return f"""<g transform="translate({x},0) scale({scale})"><rect x="-26" y="260" width="52" height="330" fill="#6b4423"/>
<g fill="#2f8f3a"><circle cx="0" cy="200" r="140"/><circle cx="-120" cy="260" r="100"/><circle cx="120" cy="260" r="100"/><circle cx="-40" cy="120" r="90"/><circle cx="70" cy="130" r="80"/></g>
<g fill="#ffd84d"><circle cx="-70" cy="190" r="12"/><circle cx="40" cy="230" r="12"/><circle cx="100" cy="170" r="12"/><circle cx="-10" cy="150" r="12"/><circle cx="-130" cy="270" r="12"/></g></g>"""


THEMES["vrindavan"] = dict(
    sky="linear-gradient(#8fe0ff 0%, #c9f3d8 55%, #fff6c8 78%)",
    back="""<svg class="bg-svg" id="clouds" style="top:60px;height:760px" viewBox="0 0 1080 760">
<g fill="#ffffff" opacity="0.9"><ellipse cx="820" cy="120" rx="120" ry="44"/><ellipse cx="880" cy="96" rx="70" ry="46"/><ellipse cx="200" cy="170" rx="100" ry="38"/></g>"""
    + tree_kadamba(230, 0.95) + tree_kadamba(900, 0.7) + """</svg>""",
    mid=hills("#8ed36b", "#62bd55"),
    front="""<svg class="bg-svg" style="top:1560px;height:360px" viewBox="0 0 1080 360"><rect y="210" width="1080" height="150" fill="#4aa84a"/>
<g stroke="#2d7a35" stroke-width="5" fill="none"><path d="M60 210 V150 M120 210 V120 M300 210 V140 M700 210 V130 M880 210 V150 M1000 210 V120"/></g>
<g fill="#ff7eb6"><circle cx="60" cy="146" r="16"/><circle cx="120" cy="116" r="16"/><circle cx="300" cy="136" r="16"/><circle cx="700" cy="126" r="16"/><circle cx="880" cy="146" r="16"/><circle cx="1000" cy="116" r="16"/></g>
<g fill="#ffffff"><circle cx="60" cy="146" r="6"/><circle cx="120" cy="116" r="6"/><circle cx="700" cy="126" r="6"/><circle cx="1000" cy="116" r="6"/></g></svg>""",
)

THEMES["gokul"] = dict(
    sky="linear-gradient(#ffd27a 0%, #ffe9b0 50%, #fff6dc 78%)",
    back="""<svg class="bg-svg" id="clouds" style="top:120px;height:760px" viewBox="0 0 1080 760">
<g fill="#fff" opacity="0.8"><ellipse cx="880" cy="90" rx="110" ry="40"/><ellipse cx="170" cy="130" rx="90" ry="34"/></g>
<g><rect x="60" y="360" width="260" height="190" fill="#d9a46b"/><polygon points="30,360 190,230 350,360" fill="#b9791f"/><rect x="150" y="440" width="80" height="110" fill="#6b4423"/>
<rect x="640" y="380" width="300" height="170" fill="#d9a46b"/><polygon points="610,380 790,250 970,380" fill="#c98a2e"/><rect x="760" y="450" width="70" height="100" fill="#6b4423"/></g></svg>""",
    mid="""<svg class="bg-svg" style="top:1200px;height:720px" viewBox="0 0 1080 720"><rect width="1080" height="720" fill="#d8b27a"/>
<path d="M0 0 C300 40 700 40 1080 0 V80 H0Z" fill="#c9a164"/>
<g fill="#ffffff" stroke="#3b2a1a" stroke-width="5"><ellipse cx="520" cy="190" rx="95" ry="48"/><circle cx="440" cy="168" r="30"/><rect x="450" y="215" width="14" height="50"/><rect x="590" y="215" width="14" height="50"/></g>
<g fill="#3b2a1a"><circle cx="470" cy="190" r="14"/><circle cx="560" cy="170" r="12"/><circle cx="430" cy="160" r="4"/></g></svg>""",
    front="""<svg class="bg-svg" style="top:1560px;height:360px" viewBox="0 0 1080 360"><rect y="200" width="1080" height="160" fill="#c49a5e"/>
<g stroke="#5a3a1a" stroke-width="6"><path d="M70 90 C10 120 10 200 70 230 C130 200 130 120 70 90Z" fill="#c8572b"/><path d="M990 90 C930 120 930 200 990 230 C1050 200 1050 120 990 90Z" fill="#c8572b"/></g>
<g fill="#fff4cf"><ellipse cx="70" cy="100" rx="42" ry="14"/><ellipse cx="990" cy="100" rx="42" ry="14"/></g></svg>""",
)

THEMES["yamuna"] = dict(
    sky="linear-gradient(#ff9d6b 0%, #ffcf94 48%, #fff0c8 74%)",
    back="""<svg class="bg-svg" id="clouds" style="top:100px;height:760px" viewBox="0 0 1080 760">
<circle cx="540" cy="360" r="130" fill="#fff3c4" opacity="0.9"/>
<g fill="#ffb577" opacity="0.8"><ellipse cx="200" cy="130" rx="120" ry="34"/><ellipse cx="860" cy="200" rx="130" ry="36"/></g>"""
    + tree_kadamba(120, 0.8) + tree_kadamba(980, 0.75).replace("#2f8f3a", "#2a7a36") + """</svg>""",
    mid="""<svg class="bg-svg" style="top:1130px;height:790px" viewBox="0 0 1080 790"><rect width="1080" height="330" fill="#2f9bd6"/>
<path d="M0 40 Q90 10 180 40 T360 40 T540 40 T720 40 T900 40 T1080 40 V90 H0Z" fill="#6ccbf2"/>
<path d="M0 150 Q120 120 240 150 T480 150 T720 150 T960 150 T1200 150 V200 H0Z" fill="#59b9e8" opacity="0.8"/>
<path d="M0 320 H1080 V790 H0Z" fill="#c9a06a"/><path d="M0 320 H1080 V350 H0Z" fill="#a98150"/></svg>""",
    front="""<svg class="bg-svg" style="top:1530px;height:390px" viewBox="0 0 1080 390"><rect y="210" width="1080" height="180" fill="#b88b58"/>
<g fill="#d8a96d" stroke="#8a5f2e" stroke-width="4"><rect x="0" y="150" width="1080" height="60"/><rect x="0" y="210" width="1080" height="40"/></g>
<g fill="#ffb02e"><ellipse cx="120" cy="140" rx="44" ry="20"/><ellipse cx="540" cy="140" rx="44" ry="20"/><ellipse cx="960" cy="140" rx="44" ry="20"/></g>
<g fill="#ffe27a"><path d="M120 122 C100 94 120 74 120 54 C140 74 140 94 120 122Z"/><path d="M540 122 C520 94 540 74 540 54 C560 74 560 94 540 122Z"/><path d="M960 122 C940 94 960 74 960 54 C980 74 980 94 960 122Z"/></g></svg>""",
)

THEMES["govardhan"] = dict(
    sky="linear-gradient(#5cc6ff 0%, #a9e6ff 56%, #e3f7ff 76%)",
    back="""<svg class="bg-svg" id="clouds" style="top:80px;height:1250px" viewBox="0 0 1080 1250">
<g fill="#fff" opacity="0.95"><ellipse cx="190" cy="110" rx="120" ry="44"/><ellipse cx="880" cy="190" rx="130" ry="46"/><ellipse cx="940" cy="160" rx="80" ry="48"/></g>
<path d="M-300 1250 L-300 820 C0 480 300 300 540 250 C780 300 1080 480 1380 820 L1380 1250 Z" fill="#7a8f57"/>
<path d="M-100 1250 L-100 920 C200 640 420 420 560 390 C720 420 900 640 1180 920 L1180 1250 Z" fill="#5f7a3f"/>
<g fill="#2f6b34"><circle cx="330" cy="470" r="34"/><circle cx="420" cy="430" r="30"/><circle cx="660" cy="420" r="32"/><circle cx="760" cy="470" r="36"/><circle cx="540" cy="380" r="28"/></g></svg>""",
    mid=hills("#84cc62", "#5eb74f"),
    front=bushes("#3fa34a", "#2a7a35"),
)

KRISHNA_ORDER = ["vrindavan", "gokul", "yamuna", "govardhan", "temple", "park"]

ORDER = KRISHNA_ORDER


def pick(name, title):
    if name in THEMES:
        return name
    return ORDER[sum(map(ord, title)) % len(ORDER)]
