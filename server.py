"""
宠物外观版本测试跟踪器 - 后端服务
启动方式: python server.py
访问地址: http://localhost:5210
"""
import json
import os
import subprocess
import sys
import re

# ========== 自动安装依赖 ==========
try:
    from flask import Flask, jsonify, request, send_from_directory
    from flask_cors import CORS
except ImportError:
    print("正在安装依赖...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "flask-cors", "-q"])
    from flask import Flask, jsonify, request, send_from_directory
    from flask_cors import CORS

app = Flask(__name__, static_folder='static')
CORS(app)

DATA_FILE = os.path.join(os.path.dirname(__file__), 'pet_data.json')
TRACKER_FILE = os.path.join(os.path.dirname(__file__), 'tracker_data.json')

# ========== 策划表数据源配置 ==========
# 方式1: 直接读取本地策划表导出的 lua/txt 文件
# 方式2: 调用 Config MCP SQL 查询接口
# 请根据你的环境修改以下配置

# Config MCP 的 HTTP 地址 (如果有的话)
CONFIG_MCP_URL = os.environ.get('CONFIG_MCP_URL', '')

# 本地策划表 binary 路径 (导出后的 lua 文件目录)
LOCAL_CONFIG_PATH = os.environ.get('LOCAL_CONFIG_PATH', r'd:\release\binary')


def load_pet_data():
    """加载宠物因子数据"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_pet_data(data):
    """保存宠物因子数据"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_tracker_data():
    """加载测试跟踪数据"""
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"versions": [], "currentVersion": None}


def save_tracker_data(data):
    """保存测试跟踪数据"""
    with open(TRACKER_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def parse_appearance_factor_from_lua():
    """
    从本地 lua 导出文件解析 AnimalPet_AppearanceFactor 表
    尝试多个可能的路径
    """
    possible_paths = [
        os.path.join(LOCAL_CONFIG_PATH, 'Npc', 'AnimalPet_AppearanceFactor.lua'),
        os.path.join(LOCAL_CONFIG_PATH, 'lua', 'Npc', 'AnimalPet_AppearanceFactor.lua'),
        os.path.join(LOCAL_CONFIG_PATH, 'AnimalPet_AppearanceFactor.lua'),
    ]

    lua_file = None
    for p in possible_paths:
        if os.path.exists(p):
            lua_file = p
            break

    if not lua_file:
        return None, f"未找到策划表文件，尝试过的路径: {possible_paths}"

    try:
        with open(lua_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return parse_lua_table(content), None
    except Exception as e:
        return None, f"解析文件失败: {str(e)}"


def parse_lua_table(content):
    """
    简单解析 lua 导出的策划表数据
    提取 body 类型的外观因子信息
    """
    results = []
    # 简单的正则解析方式 - 根据实际 lua 格式调整
    # 这里提供基础框架,具体解析逻辑根据实际文件格式调整
    
    # 尝试按行提取记录
    lines = content.split('\n')
    current_record = {}
    
    for line in lines:
        line = line.strip()
        # 匹配 key = value 模式
        match = re.match(r'\["?(\w+)"?\]\s*=\s*(.+?),?\s*$', line)
        if match:
            key, value = match.group(1), match.group(2)
            # 清理值
            value = value.strip().rstrip(',')
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value == 'nil':
                value = None
            else:
                try:
                    value = float(value) if '.' in value else int(value)
                except:
                    pass
            current_record[key] = value
        
        # 检测记录结束
        if line == '},' or line == '}':
            if current_record.get('ClassName') == 'body' and current_record.get('Id'):
                results.append({
                    'id': current_record.get('Id'),
                    'name': current_record.get('Name', ''),
                    'rank': current_record.get('Rank', 0),
                    'score': current_record.get('Score'),
                    'petType': current_record.get('PetType'),
                    'obtainMethod': current_record.get('ObtainMethod', ''),
                    'openSeason': current_record.get('OpenSeason', ''),
                })
            current_record = {}
    
    return results


# ========== API 路由 ==========

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/api/query_pets', methods=['GET'])
def query_pets():
    """
    查询指定赛季的宠物外观
    参数: season=3.3.3
    支持两种数据源:
      1. 优先: 从 Config MCP 实时查询 (需要 mcp_bridge 服务)
      2. 兜底: 从本地 pet_data.json 筛选
    """
    season = request.args.get('season', '').strip()
    if not season:
        return jsonify({"success": False, "error": "请提供 season 参数"})

    # 规范化版本号: 333 -> 3.3.3
    if re.match(r'^\d{3,}$', season) and '.' not in season:
        season = '.'.join(season)

    all_data = load_pet_data()

    # 筛选匹配的赛季
    results = []
    for pet in all_data:
        os_text = pet.get('openSeason', '') or ''
        # 精确匹配: "3.3.3" 匹配 "3.3.3" 和 "3.3.3,1D@8H"
        if os_text == season or os_text.startswith(season + ',') or os_text.startswith(season + ' '):
            results.append(pet)

    return jsonify({
        "success": True,
        "season": season,
        "total": len(results),
        "pets": results,
        "all_seasons": get_all_seasons(all_data),
    })


@app.route('/api/inject_pets', methods=['POST'])
def inject_pets():
    """
    注入宠物数据（追加模式，去重）
    前端或脚本可以把 MCP 查询结果直接 POST 到这里
    Body: {"rows": [...]} 或 [...]
    """
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "无数据"})

    rows = data if isinstance(data, list) else data.get('rows', data.get('pets', []))
    if not rows:
        return jsonify({"success": False, "error": "rows/pets 为空"})

    existing = load_pet_data()
    existing_ids = {p.get('id') for p in existing}
    added = 0

    for r in rows:
        pet = {
            'id': int(r.get('Id') or r.get('id') or 0),
            'name': str(r.get('Name') or r.get('name') or ''),
            'rank': int(r.get('Rank') or r.get('rank') or 0),
            'score': int(r.get('Score') or r.get('score') or 0),
            'petType': int(r.get('PetType') or r.get('petType') or 0),
            'obtainMethod': str(r.get('ObtainMethod') or r.get('obtainMethod') or ''),
            'openSeason': str(r.get('OpenSeason') or r.get('openSeason') or ''),
            'status': 0,
        }
        if pet['id'] and pet['id'] not in existing_ids:
            existing.append(pet)
            existing_ids.add(pet['id'])
            added += 1

    existing.sort(key=lambda x: x.get('id', 0))
    save_pet_data(existing)
    return jsonify({
        "success": True,
        "added": added,
        "total": len(existing),
        "message": f"新增 {added} 条，总计 {len(existing)} 条"
    })


@app.route('/api/all_seasons', methods=['GET'])
def all_seasons():
    """获取所有可用赛季列表"""
    all_data = load_pet_data()
    seasons = get_all_seasons(all_data)
    return jsonify({"success": True, "seasons": seasons, "total_pets": len(all_data)})


def get_all_seasons(all_data):
    """提取所有不重复的赛季版本号"""
    seasons = set()
    for pet in all_data:
        os_text = pet.get('openSeason', '') or ''
        if os_text:
            # 提取主版本号 (去掉 ,1D@8H 之类的后缀)
            main_season = os_text.split(',')[0].strip()
            if main_season:
                seasons.add(main_season)
    return sorted(seasons)


@app.route('/api/refresh_data', methods=['POST'])
def refresh_data():
    """
    刷新策划表数据
    支持三种方式:
    1. 上传 JSON 数据 (body 传 JSON 数组)
    2. 从本地 lua 文件解析
    3. 未来可扩展: 调用 Config MCP
    
    传 append=true 追加而非覆盖
    """
    # 方式1: 直接上传 JSON
    if request.is_json:
        data = request.get_json()
        append_mode = False
        if isinstance(data, dict):
            append_mode = data.get('append', False)
        
        if isinstance(data, list):
            if append_mode:
                existing = load_pet_data()
                existing_ids = {p.get('id') for p in existing}
                for item in data:
                    if item.get('id') not in existing_ids:
                        existing.append(item)
                        existing_ids.add(item.get('id'))
                save_pet_data(existing)
                return jsonify({"success": True, "message": f"追加后共 {len(existing)} 条数据", "total": len(existing)})
            save_pet_data(data)
            return jsonify({"success": True, "message": f"已更新 {len(data)} 条数据", "total": len(data)})
        elif isinstance(data, dict) and 'rows' in data:
            rows = data['rows']
            # 转换格式
            pets = []
            for r in rows:
                pets.append({
                    'id': r.get('Id') or r.get('id'),
                    'name': r.get('Name') or r.get('name', ''),
                    'rank': r.get('Rank') or r.get('rank', 0),
                    'score': r.get('Score') or r.get('score'),
                    'petType': r.get('PetType') or r.get('petType'),
                    'obtainMethod': r.get('ObtainMethod__text') or r.get('obtainMethod', ''),
                    'openSeason': r.get('OpenSeason__text') or r.get('openSeason', ''),
                    'status': r.get('Status') or r.get('status', 0),
                })
            if append_mode:
                existing = load_pet_data()
                existing_ids = {p.get('id') for p in existing}
                for item in pets:
                    if item.get('id') not in existing_ids:
                        existing.append(item)
                        existing_ids.add(item.get('id'))
                save_pet_data(existing)
                return jsonify({"success": True, "message": f"追加后共 {len(existing)} 条", "total": len(existing)})
            save_pet_data(pets)
            return jsonify({"success": True, "message": f"已更新 {len(pets)} 条数据", "total": len(pets)})

    # 方式2: 尝试从本地文件解析
    data, error = parse_appearance_factor_from_lua()
    if data is not None:
        save_pet_data(data)
        return jsonify({"success": True, "message": f"从本地文件解析到 {len(data)} 条数据", "total": len(data)})
    
    return jsonify({"success": False, "error": error or "无法刷新数据"})


@app.route('/api/tracker', methods=['GET'])
def get_tracker():
    """获取测试跟踪数据"""
    return jsonify({"success": True, "data": load_tracker_data()})


@app.route('/api/tracker', methods=['POST'])
def save_tracker():
    """保存测试跟踪数据"""
    data = request.get_json()
    save_tracker_data(data)
    return jsonify({"success": True})


@app.route('/api/upload_data', methods=['POST'])
def upload_data():
    """通过文件上传更新数据"""
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "请上传文件"})
    
    file = request.files['file']
    try:
        content = file.read().decode('utf-8')
        data = json.loads(content)
        if isinstance(data, dict) and 'rows' in data:
            data = data['rows']
        
        if isinstance(data, list):
            # 标准化字段名
            pets = []
            for r in data:
                pets.append({
                    'id': r.get('Id') or r.get('id'),
                    'name': r.get('Name') or r.get('name', ''),
                    'rank': r.get('Rank') or r.get('rank', 0),
                    'score': r.get('Score') or r.get('score'),
                    'petType': r.get('PetType') or r.get('petType'),
                    'obtainMethod': r.get('ObtainMethod__text') or r.get('obtainMethod', ''),
                    'openSeason': r.get('OpenSeason__text') or r.get('openSeason', ''),
                })
            save_pet_data(pets)
            return jsonify({"success": True, "message": f"上传成功，共 {len(pets)} 条", "total": len(pets)})
        
        return jsonify({"success": False, "error": "数据格式不正确"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


if __name__ == '__main__':
    # 确保 static 目录存在
    os.makedirs(os.path.join(os.path.dirname(__file__), 'static'), exist_ok=True)
    
    print("=" * 50)
    print("🐾 宠物外观版本测试跟踪器")
    print("=" * 50)
    print(f"📂 数据文件: {DATA_FILE}")
    print(f"📂 跟踪文件: {TRACKER_FILE}")
    print(f"🌐 访问地址: http://localhost:5210")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5210, debug=True)
