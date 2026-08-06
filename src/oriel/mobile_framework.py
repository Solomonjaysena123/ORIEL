"""ORIEL 0.9.7 iOS/iPadOS and unified mobile packaging."""
from __future__ import annotations
import json, os, plistlib, re, shutil, subprocess, time, uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Protocol
from xml.etree import ElementTree
from .android_framework import AndroidConfig, create_android_project, validate_android_project
from .ui_engine import Node, RenderTree, UIContext, validate_tree

class MobileConfigurationError(ValueError):pass
class MobileBuildError(RuntimeError):pass

class ApplePlatform(str,Enum):
    IOS="iOS";IPADOS="iPadOS";UNIVERSAL="universal"
class IOSPermission(str,Enum):
    CAMERA="NSCameraUsageDescription"
    MICROPHONE="NSMicrophoneUsageDescription"
    LOCATION="NSLocationWhenInUseUsageDescription"
    PHOTOS="NSPhotoLibraryUsageDescription"
    CONTACTS="NSContactsUsageDescription"
    BLUETOOTH="NSBluetoothAlwaysUsageDescription"
    NOTIFICATIONS="notifications"
class IOSLifecycleState(str,Enum):
    INACTIVE="inactive";ACTIVE="active";BACKGROUND="background";TERMINATED="terminated"

class IOSLifecycle:
    _allowed={None:{IOSLifecycleState.INACTIVE},IOSLifecycleState.INACTIVE:{IOSLifecycleState.ACTIVE,IOSLifecycleState.BACKGROUND,IOSLifecycleState.TERMINATED},IOSLifecycleState.ACTIVE:{IOSLifecycleState.INACTIVE,IOSLifecycleState.BACKGROUND},IOSLifecycleState.BACKGROUND:{IOSLifecycleState.INACTIVE,IOSLifecycleState.TERMINATED},IOSLifecycleState.TERMINATED:set()}
    def __init__(self):self.state=None;self.observers=[]
    def observe(self,observer):
        if not callable(observer):raise TypeError("lifecycle observer must be callable")
        self.observers.append(observer)
        return lambda:self.observers.remove(observer) if observer in self.observers else None
    def transition(self,state):
        if state not in self._allowed[self.state]:raise RuntimeError(f"invalid iOS lifecycle transition: {self.state} -> {state.value}")
        self.state=state
        for observer in tuple(self.observers):observer(state)

@dataclass(frozen=True,slots=True)
class IOSDeviceInfo:
    model:str="iPhone Simulator";system_version:str="18.0";locale:str="en-US";idiom:str="phone";is_simulator:bool=True
    def __post_init__(self):
        if self.idiom not in {"phone","pad"}:raise ValueError("idiom must be phone or pad")
        if not re.fullmatch(r"\d+(?:\.\d+){0,2}",self.system_version):raise ValueError("invalid iOS system version")

class IOSDeviceBackend(Protocol):
    def device_info(self)->IOSDeviceInfo:...
    def open_url(self,url:str)->bool:...
    def haptic(self,style:str)->None:...

class MockIOSDevice:
    def __init__(self,info=None):self.info=info or IOSDeviceInfo();self.urls=[];self.haptics=[]
    def device_info(self):return self.info
    def open_url(self,url):
        if not re.fullmatch(r"(?:https?|tel|mailto|maps):[^\r\n]+",url):return False
        self.urls.append(url);return True
    def haptic(self,style):
        if style not in {"light","medium","heavy","success","warning","error"}:raise ValueError("unsupported haptic style")
        self.haptics.append(style)

@dataclass(frozen=True,slots=True)
class IOSConfig:
    bundle_id:str
    app_name:str
    version:str="0.1.0"
    build_number:int=1
    deployment_target:str="15.0"
    platform:ApplePlatform=ApplePlatform.UNIVERSAL
    team_id:str|None=None
    permissions:Mapping[IOSPermission,str]=field(default_factory=dict)
    background_modes:tuple[str,...]=()
    def __post_init__(self):
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9-]*(?:\.[A-Za-z0-9-]+)+",self.bundle_id):raise MobileConfigurationError("invalid Apple bundle identifier")
        if not self.app_name.strip() or self.app_name in {".",".."} or any(c in self.app_name for c in '\\/:*?"<>|\r\n\x00'):raise MobileConfigurationError("unsafe application name")
        if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?",self.version):raise MobileConfigurationError("version must use semantic versioning")
        if self.build_number<1:raise MobileConfigurationError("build number must be positive")
        if not re.fullmatch(r"\d+\.\d+",self.deployment_target):raise MobileConfigurationError("invalid deployment target")
        if self.team_id and not re.fullmatch(r"[A-Z0-9]{10}",self.team_id):raise MobileConfigurationError("Apple team id must contain 10 uppercase characters")
        for permission,reason in self.permissions.items():
            if permission!=IOSPermission.NOTIFICATIONS and not reason.strip():raise MobileConfigurationError(f"usage description required for {permission.name.lower()}")
        allowed={"audio","location","fetch","remote-notification","processing"}
        if any(mode not in allowed for mode in self.background_modes):raise MobileConfigurationError("unsupported iOS background mode")

class IOSRenderer:
    platform="ios"
    _views={"container":"UIStackView","text":"UILabel","heading":"UILabel","button":"UIButton","image":"UIImageView","input":"UITextField","link":"UIButton"}
    def render(self,node:Node,context:UIContext)->RenderTree:
        diagnostics=tuple(validate_tree(node))
        def encode(current):
            layout=current.layout
            if current.kind=="container" and layout:view={"grid":"UICollectionView","stack":"UIView"}.get(layout.display,"UIStackView")
            else:view=self._views.get(current.kind,"UIView")
            props=dict(current.props)
            if current.kind in {"text","heading"}:props["text"]=props.pop("value","")
            if current.semantics:
                props.update(accessibilityLabel=current.semantics.label,accessibilityHint=current.semantics.hint,isAccessibilityElement=not current.semantics.hidden,enabled=current.semantics.enabled)
                if current.semantics.heading_level:props["accessibilityTraits"]=["header"]
            encoded_layout=None if not layout else {"display":layout.display,"axis":layout.direction,"spacing":layout.gap,"padding":[layout.padding.top,layout.padding.right,layout.padding.bottom,layout.padding.left],"width":layout.width,"height":layout.height,"align":layout.align,"justify":layout.justify,"grow":layout.grow}
            return {"view":view,"key":current.key,"props":props,"layout":encoded_layout,"children":[encode(child) for child in current.children]}
        return RenderTree(self.platform,encode(node),diagnostics)

def _plist(config:IOSConfig)->dict[str,Any]:
    value={"CFBundleDisplayName":config.app_name,"CFBundleIdentifier":"$(PRODUCT_BUNDLE_IDENTIFIER)","CFBundleShortVersionString":config.version,"CFBundleVersion":str(config.build_number),"UILaunchScreen":{},"UIApplicationSupportsIndirectInputEvents":True}
    for permission,reason in config.permissions.items():
        if permission!=IOSPermission.NOTIFICATIONS:value[permission.value]=reason
    if config.background_modes:value["UIBackgroundModes"]=list(config.background_modes)
    if config.platform==ApplePlatform.IOS:value["UIDeviceFamily"]=[1]
    elif config.platform==ApplePlatform.IPADOS:value["UIDeviceFamily"]=[2]
    else:value["UIDeviceFamily"]=[1,2]
    return value

def _project_yml(config:IOSConfig)->str:
    devices={"iOS":"iPhone","iPadOS":"iPad","universal":"universal"}[config.platform.value]
    team=f"\n        DEVELOPMENT_TEAM: {config.team_id}" if config.team_id else ""
    return f'''name: {config.app_name}
options:
  bundleIdPrefix: {config.bundle_id.rsplit(".",1)[0]}
targets:
  {config.app_name}:
    type: application
    platform: iOS
    deploymentTarget: "{config.deployment_target}"
    sources: [Sources]
    info:
      path: Resources/Info.plist
    settings:
      base:
        PRODUCT_BUNDLE_IDENTIFIER: {config.bundle_id}
        PRODUCT_NAME: {config.app_name}
        TARGETED_DEVICE_FAMILY: "{'1' if devices=='iPhone' else '2' if devices=='iPad' else '1,2'}"
        SWIFT_VERSION: "5.0"
        CODE_SIGN_STYLE: Automatic{team}
'''

def create_ios_project(config:IOSConfig,base:Path=Path.cwd())->Path:
    root=base/config.app_name
    if root.exists():raise FileExistsError(f"Project already exists: {root}")
    for folder in (root/"Sources",root/"Resources",root/"Scripts"):folder.mkdir(parents=True,exist_ok=True)
    (root/"project.yml").write_text(_project_yml(config),encoding="utf-8")
    with (root/"Resources"/"Info.plist").open("wb") as stream:plistlib.dump(_plist(config),stream,sort_keys=True)
    (root/"Sources"/"AppDelegate.swift").write_text(f'''import UIKit

@main
final class AppDelegate: UIResponder, UIApplicationDelegate {{
    func application(_ application: UIApplication, didFinishLaunchingWithOptions options: [UIApplication.LaunchOptionsKey: Any]? = nil) -> Bool {{ true }}
    func application(_ application: UIApplication, configurationForConnecting session: UISceneSession, options: UIScene.ConnectionOptions) -> UISceneConfiguration {{ UISceneConfiguration(name: "Default", sessionRole: session.role) }}
}}
''',encoding="utf-8")
    (root/"Sources"/"SceneDelegate.swift").write_text(f'''import UIKit

final class SceneDelegate: UIResponder, UIWindowSceneDelegate {{
    var window: UIWindow?
    func scene(_ scene: UIScene, willConnectTo session: UISceneSession, options: UIScene.ConnectionOptions) {{
        guard let scene = scene as? UIWindowScene else {{ return }}
        let controller = UIViewController()
        controller.view.backgroundColor = .systemBackground
        let label = UILabel(); label.text = "{_swift(config.app_name)}"; label.accessibilityLabel = "{_swift(config.app_name)}"
        label.translatesAutoresizingMaskIntoConstraints = false; controller.view.addSubview(label)
        NSLayoutConstraint.activate([label.centerXAnchor.constraint(equalTo: controller.view.centerXAnchor), label.centerYAnchor.constraint(equalTo: controller.view.centerYAnchor)])
        window = UIWindow(windowScene: scene); window?.rootViewController = controller; window?.makeKeyAndVisible()
    }}
}}
''',encoding="utf-8")
    (root/".gitignore").write_text("build/\nDerivedData/\n*.xcworkspace/xcuserdata/\n*.xcodeproj/xcuserdata/\n*.p12\n*.mobileprovision\n",encoding="utf-8")
    (root/"oriel-mobile.json").write_text(json.dumps({"orielVersion":"0.9.7","platform":"ios","bundleId":config.bundle_id,"version":config.version,"buildNumber":config.build_number},indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (root/"README.md").write_text(f"# {config.app_name}\n\nGenerate: `xcodegen generate`\nBuild simulator: `xcodebuild -project {config.app_name}.xcodeproj -scheme {config.app_name} -sdk iphonesimulator CODE_SIGNING_ALLOWED=NO build`\n",encoding="utf-8")
    return root

def _swift(value:str)->str:return value.replace("\\","\\\\").replace('"','\\"').replace("\n","\\n")

def validate_ios_project(project:Path,*,store_ready=False,environment:Mapping[str,str]|None=None)->list[str]:
    env=os.environ if environment is None else environment;issues=[]
    for relative in ("project.yml","Resources/Info.plist","Sources/AppDelegate.swift","Sources/SceneDelegate.swift"):
        if not (project/relative).is_file():issues.append(f"missing required iOS project file: {relative}")
    plist=project/"Resources"/"Info.plist"
    if plist.is_file():
        try:
            with plist.open("rb") as stream:value=plistlib.load(stream)
            for key in ("CFBundleIdentifier","CFBundleShortVersionString","CFBundleVersion"):
                if key not in value:issues.append(f"Info.plist missing {key}")
        except Exception as error:issues.append(f"invalid Info.plist: {error}")
    for secret in project.rglob("*"):
        if secret.is_file() and secret.suffix.lower() in {".p12",".mobileprovision"}:issues.append(f"Apple signing material must not be stored in project: {secret.relative_to(project)}")
    if store_ready:
        for name in ("ORIEL_APPLE_TEAM_ID","ORIEL_APPLE_SIGNING_IDENTITY","ORIEL_APPLE_PROVISIONING_PROFILE"):
            if not env.get(name):issues.append(f"missing Apple signing environment variable: {name}")
    return issues

@dataclass(frozen=True,slots=True)
class UnifiedMobileConfig:
    name:str
    application_id:str
    version:str="0.1.0"
    build_number:int=1
    android_min_sdk:int=24
    ios_deployment_target:str="15.0"

def create_mobile_project(config:UnifiedMobileConfig,base:Path=Path.cwd())->Path:
    root=base/config.name
    if root.exists():raise FileExistsError(f"Project already exists: {root}")
    root.mkdir(parents=True)
    create_android_project(AndroidConfig(config.application_id,config.name,config.version,config.build_number,min_sdk=config.android_min_sdk),root/"android")
    create_ios_project(IOSConfig(config.application_id,config.name,config.version,config.build_number,config.ios_deployment_target),root/"ios")
    (root/"mobile.json").write_text(json.dumps({"name":config.name,"applicationId":config.application_id,"version":config.version,"buildNumber":config.build_number,"android":"android/"+config.name,"ios":"ios/"+config.name},indent=2)+"\n",encoding="utf-8")
    (root/"README.md").write_text(f"# {config.name}\n\nUnified ORIEL 0.9.7 mobile project.\n",encoding="utf-8")
    return root

def validate_mobile_project(root:Path)->list[str]:
    try:meta=json.loads((root/"mobile.json").read_text(encoding="utf-8"))
    except Exception as error:return [f"invalid unified mobile metadata: {error}"]
    return [*validate_android_project(root/meta["android"]),*validate_ios_project(root/meta["ios"])]

@dataclass(frozen=True,slots=True)
class AppleToolchain:
    xcodebuild:str|None;xcodegen:str|None
    @property
    def available(self):return bool(self.xcodebuild and self.xcodegen)
    @classmethod
    def detect(cls):return cls(shutil.which("xcodebuild"),shutil.which("xcodegen"))

def build_ios_project(project:Path,*,archive=False,timeout=1800)->Path:
    issues=validate_ios_project(project)
    if issues:raise MobileBuildError("; ".join(issues))
    tools=AppleToolchain.detect()
    if not tools.available:raise MobileBuildError("iOS build requires macOS, Xcode, and XcodeGen")
    result=subprocess.run([tools.xcodegen,"generate"],cwd=project,text=True,capture_output=True,timeout=timeout)
    if result.returncode:raise MobileBuildError(result.stderr or result.stdout)
    name=next(line.split(":",1)[1].strip() for line in (project/"project.yml").read_text().splitlines() if line.startswith("name:"))
    derived=project/"DerivedData"
    command=[tools.xcodebuild,"-project",f"{name}.xcodeproj","-scheme",name,"-derivedDataPath",str(derived)]
    command += ["-destination","generic/platform=iOS","archive","-archivePath",str(project/"build"/f"{name}.xcarchive")] if archive else ["-sdk","iphonesimulator","-destination","generic/platform=iOS Simulator","CODE_SIGNING_ALLOWED=NO","build"]
    result=subprocess.run(command,cwd=project,text=True,capture_output=True,timeout=timeout)
    if result.returncode:raise MobileBuildError((result.stderr or result.stdout)[-5000:])
    artifact=project/"build"/f"{name}.xcarchive" if archive else derived/"Build"/"Products"/"Debug-iphonesimulator"/f"{name}.app"
    if not artifact.exists():raise MobileBuildError(f"Xcode completed but expected artifact is missing: {artifact}")
    return artifact
