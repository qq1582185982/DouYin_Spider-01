# DouYin Spider Web UI

基于 SvelteKit 构建的抖音爬虫管理界面。

## 功能特性

- 🎯 **用户爬取** - 输入用户主页URL，批量爬取所有作品
- 🔍 **搜索爬取** - 根据关键词搜索并爬取相关视频
- 📺 **直播监控** - 实时监控直播间弹幕和礼物
- 📊 **数据管理** - 查看和管理已爬取的视频数据
- ⚙️ **系统设置** - 配置Cookie、保存路径等参数

## 快速开始

### 安装依赖
```bash
npm install
```

### 开发模式
```bash
npm run dev
```

### 构建生产版本
```bash
npm run build
```

## 技术栈

- **框架**: SvelteKit
- **样式**: Tailwind CSS
- **语言**: TypeScript
- **UI组件**: 自定义组件库
- **状态管理**: Svelte Store

## 项目结构

```
web/
├── src/
│   ├── lib/
│   │   ├── components/     # UI组件
│   │   ├── stores/         # 状态管理
│   │   ├── utils.ts        # 工具函数
│   │   ├── api.ts          # API客户端
│   │   └── types.ts        # 类型定义
│   ├── routes/             # 页面路由
│   │   ├── +page.svelte    # 首页/仪表板
│   │   ├── spider/         # 爬虫功能
│   │   ├── videos/         # 视频管理
│   │   ├── live/           # 直播监控
│   │   └── settings/       # 系统设置
│   └── app.css             # 全局样式
├── static/                 # 静态资源
└── package.json

```

## 配置说明

1. **后端API地址**: 在 `vite.config.ts` 中配置代理
2. **端口**: 默认运行在 5173 端口

## 注意事项

- 首次使用需要在设置页面配置抖音Cookie
- Cookie需要从浏览器开发者工具中获取
- 确保后端服务已启动（默认端口8000）