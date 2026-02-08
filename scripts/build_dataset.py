# scripts/build_dataset.py
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

API = "https://api.api-onepiece.com/v2/characters/en"  # no key needed
OUT = Path("data/characters.json")

def bounty_to_int(b: Optional[str]) -> Optional[int]:
    if not b:
        return None
    b = str(b).strip()
    if b in ["", "?", "null", "None", "N/A"]:
        return None
    # keep digits only (handles "3 000 000 000" / "3,000,000,000" etc.)
    digits = re.sub(r"[^\d]", "", b)
    return int(digits) if digits else None

def robohash_url(name: str) -> str:
    # copyright 걱정 없는 자동 생성 이미지 (매번 동일하게 나옴)
    # set=set4 = cats, set=set2 = robots 등 취향대로 변경 가능
    safe = requests.utils.quote(name)
    return f"https://robohash.org/{safe}.png?size=600x400&set=set4"

def main():
    r = requests.get(API, timeout=60)
    r.raise_for_status()
    items: List[Dict[str, Any]] = r.json()

    # bounty 있는 캐릭터만 뽑고, 현상금 큰 순으로 100명
    rows = []
    for it in items:
        name = (it.get("name") or "").strip()
        job = (it.get("job") or "").strip()  # '별명' 대신 job을 Epithet로 쓰자
        bounty_raw = it.get("bounty")
        b_int = bounty_to_int(bounty_raw)
        if not name or b_int is None:
            continue

        rows.append((b_int, name, job, bounty_raw))

    rows.sort(key=lambda x: x[0], reverse=True)
    top = rows[:100]

    data = []
    for b_int, name, job, bounty_raw in top:
        data.append(
            {
                "name": name,
                "Epithet": job if job else "N/A",
                "Bounty": f"{b_int:,}",
                "Images": [robohash_url(name)],
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✅ wrote {len(data)} chars -> {OUT}")

if __name__ == "__main__":
    main()
