import json, random, re, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]   # scripts/ 상위 폴더
DATA = ROOT / "data" / "characters.json"
README = ROOT / "README.md"

def die(msg: str, code: int = 1):
    print(f"[ERROR] {msg}")
    sys.exit(code)

def repl(text: str, start: str, end: str, value: str) -> str:
    pattern = rf"{re.escape(start)}.*?{re.escape(end)}"
    return re.sub(pattern, f"{start}{value}{end}", text, flags=re.DOTALL)

if not DATA.exists():
    die(f"파일이 없음: {DATA}\n→ data/characters.json 생성 후 다시 실행해.")

raw = DATA.read_text(encoding="utf-8").strip()
if not raw:
    die(f"파일이 비어있음: {DATA}\n→ characters.json에 데이터가 들어있는지 확인해.")

# JSON 파싱
try:
    chars = json.loads(raw)
except json.JSONDecodeError:
    preview = raw[:200].replace("\n", "\\n")
    die(
        "JSON 파싱 실패(파일 내용이 JSON이 아님)\n"
        f"파일 앞부분 미리보기: {preview}\n"
        "→ 스크래핑 실패로 HTML/텍스트가 저장됐을 가능성이 큼."
    )

if not isinstance(chars, list) or len(chars) == 0:
    die("characters.json은 '비어있지 않은 리스트(JSON array)' 형태여야 함.")

def get(c, *keys, default="N/A"):
    for k in keys:
        v = c.get(k) if isinstance(c, dict) else None
        if v is None:
            continue
        if isinstance(v, (str, int, float)) and str(v).strip():
            return str(v).strip()
    return default

c = random.choice(chars)

name = get(c, "English Name", "Official English Name", "engName", "name", default="Unknown")
epithet = get(c, "Epithet", "epithet", default="N/A")
bounty = get(c, "Bounty", "bounty", default="N/A")

img = None
imgs = c.get("Images") if isinstance(c, dict) else None
if isinstance(imgs, list) and imgs:
    img = str(imgs[0]).strip()
elif isinstance(imgs, str) and imgs.strip():
    img = imgs.strip()
else:
    img = get(c, "img", "image", default="https://placehold.co/600x400?text=No+Image")

md = README.read_text(encoding="utf-8")

md = repl(md, "<!--OP_CHAR_NAME_START-->", "<!--OP_CHAR_NAME_END-->", name)
md = repl(md, "<!--OP_CHAR_EPITHET_START-->", "<!--OP_CHAR_EPITHET_END-->", epithet)
md = repl(md, "<!--OP_CHAR_BOUNTY_START-->", "<!--OP_CHAR_BOUNTY_END-->", bounty)
md = re.sub(
    r"<!--OP_CHAR_IMG_START-->.*?<!--OP_CHAR_IMG_END-->",
    f"<!--OP_CHAR_IMG_START-->\n![Character]({img})\n<!--OP_CHAR_IMG_END-->",
    md,
    flags=re.DOTALL,
)

README.write_text(md, encoding="utf-8")
print(f"Picked: {name} / {bounty}")
print(f"Image: {img}")
