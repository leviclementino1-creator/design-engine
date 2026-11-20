# design-engine / run_jsx.ps1 - the safe dispatcher to the OPEN Photoshop or Illustrator.
# Refuses unless the app is already running (the engine never launches an Adobe app), then sends ONE script over COM and
# prints the log the script wrote.
#   powershell -NoProfile -ExecutionPolicy Bypass -File run_jsx.ps1 -App ps|ai -Jsx <file> -Log <file> [-Timeout 180] [-ProgId <com id>]
# exit: 0 the log ends in "done" | 1 the script logged ERR or no "done" | 2 app not open | 3 COM unreachable | 4 script missing
param(
    [Parameter(Mandatory = $true)][ValidateSet('ps', 'ai')][string]$App,
    [Parameter(Mandatory = $true)][string]$Jsx,
    [Parameter(Mandatory = $true)][string]$Log,
    [int]$Timeout = 180,
    [string]$ProgId = ''
)
$name = 'Illustrator'; $ids = @('Illustrator.Application')
if ($App -eq 'ps') { $name = 'Photoshop'; $ids = @('Photoshop.Application', 'Photoshop.Application.BETA') }
if ($ProgId) { $ids = @($ProgId) }

if (-not (Test-Path -LiteralPath $Jsx)) { "ABORT: script not found: $Jsx"; exit 4 }
if (-not (Get-Process -Name $name -ErrorAction SilentlyContinue)) {
    "ABORT: $name is not open - open it first (the engine never launches the app)"; exit 2
}
$com = $null
foreach ($id in $ids) { try { $com = [Runtime.InteropServices.Marshal]::GetActiveObject($id); break } catch { } }
if (-not $com) { foreach ($id in $ids) { try { $com = New-Object -ComObject $id -ErrorAction Stop; break } catch { } } }
if (-not $com) { "ABORT: $name is open but did not answer over COM ($($ids -join ', '))"; exit 3 }

Remove-Item -LiteralPath $Log -ErrorAction SilentlyContinue
try { [void]$com.DoJavaScriptFile($Jsx) } catch { "COM: $($_.Exception.Message)" }

$text = ''
for ($i = 0; $i -lt $Timeout; $i++) {
    if (Test-Path -LiteralPath $Log) {
        $text = [IO.File]::ReadAllText($Log)
        if ($text -match '(?m)^(done|ERR )') { break }
    }
    Start-Sleep -Seconds 1
}
if (-not $text) { "NO LOG after ${Timeout}s (a dialog may be open in $name)"; exit 1 }
$text.TrimEnd()
if ($text -match '(?m)^ERR ' -or $text -notmatch '(?m)^done') { exit 1 }
exit 0
