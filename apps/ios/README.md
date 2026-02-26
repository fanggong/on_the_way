# iOS App (React Native) - v0.1.0

完整 React Native 原生工程（含 `ios/` Xcode 工程与 Podfile）已就绪。

## Scope

- F1 手工录入 `manual-signal`
- F2 查询 `daily-summary`
- F3 状态提示（`idle/submitting/success/error`）

## Environment

可在启动 Metro 前设置接口地址:

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
