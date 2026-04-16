"""
fetch_all_pets.py  
通过 config_sql MCP 接口结果，生成完整的 pet_data.json
运行: python fetch_all_pets.py
"""
import json, os, sys, urllib.request

DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(DIR, 'pet_data.json')
SERVER = 'http://127.0.0.1:5210'

def transform(row):
    """将 MCP 行数据转为 tracker 格式"""
    return {
        "id": int(row.get("Id") or row.get("id") or 0),
        "name": str(row.get("Name") or row.get("name") or ""),
        "rank": int(row.get("Rank") or row.get("rank") or 0),
        "score": int(row.get("Score") or row.get("score") or 0),
        "petType": int(row.get("PetType") or row.get("petType") or 0),
        "obtainMethod": str(row.get("ObtainMethod") or row.get("obtainMethod") or ""),
        "openSeason": str(row.get("OpenSeason") or row.get("openSeason") or ""),
        "status": 0
    }

def main():
    # 读取 stdin 或命令行指定的 JSON 文件
    if len(sys.argv) > 1:
        src = sys.argv[1]
        with open(src, 'r', encoding='utf-8') as f:
            raw = json.load(f)
    else:
        print("用法: python fetch_all_pets.py <mcp_result.json>")
        print("  或通过管道: echo '[...]' | python fetch_all_pets.py -")
        print("\n也可以通过 HTTP POST 传入数据:")
        print(f"  curl -X POST {SERVER}/api/refresh_data -H 'Content-Type: application/json' -d @data.json")
        return

    # raw 可以是 {rows:[...]} 或 [...]
    if isinstance(raw, dict):
        rows = raw.get('rows') or raw.get('data', {}).get('rows', [])
    elif isinstance(raw, list):
        rows = raw
    else:
        print("格式错误"); return

    pets = [transform(r) for r in rows]
    # 去重
    seen = set()
    unique = []
    for p in pets:
        if p["id"] and p["id"] not in seen:
            seen.add(p["id"])
            unique.append(p)
    unique.sort(key=lambda x: x["id"])

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)
    print(f"✅ 写入 {len(unique)} 条宠物数据到 {OUT}")

if __name__ == '__main__':
    main()
