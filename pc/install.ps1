# Sagar Vaani - Voice Server setup for Windows PC
# Run in PowerShell:
#   irm https://raw.githubusercontent.com/1sagargamer-web/sagar-baby/main/pc/install.ps1 | iex
#
# Ye script:
#  1. Gemini key, Hugging Face token aur Firebase key file poochti hai (sirf pehli baar)
#  2. Python + AI model ka saaman install karti hai (NVIDIA GPU ho to GPU wala)
#  3. Free internet link (Cloudflare) ka tool laati hai
#  4. Desktop + Startup shortcut banati hai, aur server chalu kar deti hai

# 'Continue': uv/pip apni progress stderr pe likhte hain, us se script na ruke. Har step khud check hota hai.
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$RepoRaw = 'https://raw.githubusercontent.com/1sagargamer-web/sagar-baby/main'
$Root = Join-Path $env:LOCALAPPDATA 'SagarVaani'
New-Item -ItemType Directory -Force -Path $Root | Out-Null

function Say($text, $color = 'White') { Write-Host $text -ForegroundColor $color }
function Step($n, $text) { Write-Host ''; Write-Host "[$n/6] $text" -ForegroundColor Cyan }
function Fail($text) {
    Write-Host ''
    Write-Host "GADBAD: $text" -ForegroundColor Red
    Write-Host 'Is window ka screenshot Claude ko bhej do.' -ForegroundColor Yellow
    throw $text
}

Clear-Host
Say '=============================================' Cyan
Say '      SAGAR VAANI - Voice Server Setup' Cyan
Say '=============================================' Cyan
Say 'Pehli baar 10-30 minute lag sakte hain (internet speed pe depend).'
Say 'Beech mein window band mat karna.'

# ------------------------------------------------------------------ 1. Keys
Step 1 'Keys (sirf pehli baar)'
$cfgPath = Join-Path $Root 'config.json'
$old = $null
if (Test-Path $cfgPath) { $old = Get-Content $cfgPath -Raw | ConvertFrom-Json }

function Ask($label, $prefixes, $current) {
    if ($current) {
        $ans = Read-Host "$label pehle se saved hai. Badalna hai? (Enter = nahi, ya nayi value paste karo)"
        if ([string]::IsNullOrWhiteSpace($ans)) { return $current }
        return $ans.Trim()
    }
    while ($true) {
        $ans = Read-Host "$label paste karo (right-click = paste), phir Enter"
        $ans = "$ans".Trim()
        if ($ans.Length -lt 20 -or $ans.Contains(' ')) {
            Say "Ye $label nahi lag raha (bahut chhota ya beech mein space). Dobara paste karo." Yellow
            continue
        }
        $ok = $false
        foreach ($p in $prefixes) { if ($ans.StartsWith($p)) { $ok = $true } }
        if (-not $ok) { Say "Note: $label aam taur pe '$($prefixes -join "' ya '")' se shuru hota hai, par isse bhi try karte hain." Yellow }
        return $ans
    }
}

# Gemini keys: purani 'AIza...', nayi 'AQ....'
$gemini = Ask 'Gemini API key' @('AIza', 'AQ.') $(if ($old) { $old.gemini } else { $null })
$hf = Ask 'Hugging Face token' @('hf_') $(if ($old) { $old.hf } else { $null })
# keys turant save (setup beech mein ruke to dobara na poochhe)
([ordered]@{ gemini = $gemini; hf = $hf; voiceRepo = 'sagar5582/sagar-voice'; voiceFile = 'sagar.mp3' } | ConvertTo-Json) | Set-Content -Path $cfgPath -Encoding UTF8

$fbFile = Join-Path $Root 'firebase-key.json'
if (-not (Test-Path $fbFile)) {
    Say ''
    Say 'Ab Firebase ki key file chahiye (isse server ka link app mein apne aap pahunchega):' Yellow
    Say '  1) Browser mein console.firebase.google.com kholo -> sagar-vaani project'
    Say '  2) Settings (gear icon) -> Project settings -> "Service accounts" tab'
    Say '  3) "Generate new private key" -> "Generate key" dabao. Ek .json file download hogi.'
    Read-Host 'File download ho jaye to yahan Enter dabao, phir us file ko chuno'
    Add-Type -AssemblyName System.Windows.Forms
    $owner = New-Object System.Windows.Forms.Form -Property @{ TopMost = $true }
    $dlg = New-Object System.Windows.Forms.OpenFileDialog
    $dlg.Title = 'Firebase key file chuno (sagar-vaani-firebase-adminsdk-....json)'
    $dlg.Filter = 'JSON files (*.json)|*.json'
    $dlg.InitialDirectory = Join-Path $env:USERPROFILE 'Downloads'
    if ($dlg.ShowDialog($owner) -eq 'OK') {
        $txt = Get-Content $dlg.FileName -Raw
        if ($txt -notmatch '"private_key"') { Say 'Ye Firebase key file nahi lag rahi. Baad mein setup dobara chala ke de dena.' Yellow }
        else { Copy-Item $dlg.FileName $fbFile -Force; Say 'Firebase key save ho gayi.' Green }
    } else {
        Say 'Firebase file nahi chuni. Server chalega, par link app mein khud daalna padega.' Yellow
    }
    $owner.Dispose()
}

# ------------------------------------------------------------------ 2. uv (Python manager)
Step 2 'Python tool (uv) install ho raha hai'
$uv = $null
foreach ($p in @((Join-Path $env:USERPROFILE '.local\bin\uv.exe'), (Join-Path $env:USERPROFILE '.cargo\bin\uv.exe'))) {
    if (Test-Path $p) { $uv = $p }
}
if (-not $uv) {
    $c = Get-Command uv -ErrorAction SilentlyContinue
    if ($c) { $uv = $c.Source }
}
if (-not $uv) {
    powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    foreach ($p in @((Join-Path $env:USERPROFILE '.local\bin\uv.exe'), (Join-Path $env:USERPROFILE '.cargo\bin\uv.exe'))) {
        if (Test-Path $p) { $uv = $p }
    }
}
if (-not $uv) { Fail 'uv install nahi hua' }
Say "uv ready: $uv" Green

# ------------------------------------------------------------------ 3. Python + PyTorch
Step 3 'Python + AI engine (PyTorch) - ye sabse lamba step hai'

function SmartAppControlHelp {
    Write-Host ''
    Write-Host 'Windows ki "Smart App Control" setting AI ki files ko rok rahi hai.' -ForegroundColor Red
    Write-Host 'Ise theek karne ke 2 raaste hain - Claude ko ye screenshot bhejo, wo bata dega.' -ForegroundColor Yellow
    Fail 'Smart App Control ne file block ki'
}

# Official python.org Python (Microsoft isko pehchanta hai - signed hai)
$sysPy = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\python.exe'
if (-not (Test-Path $sysPy)) {
    Say 'python.org se official Python 3.11 aa raha hai...'
    $pyInst = Join-Path $env:TEMP 'python-3.11.9-amd64.exe'
    try {
        Invoke-WebRequest 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile $pyInst -UseBasicParsing -ErrorAction Stop
    } catch { Fail "Python download nahi hua: $($_.Exception.Message)" }
    $p = Start-Process $pyInst -ArgumentList '/quiet InstallAllUsers=0 PrependPath=0 Include_launcher=0 Include_test=0 Include_doc=0 Shortcuts=0' -Wait -PassThru
    Remove-Item $pyInst -Force -ErrorAction SilentlyContinue
    if (-not (Test-Path $sysPy)) { Fail "Python install nahi hua (code $($p.ExitCode))" }
}
$out = & $sysPy -c "import sys; print(sys.version)" 2>&1
if ($LASTEXITCODE -ne 0) {
    Say "$out" Red
    if ("$out" -match '4551|Application Control') { SmartAppControlHelp }
    Fail 'Python chal nahi raha'
}
Say "Python ready: $out" Green

$venv = Join-Path $Root 'venv'
$py = Join-Path $venv 'Scripts\python.exe'
$marker = Join-Path $venv 'official-python.txt'
if ((Test-Path $venv) -and -not (Test-Path $marker)) {
    # purana (block hua) venv hatao
    Remove-Item $venv -Recurse -Force -ErrorAction SilentlyContinue
}
if (-not (Test-Path $py)) {
    & $sysPy -m venv $venv
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $py)) { Fail 'Python venv nahi bana' }
    Set-Content $marker 'ok'
}

$hasNvidia = $false
try {
    if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) { $hasNvidia = $true }
    elseif (Get-CimInstance Win32_VideoController | Where-Object { $_.Name -match 'NVIDIA' }) { $hasNvidia = $true }
} catch {}

if ($hasNvidia) {
    Say 'NVIDIA graphics card mila - GPU wala (tez) version install ho raha hai.' Green
    $torchIndex = 'https://download.pytorch.org/whl/cu124'
} else {
    Say 'NVIDIA graphics card nahi mila - CPU version install ho raha hai (thoda dheere chalega).' Yellow
    $torchIndex = 'https://download.pytorch.org/whl/cpu'
}
& $uv pip install --python $py 'torch==2.6.0' 'torchaudio==2.6.0' --index-url $torchIndex
if ($LASTEXITCODE -ne 0) { Fail 'PyTorch install nahi hua' }

Say 'Baaki AI packages install ho rahe hain...'
$req = Join-Path $env:TEMP 'sagar-requirements-pc.txt'
try {
    Invoke-WebRequest "$RepoRaw/voice-server/requirements-pc.txt" -OutFile $req -UseBasicParsing -ErrorAction Stop
} catch { Fail "requirements download nahi hui: $($_.Exception.Message)" }
& $uv pip install --python $py -r $req
if ($LASTEXITCODE -ne 0) { Fail 'AI packages install nahi hue' }

Say 'Check kar raha hoon ki Windows sab files chalne de raha hai...'
$chk = Join-Path $Root 'pc_check.py'
try {
    Invoke-WebRequest "$RepoRaw/voice-server/pc_check.py" -OutFile $chk -UseBasicParsing -ErrorAction Stop
} catch { Fail "check script download nahi hui: $($_.Exception.Message)" }
$test = & $py $chk 2>&1
$testText = ($test | Out-String)
Write-Host $testText
if ($testText -notmatch 'ALL_OK') {
    if ($testText -match 'SMART_APP_CONTROL_BLOCKED') { SmartAppControlHelp }
    Fail 'AI packages load nahi hue'
}
Say 'Sab packages theek chal rahe hain.' Green

# ------------------------------------------------------------------ 4. Cloudflare tunnel tool
Step 4 'Free internet link tool (Cloudflare) aa raha hai'
$cf = Join-Path $Root 'cloudflared.exe'
if (-not (Test-Path $cf)) {
    $arch = if ([Environment]::Is64BitOperatingSystem) { 'amd64' } else { '386' }
    try {
        Invoke-WebRequest "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-$arch.exe" -OutFile $cf -UseBasicParsing -ErrorAction Stop
    } catch { Fail "Cloudflare tool download nahi hua: $($_.Exception.Message)" }
}
Say 'Cloudflare tool ready.' Green

# ------------------------------------------------------------------ 5. Save config + run script
Step 5 'Settings save ho rahi hain'
$cfg = [ordered]@{
    gemini     = $gemini
    hf         = $hf
    voiceRepo  = 'sagar5582/sagar-voice'
    voiceFile  = 'sagar.mp3'
    uv         = $uv
    gpu        = $hasNvidia
}
($cfg | ConvertTo-Json) | Set-Content -Path $cfgPath -Encoding UTF8
try {
    Invoke-WebRequest "$RepoRaw/pc/run.ps1" -OutFile (Join-Path $Root 'run.ps1') -UseBasicParsing -ErrorAction Stop
} catch { Fail "run.ps1 download nahi hua: $($_.Exception.Message)" }
Say 'Saved.' Green

# ------------------------------------------------------------------ 6. Shortcuts + start
Step 6 'Shortcut ban rahe hain'
$run = Join-Path $Root 'run.ps1'
$ws = New-Object -ComObject WScript.Shell
$targets = @(
    (Join-Path ([Environment]::GetFolderPath('Desktop')) 'Sagar Vaani Server.lnk'),
    (Join-Path ([Environment]::GetFolderPath('Startup')) 'Sagar Vaani Server.lnk')
)
foreach ($t in $targets) {
    $s = $ws.CreateShortcut($t)
    $s.TargetPath = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
    $s.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$run`""
    $s.WorkingDirectory = $Root
    $s.WindowStyle = 7
    $s.Save()
}
Say 'Desktop par "Sagar Vaani Server" shortcut ban gaya. PC on hote hi server apne aap chalu hoga.' Green

$ans = Read-Host 'Charger laga ho tab PC ko sleep na hone dein? (server chalta rahe) [Y/n]'
if ($ans -notmatch '^[nN]') {
    powercfg /change standby-timeout-ac 0 | Out-Null
    Say 'Theek hai - charger pe PC sleep nahi hoga (screen band ho sakti hai, koi baat nahi).' Green
}

Say ''
Say '=============================================' Green
Say ' Setup poora! Ab server chalu ho raha hai...' Green
Say ' Ek nayi window khulegi - use band mat karna.' Green
Say ' Pehli baar AI model download hoga (~3 GB).' Green
Say '=============================================' Green
Start-Process "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$run`""
