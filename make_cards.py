"""AI, Simply 팁형 카드 5장(표지·1·2·3단계·마무리)을 밝은 파스텔 디자인으로 만든다.

사용법: python make_cards.py content.json posts/2026-11-22
content.json 형식:
{
  "cover": {"line1": "답장 쓰기 막막할 때", "line2": "이 3단계면 끝나요", "sub": "어떤 AI에서도 바로 쓸 수 있어요"},
  "steps": [{"pill": "받은 글 그대로 붙여넣기", "desc": "설명 (줄바꿈은 \\n)", "ex": "이렇게 써보세요 예시 (줄바꿈 \\n)"}, ... 3개],
  "outro": {"line1": "저장해두고", "line2": "다음 답장에 써보세요", "sub": "팔로우하면 매일 AI 꿀팁 하나씩"}
}
"""
import html, json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:"Noto Sans CJK KR",sans-serif;background:#fff}
.card{width:1080px;height:1350px;position:relative;overflow:hidden;background:#fff;color:#2E2F2B}
.top{position:absolute;left:0;top:0;width:1080px;height:650px;overflow:hidden}
.top svg{position:absolute;left:0;top:0}
.tag{position:absolute;left:60px;top:56px;background:#fff;color:#5E8A2A;font-weight:900;font-size:30px;padding:10px 26px;border-radius:40px;z-index:3}
.pill{position:absolute;left:64px;top:606px;height:88px;padding:0 40px;display:flex;align-items:center;background:#EAF3FC;border:3px solid #A9C8EA;border-radius:50px;color:#3F7FD9;font-weight:900;font-size:44px;z-index:3;box-shadow:0 6px 0 rgba(63,127,217,.08)}
.pill b{color:#9CC45A;margin-right:18px;font-weight:900}
.body{position:absolute;left:80px;right:80px;top:750px}
.desc{font-size:44px;line-height:1.55;font-weight:500;color:#3A3B37}
.try{margin-top:56px;font-size:34px;font-weight:900;color:#3F7FD9}
.ex{margin-top:18px;background:#F3F1EC;border-radius:36px;padding:34px 40px;font-size:42px;font-weight:700;line-height:1.4;color:#2E2F2B}
.logo{position:absolute;left:0;right:0;bottom:92px;text-align:center;font-weight:900;font-size:32px;color:#8FB550;letter-spacing:.5px}
.dots{position:absolute;left:0;right:0;bottom:50px;display:flex;justify-content:center;gap:16px}
.dots i{width:16px;height:16px;border-radius:50%;background:#DEDBD2}
.dots i.on{background:#9CC45A;width:40px;border-radius:10px}
.full .top{height:1350px}
.ctitle{position:absolute;left:0;right:0;text-align:center;font-weight:900;line-height:1.25;z-index:3}
.csub{position:absolute;left:0;right:0;text-align:center;font-weight:700;z-index:3}
"""

ART_COVER = """<svg width="1080" height="1350" viewBox="0 0 1080 1350">
<rect width="1080" height="1350" fill="#F3F1EC"/>
<path d="M-80 760 C-80 500 120 380 300 380 C480 380 640 520 640 760 Z" fill="#F2DE7A"/>
<path d="M520 760 C520 470 700 330 860 330 C1040 330 1180 480 1180 760 Z" fill="#F4BFC3"/>
<path d="M200 760 C200 420 380 250 550 250 C720 250 900 420 900 760 Z" fill="#BFD97E"/>
<rect y="740" width="1080" height="610" fill="#fff"/>
<g transform="translate(360,90)"><rect width="360" height="200" rx="60" fill="#fff"/><path d="M150 195 L185 250 L220 195 Z" fill="#fff"/>
<rect x="60" y="62" width="150" height="22" rx="11" fill="#DEDBD2"/><rect x="60" y="112" width="240" height="22" rx="11" fill="#A9C8EA"/>
<text x="268" y="96" font-size="72" font-weight="900" fill="#F0A0A8" font-family="Noto Sans CJK KR">?</text></g>
<path d="M190 250 l14 38 38 14 -38 14 -14 38 -14 -38 -38 -14 38 -14z" fill="#F5C94A"/>
<path d="M900 170 l10 26 26 10 -26 10 -10 26 -10 -26 -26 -10 26 -10z" fill="#F5C94A"/></svg>"""

ART_STEP = [
"""<svg width="1080" height="650" viewBox="0 0 1080 650">
<rect width="1080" height="650" fill="#F3F1EC"/>
<path d="M-100 650 C-100 420 60 320 220 320 C380 320 520 440 520 650 Z" fill="#F2DE7A"/>
<path d="M620 650 C620 400 780 290 920 290 C1080 290 1200 420 1200 650 Z" fill="#F4BFC3"/>
<path d="M250 650 C250 380 410 250 560 250 C720 250 870 390 870 650 Z" fill="#BFD97E"/>
<g transform="translate(330,110)"><rect width="460" height="150" rx="75" fill="#fff"/><path d="M330 145 L370 205 L400 145 Z" fill="#fff"/>
<rect x="70" y="62" width="250" height="26" rx="13" fill="#A9C8EA"/><rect x="340" y="56" width="6" height="38" rx="3" fill="#3F7FD9"/></g>
<path d="M870 120 l12 32 32 12 -32 12 -12 32 -12 -32 -32 -12 32 -12z" fill="#F5C94A"/></svg>""",
"""<svg width="1080" height="650" viewBox="0 0 1080 650">
<rect width="1080" height="650" fill="#CFE08F"/>
<path d="M-100 650 C-100 470 80 380 240 380 C400 380 540 480 540 650 Z" fill="#BFD97E"/>
<path d="M560 650 C560 450 740 350 900 350 C1060 350 1200 460 1200 650 Z" fill="#DDE9A8"/>
<g transform="translate(250,120)"><rect width="580" height="330" rx="60" fill="#fff"/>
<rect x="60" y="64" width="330" height="24" rx="12" fill="#DEDBD2"/><rect x="60" y="124" width="420" height="24" rx="12" fill="#DEDBD2"/>
<rect x="46" y="196" width="488" height="84" rx="42" fill="#FBE3E5"/><rect x="80" y="226" width="340" height="24" rx="12" fill="#F0A0A8"/></g>
<circle cx="830" cy="140" r="54" fill="#F5C94A"/><rect x="800" y="132" width="60" height="16" rx="8" fill="#fff"/><rect x="822" y="110" width="16" height="60" rx="8" fill="#fff"/></svg>""",
"""<svg width="1080" height="650" viewBox="0 0 1080 650">
<rect width="1080" height="650" fill="#F3F1EC"/>
<path d="M-60 650 C-60 440 120 330 300 330 C480 330 640 450 640 650 Z" fill="#F4BFC3"/>
<path d="M480 650 C480 420 660 300 840 300 C1020 300 1180 430 1180 650 Z" fill="#F2DE7A"/>
<g transform="translate(120,110)"><rect width="400" height="120" rx="60" fill="#fff"/><rect x="56" y="48" width="200" height="24" rx="12" fill="#A9C8EA"/>
<text x="300" y="86" font-size="64" font-weight="900" fill="#3F7FD9" font-family="Noto Sans CJK KR">?</text></g>
<g transform="translate(560,260)"><rect width="400" height="120" rx="60" fill="#8E7868"/><rect x="60" y="48" width="280" height="24" rx="12" fill="#fff" opacity=".9"/></g>
<g transform="translate(120,410)"><rect width="520" height="160" rx="50" fill="#fff"/><rect x="56" y="46" width="300" height="24" rx="12" fill="#BFD97E"/><rect x="56" y="94" width="220" height="24" rx="12" fill="#DEDBD2"/>
<circle cx="440" cy="80" r="42" fill="#9CC45A"/><path d="M420 80 l14 14 28 -30" stroke="#fff" stroke-width="10" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>
<path d="M900 120 l12 32 32 12 -32 12 -12 32 -12 -32 -32 -12 32 -12z" fill="#F5C94A"/></svg>""",
]

ART_OUTRO = """<svg width="1080" height="1350" viewBox="0 0 1080 1350">
<rect width="1080" height="1350" fill="#CFE08F"/>
<path d="M-100 780 C-100 540 100 430 280 430 C460 430 620 560 620 780 Z" fill="#BFD97E"/>
<path d="M500 780 C500 520 700 400 880 400 C1060 400 1200 540 1200 780 Z" fill="#DDE9A8"/>
<rect y="760" width="1080" height="590" fill="#fff"/>
<g transform="translate(410,170)"><path d="M0 40 C0 18 18 0 40 0 H220 C242 0 260 18 260 40 V400 L130 310 L0 400 Z" fill="#fff"/>
<path d="M130 110 l20 52 52 20 -52 20 -20 52 -20 -52 -52 -20 52 -20z" fill="#F5C94A"/></g>
<path d="M240 260 l12 32 32 12 -32 12 -12 32 -12 -32 -32 -12 32 -12z" fill="#fff"/>
<path d="M840 210 l10 26 26 10 -26 10 -10 26 -10 -26 -26 -10 26 -10z" fill="#fff"/></svg>"""


def esc(s):
    return html.escape(s).replace("\n", "<br>")


def dots(i, n=5):
    return "".join('<i class="on"></i>' if j == i else "<i></i>" for j in range(n))


def card(inner, i):
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>'
            f'{inner}<div class="logo">AI, Simply</div><div class="dots">{dots(i)}</div></div></body></html>')


def build(d):
    pages = []
    c = d["cover"]
    pages.append(card(
        f'<div class="card full"><div class="top">{ART_COVER}</div>'
        f'<div class="tag" style="background:#BFD97E;color:#fff">AI 꿀팁</div>'
        f'<div class="ctitle" style="top:830px;font-size:86px;color:#2E2F2B">{esc(c["line1"])}<br>'
        f'<span style="color:#8FB550">{esc(c["line2"])}</span></div>'
        f'<div class="csub" style="top:1090px;font-size:42px;color:#6B6C66">{esc(c["sub"])}</div>', 0))
    for k, s in enumerate(d["steps"][:3]):
        pages.append(card(
            f'<div class="card"><div class="top">{ART_STEP[k]}</div><div class="tag">AI 꿀팁</div>'
            f'<div class="pill"><b>0{k+1}</b>{esc(s["pill"])}</div>'
            f'<div class="body"><div class="desc">{esc(s["desc"])}</div>'
            f'<div class="try">이렇게 써보세요</div><div class="ex">{esc(s["ex"])}</div></div>', k + 1))
    o = d["outro"]
    pages.append(card(
        f'<div class="card full"><div class="top">{ART_OUTRO}</div><div class="tag">AI 꿀팁</div>'
        f'<div class="ctitle" style="top:850px;font-size:88px;color:#2E2F2B">{esc(o["line1"])}<br>'
        f'<span style="color:#8FB550">{esc(o["line2"])}</span></div>'
        f'<div class="csub" style="top:1110px;font-size:42px;color:#6B6C66">{esc(o["sub"])}</div>', 4))
    return pages


def main():
    src, outdir = sys.argv[1], Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    d = json.load(open(src, encoding="utf-8"))
    pages = build(d)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        for i, h in enumerate(pages, 1):
            pg.set_content(h)
            pg.wait_for_timeout(200)
            pg.screenshot(path=str(outdir / f"card_{i}.png"))
        b.close()
    print("카드", len(pages), "장 생성 →", outdir)


if __name__ == "__main__":
    main()
