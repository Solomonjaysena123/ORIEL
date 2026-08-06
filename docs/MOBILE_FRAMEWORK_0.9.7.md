# ORIEL iOS and Unified Mobile Framework 0.9.7

ORIEL 0.9.7 adds portable iOS/iPadOS project generation and a unified Android+iOS project model.

Use `oriel ios new App --bundle-id org.example.app` to generate XcodeGen configuration, Swift UIKit lifecycle sources, Info.plist privacy descriptions, device-family settings, and release metadata. Validate with `oriel ios validate App`; build a simulator app with `oriel ios build App`, or an archive with `--archive`.

`IOSRenderer` maps shared UI nodes to UIKit view contracts and retains layout, accessibility, keys, and diagnostics. `IOSLifecycle`, `IOSDeviceInfo`, and `MockIOSDevice` provide testable platform contracts.

Use `oriel mobile new App --application-id org.example.app` for one root containing matched Android and iOS projects and `oriel mobile validate App` for cumulative validation.

Store validation requires `ORIEL_APPLE_TEAM_ID`, `ORIEL_APPLE_SIGNING_IDENTITY`, and `ORIEL_APPLE_PROVISIONING_PROFILE`. Signing certificates and provisioning profiles must stay outside source control. Signed archives and App Store upload require macOS, Xcode, Apple credentials, and App Store Connect access.
