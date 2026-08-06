"""ORIEL 0.9.6 Android framework and packaging contracts."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Protocol
from xml.etree import ElementTree

from .ui_engine import Layout, Node, RenderTree, UIContext, validate_tree


class AndroidConfigurationError(ValueError):
    pass


class AndroidBuildError(RuntimeError):
    pass


class LifecycleState(str, Enum):
    CREATED="created"
    STARTED="started"
    RESUMED="resumed"
    PAUSED="paused"
    STOPPED="stopped"
    DESTROYED="destroyed"


_LIFECYCLE_TRANSITIONS={
    None:{LifecycleState.CREATED},
    LifecycleState.CREATED:{LifecycleState.STARTED,LifecycleState.DESTROYED},
    LifecycleState.STARTED:{LifecycleState.RESUMED,LifecycleState.STOPPED},
    LifecycleState.RESUMED:{LifecycleState.PAUSED},
    LifecycleState.PAUSED:{LifecycleState.RESUMED,LifecycleState.STOPPED},
    LifecycleState.STOPPED:{LifecycleState.STARTED,LifecycleState.DESTROYED},
    LifecycleState.DESTROYED:set(),
}


class AndroidLifecycle:
    def __init__(self)->None:
        self._state:LifecycleState|None=None
        self._observers:list[Callable[[LifecycleState],None]]=[]

    @property
    def state(self)->LifecycleState|None:return self._state

    def observe(self,observer:Callable[[LifecycleState],None])->Callable[[],None]:
        if not callable(observer):raise TypeError("lifecycle observer must be callable")
        self._observers.append(observer)
        def remove()->None:
            if observer in self._observers:self._observers.remove(observer)
        return remove

    def transition(self,state:LifecycleState)->None:
        if state not in _LIFECYCLE_TRANSITIONS[self._state]:
            current="uninitialized" if self._state is None else self._state.value
            raise RuntimeError(f"invalid Android lifecycle transition: {current} -> {state.value}")
        self._state=state
        for observer in tuple(self._observers):observer(state)


class PermissionStatus(str,Enum):
    NOT_DETERMINED="not_determined"
    GRANTED="granted"
    DENIED="denied"
    PERMANENTLY_DENIED="permanently_denied"


class AndroidPermission(str,Enum):
    CAMERA="android.permission.CAMERA"
    MICROPHONE="android.permission.RECORD_AUDIO"
    LOCATION_FINE="android.permission.ACCESS_FINE_LOCATION"
    LOCATION_COARSE="android.permission.ACCESS_COARSE_LOCATION"
    NOTIFICATIONS="android.permission.POST_NOTIFICATIONS"
    BLUETOOTH_CONNECT="android.permission.BLUETOOTH_CONNECT"
    READ_MEDIA_IMAGES="android.permission.READ_MEDIA_IMAGES"


@dataclass(frozen=True,slots=True)
class DeviceInfo:
    manufacturer:str="ORIEL"
    model:str="Mock Android Device"
    api_level:int=35
    locale:str="en-US"
    density:float=1.0
    is_emulator:bool=True
    features:frozenset[str]=frozenset()

    def __post_init__(self)->None:
        if self.api_level<21:raise ValueError("Android API level must be at least 21")
        if not self.locale:raise ValueError("device locale is required")
        if self.density<=0:raise ValueError("device density must be positive")


class AndroidDeviceBackend(Protocol):
    def device_info(self)->DeviceInfo:...
    def permission_status(self,permission:AndroidPermission)->PermissionStatus:...
    def request_permission(self,permission:AndroidPermission)->PermissionStatus:...
    def open_url(self,url:str)->bool:...
    def vibrate(self,duration_ms:int)->None:...


class MockAndroidDevice:
    def __init__(
        self,info:DeviceInfo|None=None,
        permissions:Mapping[AndroidPermission,PermissionStatus]|None=None,
        request_results:Mapping[AndroidPermission,PermissionStatus]|None=None,
    )->None:
        self.info=info or DeviceInfo()
        self.permissions=dict(permissions or {})
        self.request_results=dict(request_results or {})
        self.opened_urls:list[str]=[]
        self.vibrations:list[int]=[]

    def device_info(self)->DeviceInfo:return self.info
    def permission_status(self,permission:AndroidPermission)->PermissionStatus:
        return self.permissions.get(permission,PermissionStatus.NOT_DETERMINED)
    def request_permission(self,permission:AndroidPermission)->PermissionStatus:
        status=self.request_results.get(permission,PermissionStatus.DENIED)
        self.permissions[permission]=status
        return status
    def open_url(self,url:str)->bool:
        if not re.fullmatch(r"(?:https?|geo|tel|mailto):[^\r\n]+",url):return False
        self.opened_urls.append(url);return True
    def vibrate(self,duration_ms:int)->None:
        if not 1<=duration_ms<=60_000:raise ValueError("vibration duration must be between 1 and 60000 ms")
        self.vibrations.append(duration_ms)


class PermissionManager:
    def __init__(self,backend:AndroidDeviceBackend,declared:Iterable[AndroidPermission])->None:
        self.backend=backend;self.declared=frozenset(declared)

    def status(self,permission:AndroidPermission)->PermissionStatus:
        return self.backend.permission_status(permission)

    def request(self,permission:AndroidPermission)->PermissionStatus:
        if permission not in self.declared:
            raise PermissionError(f"permission is not declared in AndroidManifest.xml: {permission.value}")
        return self.backend.request_permission(permission)

    def require(self,permission:AndroidPermission)->None:
        if self.status(permission)!=PermissionStatus.GRANTED:
            raise PermissionError(f"Android permission required: {permission.value}")


@dataclass(frozen=True,slots=True)
class NotificationChannel:
    channel_id:str
    name:str
    importance:int=3
    description:str=""

    def __post_init__(self)->None:
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}",self.channel_id):raise ValueError("invalid notification channel id")
        if not self.name:raise ValueError("notification channel name is required")
        if not 1<=self.importance<=5:raise ValueError("notification importance must be between 1 and 5")


@dataclass(frozen=True,slots=True)
class AndroidNotification:
    notification_id:str
    channel_id:str
    title:str
    body:str
    deliver_at:float|None=None
    data:Mapping[str,str]=field(default_factory=dict)

    def __post_init__(self)->None:
        if not self.notification_id or not self.channel_id:raise ValueError("notification and channel ids are required")
        if not self.title:raise ValueError("notification title is required")
        if any(not isinstance(key,str) or not isinstance(value,str) for key,value in self.data.items()):
            raise TypeError("notification data must contain string keys and values")


class NotificationBackend(Protocol):
    def publish(self,notification:AndroidNotification)->None:...
    def cancel(self,notification_id:str)->None:...


class MemoryNotificationBackend:
    def __init__(self)->None:self.published:list[AndroidNotification]=[];self.cancelled:list[str]=[]
    def publish(self,notification:AndroidNotification)->None:self.published.append(notification)
    def cancel(self,notification_id:str)->None:self.cancelled.append(notification_id)


class NotificationManager:
    def __init__(self,backend:NotificationBackend)->None:
        self.backend=backend;self.channels:dict[str,NotificationChannel]={};self.pending:dict[str,AndroidNotification]={}
    def create_channel(self,channel:NotificationChannel)->None:self.channels[channel.channel_id]=channel
    def schedule(self,notification:AndroidNotification,*,now:float|None=None)->None:
        if notification.channel_id not in self.channels:raise KeyError(f"unknown notification channel: {notification.channel_id}")
        current=time.time() if now is None else now
        if notification.deliver_at is None or notification.deliver_at<=current:self.backend.publish(notification)
        else:self.pending[notification.notification_id]=notification
    def deliver_due(self,*,now:float|None=None)->int:
        current=time.time() if now is None else now
        due=sorted((item for item in self.pending.values() if item.deliver_at is not None and item.deliver_at<=current),key=lambda item:(item.deliver_at,item.notification_id))
        for item in due:self.backend.publish(item);self.pending.pop(item.notification_id,None)
        return len(due)
    def cancel(self,notification_id:str)->None:
        self.pending.pop(notification_id,None);self.backend.cancel(notification_id)


class NetworkRequirement(str,Enum):
    NONE="none"
    CONNECTED="connected"
    UNMETERED="unmetered"


@dataclass(frozen=True,slots=True)
class WorkConstraints:
    network:NetworkRequirement=NetworkRequirement.NONE
    requires_charging:bool=False
    requires_idle:bool=False
    battery_not_low:bool=True


@dataclass(frozen=True,slots=True)
class BackgroundWork:
    name:str
    payload:Mapping[str,Any]=field(default_factory=dict)
    constraints:WorkConstraints=field(default_factory=WorkConstraints)
    delay_seconds:float=0
    max_attempts:int=3
    backoff_seconds:float=30

    def __post_init__(self)->None:
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}",self.name):raise ValueError("invalid background work name")
        if self.delay_seconds<0 or self.backoff_seconds<=0:raise ValueError("work delays must be positive")
        if not 1<=self.max_attempts<=10:raise ValueError("max_attempts must be between 1 and 10")
        try:json.dumps(self.payload)
        except (TypeError,ValueError) as error:raise TypeError("background payload must be JSON serializable") from error


@dataclass(slots=True)
class WorkRecord:
    work_id:str
    work:BackgroundWork
    run_at:float
    attempts:int=0
    cancelled:bool=False
    completed:bool=False
    last_error:str|None=None


@dataclass(frozen=True,slots=True)
class RuntimeConditions:
    connected:bool=True
    unmetered:bool=True
    charging:bool=True
    idle:bool=True
    battery_not_low:bool=True


class BackgroundWorkManager:
    def __init__(self,handlers:Mapping[str,Callable[[Mapping[str,Any]],None]]|None=None)->None:
        self.handlers=dict(handlers or {});self.records:dict[str,WorkRecord]={}
    def register(self,name:str,handler:Callable[[Mapping[str,Any]],None])->None:
        if not callable(handler):raise TypeError("background handler must be callable")
        self.handlers[name]=handler
    def enqueue(self,work:BackgroundWork,*,now:float|None=None)->str:
        work_id=uuid.uuid4().hex
        current=time.time() if now is None else now
        self.records[work_id]=WorkRecord(work_id,work,current+work.delay_seconds)
        return work_id
    def cancel(self,work_id:str)->bool:
        record=self.records.get(work_id)
        if not record or record.completed:return False
        record.cancelled=True;return True
    @staticmethod
    def _constraints_met(work:BackgroundWork,conditions:RuntimeConditions)->bool:
        c=work.constraints
        network_ok=c.network==NetworkRequirement.NONE or (c.network==NetworkRequirement.CONNECTED and conditions.connected) or (c.network==NetworkRequirement.UNMETERED and conditions.unmetered)
        return network_ok and (not c.requires_charging or conditions.charging) and (not c.requires_idle or conditions.idle) and (not c.battery_not_low or conditions.battery_not_low)
    def run_due(self,*,now:float|None=None,conditions:RuntimeConditions=RuntimeConditions())->int:
        current=time.time() if now is None else now;executed=0
        for record in sorted(self.records.values(),key=lambda item:(item.run_at,item.work_id)):
            if record.cancelled or record.completed or record.run_at>current or not self._constraints_met(record.work,conditions):continue
            handler=self.handlers.get(record.work.name)
            if handler is None:raise KeyError(f"no background handler registered for: {record.work.name}")
            executed+=1;record.attempts+=1
            try:handler(record.work.payload);record.completed=True;record.last_error=None
            except Exception as error:
                record.last_error=f"{type(error).__name__}: {error}"
                if record.attempts>=record.work.max_attempts:record.completed=True
                else:record.run_at=current+record.work.backoff_seconds*(2**(record.attempts-1))
        return executed


@dataclass(frozen=True,slots=True)
class AndroidConfig:
    application_id:str
    app_name:str
    version_name:str="0.1.0"
    version_code:int=1
    min_sdk:int=24
    target_sdk:int=35
    compile_sdk:int=35
    permissions:tuple[AndroidPermission,...]=()
    orientation:str="unspecified"
    debuggable:bool=False

    def __post_init__(self)->None:
        if not re.fullmatch(r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*){1,}",self.application_id):
            raise AndroidConfigurationError("application_id must be a reverse-domain Android package id")
        if (
            not self.app_name.strip() or self.app_name in {".",".."}
            or any(character in self.app_name for character in '\\/:*?"<>|\r\n\x00')
            or len(self.app_name)>80
        ):raise AndroidConfigurationError("app_name is not safe for an Android project directory")
        if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?",self.version_name):
            raise AndroidConfigurationError("version_name must use semantic versioning")
        if self.version_code<1:raise AndroidConfigurationError("version_code must be positive")
        if not 21<=self.min_sdk<=self.target_sdk<=self.compile_sdk:
            raise AndroidConfigurationError("SDK levels must satisfy 21 <= min <= target <= compile")
        if self.orientation not in {"unspecified","portrait","landscape","sensor"}:
            raise AndroidConfigurationError("unsupported Android orientation")
        if len(set(self.permissions))!=len(self.permissions):raise AndroidConfigurationError("duplicate Android permissions")


class AndroidRenderer:
    platform="android"
    _VIEWS={"container":"ViewGroup","text":"TextView","button":"Button","image":"ImageView","input":"EditText","link":"TextView","heading":"TextView"}
    def render(self,node:Node,context:UIContext)->RenderTree:
        diagnostics=tuple(validate_tree(node))
        def encode(current:Node)->dict[str,Any]:
            layout=current.layout
            if current.kind=="container" and layout:
                view={"grid":"GridLayout","stack":"FrameLayout"}.get(layout.display,"LinearLayout")
            else:view=self._VIEWS.get(current.kind,"View")
            props=dict(current.props)
            if current.kind in {"text","heading"}:props["text"]=props.pop("value","")
            if current.semantics:
                props["contentDescription"]=current.semantics.label or current.semantics.hint
                props["enabled"]=current.semantics.enabled
                if current.semantics.heading_level:props["accessibilityHeading"]=True
            android_layout=None
            if layout:
                android_layout={
                    "display":layout.display,"orientation":layout.direction,"gapDp":layout.gap,
                    "paddingDp":[layout.padding.top,layout.padding.right,layout.padding.bottom,layout.padding.left],
                    "marginDp":[layout.margin.top,layout.margin.right,layout.margin.bottom,layout.margin.left],
                    "width":layout.width,"height":layout.height,"minWidth":layout.min_width,"minHeight":layout.min_height,
                    "maxWidth":layout.max_width,"maxHeight":layout.max_height,"align":layout.align,
                    "justify":layout.justify,"wrap":layout.wrap,"grow":layout.grow,"shrink":layout.shrink,
                    "gridColumns":layout.grid_columns,
                }
            return {"view":view,"key":current.key,"props":props,"layout":android_layout,"children":[encode(child) for child in current.children]}
        return RenderTree(self.platform,encode(node),diagnostics)


def _manifest(config:AndroidConfig)->str:
    permissions="\n".join(f'    <uses-permission android:name="{permission.value}" />' for permission in config.permissions)
    orientation="" if config.orientation=="unspecified" else f' android:screenOrientation="{config.orientation}"'
    return f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
{permissions}
    <application android:allowBackup="false" android:label="@string/app_name" android:theme="@style/Theme.ORIEL" android:usesCleartextTraffic="false" android:debuggable="{'true' if config.debuggable else 'false'}">
        <activity android:name=".MainActivity" android:exported="true"{orientation}>
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
'''


def _app_gradle(config:AndroidConfig)->str:
    namespace=config.application_id
    return f'''plugins {{
    id("com.android.application")
    kotlin("android")
}}

android {{
    namespace = "{namespace}"
    compileSdk = {config.compile_sdk}
    defaultConfig {{
        applicationId = "{config.application_id}"
        minSdk = {config.min_sdk}
        targetSdk = {config.target_sdk}
        versionCode = {config.version_code}
        versionName = "{config.version_name}"
    }}
    signingConfigs {{
        create("release") {{
            storeFile = System.getenv("ORIEL_ANDROID_KEYSTORE")?.let(::file)
            storePassword = System.getenv("ORIEL_ANDROID_STORE_PASSWORD")
            keyAlias = System.getenv("ORIEL_ANDROID_KEY_ALIAS")
            keyPassword = System.getenv("ORIEL_ANDROID_KEY_PASSWORD")
        }}
    }}
    buildTypes {{
        getByName("debug") {{ isDebuggable = true }}
        getByName("release") {{
            isMinifyEnabled = true
            isShrinkResources = true
            signingConfig = signingConfigs.getByName("release")
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }}
    }}
}}

dependencies {{
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")
    implementation("androidx.work:work-runtime-ktx:2.10.0")
}}
'''


def create_android_project(config:AndroidConfig,base:Path=Path.cwd())->Path:
    root=base/config.app_name
    if root.exists():raise FileExistsError(f"Project already exists: {root}")
    package_path=Path(*config.application_id.split("."))
    source=root/"app"/"src"/"main"
    kotlin=source/"java"/package_path
    for directory in (kotlin,source/"res"/"values",source/"assets",root/"gradle"/"wrapper"):directory.mkdir(parents=True,exist_ok=True)
    (root/"settings.gradle.kts").write_text('pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }\ndependencyResolutionManagement { repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS); repositories { google(); mavenCentral() } }\nrootProject.name = "'+config.app_name+'"\ninclude(":app")\n',encoding="utf-8")
    (root/"build.gradle.kts").write_text('plugins {\n    id("com.android.application") version "8.7.3" apply false\n    kotlin("android") version "2.0.21" apply false\n}\n',encoding="utf-8")
    (root/"gradle.properties").write_text("org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8\nandroid.useAndroidX=true\nkotlin.code.style=official\n",encoding="utf-8")
    (root/"app"/"build.gradle.kts").write_text(_app_gradle(config),encoding="utf-8")
    (root/"app"/"proguard-rules.pro").write_text("-keep class org.oriel.** { *; }\n",encoding="utf-8")
    (source/"AndroidManifest.xml").write_text(_manifest(config),encoding="utf-8")
    (source/"res"/"values"/"strings.xml").write_text(f'<resources>\n    <string name="app_name">{_xml_escape(config.app_name)}</string>\n</resources>\n',encoding="utf-8")
    (source/"res"/"values"/"themes.xml").write_text('<resources>\n    <style name="Theme.ORIEL" parent="Theme.MaterialComponents.DayNight.NoActionBar" />\n</resources>\n',encoding="utf-8")
    (kotlin/"MainActivity.kt").write_text(f'''package {config.application_id}

import android.os.Bundle
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {{
    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        setContentView(TextView(this).apply {{ text = "{_kotlin_escape(config.app_name)}"; contentDescription = "{_kotlin_escape(config.app_name)}" }})
    }}
}}
''',encoding="utf-8")
    metadata={"orielVersion":"0.9.6","applicationId":config.application_id,"versionName":config.version_name,"versionCode":config.version_code,"permissions":[item.value for item in config.permissions]}
    (source/"assets"/"oriel-android.json").write_text(json.dumps(metadata,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (root/".gitignore").write_text(".gradle/\nlocal.properties\n**/build/\n*.jks\n*.keystore\n",encoding="utf-8")
    (root/"README.md").write_text(f"# {config.app_name}\n\nGenerated by ORIEL 0.9.6.\n\nDebug APK: `gradle assembleDebug`\n\nRelease bundle: configure ORIEL_ANDROID_* signing variables, then run `gradle bundleRelease`.\n",encoding="utf-8")
    return root


def _xml_escape(value:str)->str:
    return value.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;").replace("'","&apos;")


def _kotlin_escape(value:str)->str:
    return value.replace("\\","\\\\").replace('"','\\"').replace("$","\\$")


def validate_android_project(project:Path,*,store_ready:bool=False,environment:Mapping[str,str]|None=None)->list[str]:
    issues:list[str]=[];env=os.environ if environment is None else environment
    required=("settings.gradle.kts","build.gradle.kts","app/build.gradle.kts","app/src/main/AndroidManifest.xml","app/src/main/res/values/strings.xml")
    for relative in required:
        if not (project/relative).is_file():issues.append(f"missing required Android project file: {relative}")
    manifest=project/"app"/"src"/"main"/"AndroidManifest.xml"
    if manifest.is_file():
        try:
            root=ElementTree.parse(manifest).getroot()
            android="{http://schemas.android.com/apk/res/android}"
            application=root.find("application")
            if application is None:issues.append("Android manifest has no application")
            else:
                if application.get(android+"debuggable")=="true" and store_ready:issues.append("store build cannot be debuggable")
                if application.get(android+"usesCleartextTraffic")!="false":issues.append("cleartext network traffic must be disabled")
            activities=root.findall("./application/activity")
            if not activities:issues.append("Android manifest has no launcher activity")
        except ElementTree.ParseError as error:issues.append(f"invalid AndroidManifest.xml: {error}")
    gradle=project/"app"/"build.gradle.kts"
    if gradle.is_file():
        content=gradle.read_text(encoding="utf-8")
        for setting in ("applicationId","versionCode","versionName","minSdk","targetSdk","compileSdk"):
            if setting not in content:issues.append(f"Gradle configuration missing {setting}")
        if store_ready:
            for variable in ("ORIEL_ANDROID_KEYSTORE","ORIEL_ANDROID_STORE_PASSWORD","ORIEL_ANDROID_KEY_ALIAS","ORIEL_ANDROID_KEY_PASSWORD"):
                if not env.get(variable):issues.append(f"missing release signing environment variable: {variable}")
    for secret in project.rglob("*"):
        if secret.is_file() and secret.suffix.lower() in {".jks",".keystore"}:issues.append(f"signing key must not be stored in the project: {secret.relative_to(project)}")
    return issues


@dataclass(frozen=True,slots=True)
class AndroidToolchain:
    java:str|None
    gradle:str|None
    adb:str|None
    sdk_root:str|None

    @property
    def available(self)->bool:return bool(self.java and self.gradle and self.sdk_root)

    @classmethod
    def detect(cls,environment:Mapping[str,str]|None=None)->"AndroidToolchain":
        env=os.environ if environment is None else environment
        return cls(shutil.which("java"),shutil.which("gradle"),shutil.which("adb"),env.get("ANDROID_SDK_ROOT") or env.get("ANDROID_HOME"))


def build_android_project(project:Path,*,bundle:bool=False,release:bool=False,timeout:int=900)->Path:
    issues=validate_android_project(project,store_ready=release)
    if issues:raise AndroidBuildError("; ".join(issues))
    toolchain=AndroidToolchain.detect()
    if not toolchain.available:raise AndroidBuildError("Android build requires Java, Gradle, and ANDROID_SDK_ROOT or ANDROID_HOME")
    task=("bundle" if bundle else "assemble")+("Release" if release else "Debug")
    command=[toolchain.gradle,task,"--no-daemon","--stacktrace"]
    result=subprocess.run(command,cwd=project,text=True,capture_output=True,timeout=timeout,check=False)
    if result.returncode:raise AndroidBuildError((result.stderr or result.stdout)[-4000:])
    pattern="*.aab" if bundle else "*.apk"
    artifacts=sorted((project/"app"/"build"/"outputs").rglob(pattern))
    if not artifacts:raise AndroidBuildError(f"Gradle completed but produced no {pattern} artifact")
    return artifacts[-1]
