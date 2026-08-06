from pathlib import Path

from oriel.android_framework import (
    AndroidConfig,
    AndroidPermission,
    create_android_project,
    validate_android_project,
)


config = AndroidConfig(
    application_id="org.oriel.example",
    app_name="OrielAndroid",
    version_name="1.0.0",
    version_code=1,
    permissions=(AndroidPermission.NOTIFICATIONS,),
)

project = create_android_project(config, Path.cwd())
issues = validate_android_project(project)
print(project)
print("ready" if not issues else "\n".join(issues))
