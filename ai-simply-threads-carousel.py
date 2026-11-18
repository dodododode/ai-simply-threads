import os, sys, time, json
import urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 매일 posts/YYYY-MM-DD/ 폴더의 카드 이미지(card_*.png)와 caption.txt를
# 쓰레드 캐러셀(슬라이드) 게시물로 올림. 폴더가 없으면 그냥 종료.
# 사용법: python ai-simply-threads-carousel.py [YYYY-MM-DD]   (날짜 생략 시 한국 날짜 오늘)

BASE = "https://graph.threads.net/v1.0"
TOKEN = os.environ["THREADS_TOKEN"].strip()
REPO = os.environ["GITHUB_REPOSITORY"]  # 예: dodododode/ai-simply-threads (GitHub Actions가 자동 제공)
UID = "me"

def api(method, path, **params):
    params["access_token"] = TOKEN
    q = urllib.parse.urlencode(params)
    try:
        if method == "GET":
            req = urllib.request.Request(f"{BASE}/{path}?{q}")
        else:
            req = urllib.request.Request(f"{BASE}/{path}", data=q.encode(), method="POST")
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace").replace(TOKEN, "***")
        print("오류:", e.code, path.split("/")[-1], body)
        sys.exit(1)

def wait_ready(cid):
    for _ in range(30):
        st = api("GET", cid, fields="status,error_message")
        if st.get("status") == "FINISHED":
            return
        if st.get("status") in ("ERROR", "EXPIRED"):
            print("오류: 처리 실패", st)
            sys.exit(1)
        time.sleep(3)
    print("오류: 처리 시간 초과")
    sys.exit(1)

kst = timezone(timedelta(hours=9))
day = sys.argv[1] if len(sys.argv) > 1 else datetime.now(kst).strftime("%Y-%m-%d")
folder = Path("posts") / day
if not folder.is_dir():
    print(f"{folder} 폴더가 없어 오늘은 게시하지 않습니다.")
    sys.exit(0)

images = sorted(folder.glob("card_*.png"))
if not 2 <= len(images) <= 20:
    print(f"오류: 카드 이미지는 2~20장이어야 합니다 (현재 {len(images)}장)")
    sys.exit(1)
cap_file = folder / "caption.txt"
caption = cap_file.read_text(encoding="utf-8").strip() if cap_file.exists() else ""
if len(caption) > 500:
    print(f"오류: 캡션이 {len(caption)}자입니다. 500자 이하로 줄여주세요.")
    sys.exit(1)

ids = []
for img in images:
    url = f"https://raw.githubusercontent.com/{REPO}/main/posts/{day}/{img.name}"
    cid = api("POST", f"{UID}/threads", media_type="IMAGE", image_url=url, is_carousel_item="true")["id"]
    wait_ready(cid)
    ids.append(cid)
    print("카드 준비:", img.name)

params = {"media_type": "CAROUSEL", "children": ",".join(ids)}
if caption:
    params["text"] = caption
car = api("POST", f"{UID}/threads", **params)["id"]
wait_ready(car)
pub = api("POST", f"{UID}/threads_publish", creation_id=car)["id"]
print("게시 완료 id=", pub)
