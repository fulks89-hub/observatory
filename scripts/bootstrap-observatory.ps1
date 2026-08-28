param(
    [switch]$Install
)

$ErrorActionPreference = "Stop"
$UvVersion = "0.12.7"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Candidates = [System.Collections.Generic.List[string]]::new()

if ($env:OBSERVATORY_PYTHON) { $Candidates.Add($env:OBSERVATORY_PYTHON) }
foreach ($Name in @("python3.13", "python3.12", "python3", "python")) {
    $Command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($Command) { $Candidates.Add($Command.Source) }
}

$Selected = $null
foreach ($Candidate in $Candidates) {
    try {
        $Details = & $Candidate -c 'import os,sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"); print(os.path.realpath(sys.executable))'
        $Version = [version]$Details[0]
        $RealPath = $Details[1]
        if ($Version.Major -ne 3 -or $Version.Minor -lt 12) { continue }
        if ($RealPath -match '[\\/]\.venv[\\/]|[\\/]venv[\\/]|[\\/]Temp[\\/]|[\\/]work[\\/]') { continue }
        $Selected = @{ Command = $Candidate; RealPath = $RealPath; Version = $Version }
        break
    } catch { continue }
}

if (-not $Selected) {
    Write-Error @"
No safe Python 3.12+ interpreter was found.
Install from https://www.python.org/downloads/ or use
https://docs.astral.sh/uv/guides/install-python/, then rerun this script.
Do not repoint a shared symlink or borrow another project's virtual environment.
"@
}

Write-Output "status=ready"
Write-Output "python_command=$($Selected.Command)"
Write-Output "python_real_path=$($Selected.RealPath)"
Write-Output "python_version=$($Selected.Version)"
Write-Output "repository=$RepoRoot"

if (-not $Install) { exit 0 }

$VenvPython = Join-Path $RepoRoot ".venv/Scripts/python.exe"
if (Test-Path (Join-Path $RepoRoot ".venv")) {
    if (-not (Test-Path $VenvPython)) {
        throw "Existing .venv is incomplete; preserve or move it aside before retrying."
    }
    $ExistingBase = & $VenvPython -c 'import os,sys; print(os.path.realpath(sys._base_executable))'
    if ($ExistingBase -ne $Selected.RealPath) {
        throw "Existing .venv uses $ExistingBase; preserve or move it aside before rebuilding with $($Selected.RealPath)."
    }
} else {
    & $Selected.Command -m venv (Join-Path $RepoRoot ".venv")
}

& $VenvPython -m pip install --disable-pip-version-check "uv==$UvVersion"
$PreviousUvEnvironment = $env:UV_PROJECT_ENVIRONMENT
try {
    $env:UV_PROJECT_ENVIRONMENT = (Join-Path $RepoRoot ".venv")
    & $VenvPython -m uv sync --locked --extra dev --python $VenvPython
} finally {
    $env:UV_PROJECT_ENVIRONMENT = $PreviousUvEnvironment
}
& (Join-Path $RepoRoot ".venv/Scripts/observatory.exe") --help | Out-Null
& (Join-Path $RepoRoot ".venv/Scripts/observatory.exe") validate --root $RepoRoot
Write-Output "install=complete"
Write-Output "cli=$(Join-Path $RepoRoot '.venv/Scripts/observatory.exe')"
