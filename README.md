# 🐾 宠物外观版本测试跟踪器

一站式宠物外观 QA 测试跟踪工具，支持多赛季版本管理、检查矩阵、头像管理、Bug 关联等功能。

## 📦 项目结构

```
pet_tracker/
├── server.py              # Flask 后端服务 (端口 5210)
├── fetch_all_pets.py       # 辅助脚本：批量导入宠物数据
├── static/
│   └── index.html          # 前端单页应用 (纯 HTML/CSS/JS)
├── pet_data.json           # 宠物策划表数据 (运行时生成，git 忽略)
├── tracker_data.json       # 测试跟踪数据 (运行时生成，git 忽略)
├── .gitignore
└── README.md
```

## 🚀 快速启动

```bash
# 1. 进入项目目录
cd pet_tracker

# 2. 启动服务 (自动安装 flask/flask-cors)
python server.py

# 3. 打开浏览器
# http://localhost:5210
```

## ✨ 核心功能

### 多赛季版本管理
- 创建/切换/重命名/删除赛季版本
- 每个版本独立管理宠物列表和测试进度
- 新建版本自动继承当前检查项模板

### 检查矩阵 (34项默认检查)
- **策划配置** (7项): 因子表、Pet模板、Item道具、赛季配置等
- **美术资源** (6项): 模型、特效、动作、大世界表现等
- **界面功能** (8项): 图标、图鉴、召唤标识、分享等
- **投放验证** (5项): 外观因子、获得方式、特质等
- **特殊专项** (8项): 灵宠系列、福宝宝、萌萌泥等

### 检查项跨版本同步
- 新增/删除/重命名检查项时自动同步到所有赛季
- 新建赛季自动继承最新检查项列表

### 其他功能
- 🖼️ 头像管理：Ctrl+V 粘贴、拖拽、文件选择，支持 Lightbox 放大浏览
- 🔗 Bug 关联：右键关联工单号或 URL，支持一键跳转
- 📝 备注系统：支持文字 + 截图备注
- 👤 多人协作：设置操作人，标记每个格子的测试者
- 📊 统计面板：实时通过率、失败数、进度条
- 🔍 筛选：全部/仅失败/仅待测
- 📥📤 导入导出：JSON 格式完整备份

## 📡 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/api/query_pets?season=3.3.4` | 按赛季查询宠物 |
| GET  | `/api/all_seasons` | 获取所有可用赛季列表 |
| POST | `/api/inject_pets` | 注入宠物数据 (追加去重) |
| POST | `/api/refresh_data` | 刷新策划表数据 |
| GET  | `/api/tracker` | 获取测试跟踪数据 |
| POST | `/api/tracker` | 保存测试跟踪数据 |

## 🔧 数据灌入

通过 Config MCP 查询策划表后，使用 `inject_pets` 接口灌入数据：

```bash
curl -X POST http://localhost:5210/api/inject_pets \
  -H "Content-Type: application/json" \
  -d '{"rows": [{"Id": 10101, "Name": "典·棠梨", "Rank": 4, ...}]}'
```

或使用辅助脚本：
```bash
python fetch_all_pets.py <mcp_result.json>
```