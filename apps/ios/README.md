# iOS App (React Native) - v0.3.1

完整 React Native 原生工程（含 `ios/` Xcode 工程与 Podfile）已就绪。  
版本状态: `已验收（已完成）`

## Scope

- 首页主题导航（延续 v0.2.0）
  - 顶部品牌区（`On The Way` / `今日概览` / 当天日期）
  - 8 主题横向导航栏
  - 2 列 x 4 行主题卡片区
  - 统一占位反馈（`即将开放`）
- v0.3.1 已退役 POC 调试能力
  - 移除手工录入页与结果查询页
  - 移除长按首页进入调试入口

## Run (local)

首次需确保 CocoaPods 可用（推荐 Homebrew）:

```bash
brew install cocoapods
```

终端 A:

```bash
npm install
npm run pods
npm start
```

终端 B:

```bash
npm run ios -- --simulator "iPhone 17"
```

也可直接用 Xcode 打开 `apps/ios/ios/OnTheWayIOS.xcodeproj` 运行模拟器或真机。

## UI Acceptance Checklist (v0.3.1)

- 首屏为主题首页。
- 8 个主题入口均可点击并提示“即将开放”。
- 不存在 POC 调试入口与相关调试页面。
