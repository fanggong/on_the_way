# iOS App (React Native) - v0.2.0

完整 React Native 原生工程（含 `ios/` Xcode 工程与 Podfile）已就绪。
版本状态: `已验收（2026-02-26）`

## Scope

- v0.2.0 首页 UI/UX（MUJI 风格）
  - 顶部品牌区（`On The Way` / `今日概览` / 当天日期）
  - 8 主题横向导航栏
  - 2 列 x 4 行主题卡片区
  - 统一占位反馈（`即将开放`）
- v0.1.0 调试页面保留（手工录入 / 结果查询）
  - 不在首页主导航展示
  - 长按首页品牌区进入调试入口

## Environment

可在启动 Metro 前设置接口地址（调试页联调使用）:

```bash
export API_BASE_URL=http://localhost:8000
```

首次需确保 CocoaPods 可用（推荐 Homebrew）:

```bash
brew install cocoapods
```

## Run (local)

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

## UI Acceptance Checklist (v0.2.0)

- 首屏为 v0.2.0 首页，不再默认显示手工录入/结果查询。
- 8 个主题入口均可点击并提示“即将开放”。
- 文案中不出现“系统”字样。
- 长按品牌区可进入调试页，验证 v0.1.0 录入/查询能力未被破坏。
