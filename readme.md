# WynnCraft Dashboard

WynnCraft Player Dashboard — WynnCraft 玩家数据监控面板

## 项目结构

```
├── .editorconfig
├── .gitignore
├── .env.example                   # 环境变量模板（所有可自定义项）
├── .env                           # 实际配置
│
├── backend/                       # Python 后端 (FastAPI)
│   ├── app/
│   │   ├── main.py                # FastAPI 入口（lifespan + CORS + 路由注册）
│   │   ├── config.py              # 从环境变量读取配置（TARGET_PLAYER, DATABASE_URL…）
│   │   ├── database.py            # 数据库引擎 & 表初始化
│   │   ├── constants.py           # 用户自定义常量（RAID_NAME_MAP）
│   │   ├── models/                # SQLModel 数据模型
│   │   │   ├── player.py          # PlayerHistory
│   │   │   ├── summary.py         # HourlySummary, DailySummary
│   │   │   └── event.py           # PlayerEventLog
│   │   ├── services/              # 核心业务逻辑
│   │   │   ├── fetcher.py         # API 抓取 + 在线/切服/升级等 Diff 日志
│   │   │   └── archiver.py        # 小时归档 + 日归档
│   │   └── routers/               # API 路由
│   │       ├── fetch.py           # POST /api/fetch_now
│   │       ├── history.py         # GET /api/history
│   │       ├── logs.py            # GET /api/logs
│   │       ├── summary.py         # GET /api/daily_summary
│   │       └── hourly.py          # GET /api/hourly_records_by_date
│   ├── requirements.txt
│   └── player_data.db             # SQLite 数据库（自动生成）
│
├── frontend/                      # Vue 3 + Vite 前端
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── public/
│   │   └── favicon.svg
│   └── src/
│       ├── main.js
│       ├── style.css
│       ├── config/
│       │   └── constants.js       # 用户自定义常量（RAID_NAME_MAP, RANKING_NAME_MAP…）
│       ├── api/
│       │   └── client.js          # 统一封装所有后端 fetch 调用
│       ├── composables/
│       │   ├── useData.js         # 核心数据状态 + 5 分钟自动刷新
│       │   ├── useCalendar.js     # 日历日期选择状态
│       │   └── useChart.js        # ECharts 图表渲染
│       └── components/
│           ├── App.vue            # 主布局（状态中枢）
│           ├── Header.vue         # 玩家信息头
│           ├── Calendar.vue       # 战绩打卡日历
│           ├── StatsPanel.vue     # 当前实时数据面板
│           ├── DailyReport.vue    # 每日战报总结
│           ├── DetailTabs.vue     # Raid / 公会 Raid / 排名 Tab
│           ├── EventTimeline.vue  # 最新动态时间线（含上线/下线/切服/Raid…）
│           └── TrendChart.vue     # ECharts 趋势图表
```

## 快速启动

### 后端

```bash
# 1. 创建并激活虚拟环境（首次）
cd backend
py -m venv ../.venv
..\.venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动
fastapi dev app/main.py   # 开发模式（热重载）
fastapi run app/main.py   # 生产模式
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

前端默认通过 Vite proxy 将 `/api` 请求转发到 `http://127.0.0.1:8000`，无需额外配置。

## 功能

- 每 5 分钟自动抓取 Wynncraft API 玩家数据
- **上线 / 下线 / 切服**事件追踪
- **Raid 通关 / 公会 Raid / 等级提升**日志记录
- 实时数据面板（总等级、游玩时间、击杀数、开箱数…）
- 小时级 + 日级数据归档与趋势图表
- 战绩打卡日历（按日查看历史战报）

## 自定义配置

### 改玩家名 / 计时起点

编辑根目录 `.env`（从 `.env.example` 复制）：

```ini
TARGET_PLAYER=Kasyu_pwq       # Wynncraft API 查询用
PLAYER_NAME=卡死鱼              # 前后端显示名称
VITE_RUNTIME_START=2026-05-20T00:00:00   # 前端计时起始时间
```

### 加新副本 / 新排名项 / 更改副本别名

| 文件 | 改什么 |
|------|--------|
| `backend/app/constants.py` | `RAID_NAME_MAP` |
| `frontend/src/config/constants.js` | `RAID_NAME_MAP` / `RANKING_NAME_MAP` |

格式：在这个字典里加一行 `"API返回的英文名": "你想显示的中文名"` 即可。
