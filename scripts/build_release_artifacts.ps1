$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Release = Join-Path $Root "release-assets"
$Versions = @("0.1.0","0.2.0","0.3.0","0.4.0","0.5.0","0.6.0","0.7.0")

python -m pip install --upgrade build
python -m build --wheel --outdir (Join-Path $Release "0.1.0") (Join-Path $Root "versions\0.1.0\oriel-cli-package")
foreach ($v in $Versions | Where-Object { $_ -ne "0.1.0" }) {
    python -m build --wheel --outdir (Join-Path $Release $v) (Join-Path $Root "versions\$v")
}
python -m build --wheel --outdir (Join-Path $Release "0.8.1") $Root
Push-Location (Join-Path $Root "vscode-extension")
npm install
npx vsce package --out (Join-Path $Release "0.8.1\oriel-language-support-0.8.1.vsix")
Pop-Location
