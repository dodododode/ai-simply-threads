import os, sys, time, re, json
import urllib.request, urllib.parse, urllib.error

# 사용법: THREADS_USER_ID=... THREADS_TOKEN=... python ai-simply-threads-post.py threads.txt
# threads.txt(글 1/N ~ N/N)를 첫 글 + 이어지는 답글(타래) 형태로 게시
# 토큰은 코드에 적지 말고 환경변수(또는 GitHub Secrets)로만 넣을 것

BASE = "https://graph.threads.net/v1.0"
UID = os.environ["THREADS_USER_ID"].strip()
TOKEN = os.environ["THREADS_TOKEN"].strip()

def call(path, **params):
    params["access_token"] = TOKEN
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(f"{BASE}/{path}", data=data, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace").replace(TOKEN, "***")
        print("오류:", e.code, path.split("/")[-1], body)
        sys.exit(1)

def post(text, reply_to=None):
    p = {"media_type": "TEXT", "text": text}
    if reply_to:
        p["reply_to_id"] = reply_to
    cid = call(f"{UID}/threads", **p)["id"]
    time.sleep(5)  # 컨테이너 처리 대기
    return call(f"{UID}/threads_publish", creation_id=cid)["id"]

src = sys.argv[1] if len(sys.argv) > 1 else "threads.txt"
parts = re.split(r"===== 글 \d+ =====\n", open(src, encoding="utf-8").read())
posts = [p.strip() for p in parts if p.strip()]

prev = None
for i, t in enumerate(posts, 1):
    prev = post(t, reply_to=prev)
    print(f"글 {i}/{len(posts)} 게시 완료 id={prev}")
    time.sleep(3)
