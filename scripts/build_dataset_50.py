# scripts/build_dataset_50.py
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import requests

OUT = Path("data/characters.json")

# 1) bounty source (no key)
ONEPIECE_API = "https://api.api-onepiece.com/v2/characters/en"  # :contentReference[oaicite:2]{index=2}

# 2) images source: Jikan (One Piece anime id is 21 on MAL)
# Jikan docs: https://docs.api.jikan.moe/  :contentReference[oaicite:3]{index=3}
JIKAN_ONEPIECE_CHARS = "https://api.jikan.moe/v4/anime/21/characters"

def norm(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"[\W_]+", "", s)          # remove spaces/punct
    s = s.replace("monkeydluffy", "luffy") # tiny helper
    return s

def bounty_to_int(b: Any) -> Optional[int]:
    if b is None:
        return None
    digits = re.sub(r"[^\d]", "", str(b))
    return int(digits) if digits else None

def get_json(url: str, timeout: int = 60) -> Any:
    r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return r.json()

def build_image_map_from_jikan() -> Dict[str, str]:
    j = get_json(JIKAN_ONEPIECE_CHARS)
    data = j.get("data", [])
    m: Dict[str, str] = {}

    for it in data:
        ch = it.get("character", {})
        name = ch.get("name", "")
        images = ch.get("images", {})
        jpg = images.get("jpg", {}) if isinstance(images, dict) else {}
        img = jpg.get("image_url") or jpg.get("large_image_url")

        if name and img:
            m[norm(name)] = img

    return m

def pick_best_image(name: str, image_map: Dict[str, str]) -> str:
    key = norm(name)
    if key in image_map:
        return image_map[key]

    # 약한 매칭: 포함 관계(예: "Roronoa Zoro" vs "Zoro, Roronoa" 같은 케이스)
    for k, v in image_map.items():
        if key and (key in k or k in key):
            return v

    # 못 찾으면 placeholder
    return "https://placehold.co/600x400?text=One+Piece"

def main():
    # Jikan: name -> image_url
    img_map = build_image_map_from_jikan()

    # One Piece API: bounty/job/name
    items: List[Dict[str, Any]] = get_json(ONEPIECE_API)

    rows: List[Tuple[int, str, str]] = []
    for it in items:
        name = (it.get("name") or "").strip()
        job = (it.get("job") or "").strip()   # Epithet 대체로 사용
        b_int = bounty_to_int(it.get("bounty"))
        if not name or b_int is None:
            continue
        rows.append((b_int, name, job))

    rows.sort(key=lambda x: x[0], reverse=True)
    top = rows[:50]

    out = []
    for b_int, name, job in top:
        img = pick_best_image(name, img_map)
        out.append({
            "name": name,
            "Epithet": job if job else "N/A",
            "Bounty": f"{b_int:,}",
            "Images": [img]
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ wrote {len(out)} characters with One Piece images -> {OUT}")

if __name__ == "__main__":
    main()
