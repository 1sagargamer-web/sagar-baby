# Sagar Vaani - Voice Server (Windows PC)
# Har baar chalne par GitHub se naya code leta hai, phir server + free internet link chalu karta hai.
# Ise band karne se app ki awaaz band ho jayegi.

$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Root = Join-Path $env:LOCALAPPDATA 'SagarVaani'
Set-Location $Root
try { $Host.UI.RawUI.WindowTitle = 'Sagar Vaani Server - is window ko band mat karna' } catch {}

function Say($text, $color = 'White') { Write-Host $text -ForegroundColor $color }

$cfgPath = Join-Path $Root 'config.json'
if (-not (Test-Path $cfgPath)) {
    Say 'Setup nahi mila. Pehle install wali command chalao.' Red
    Read-Host 'Enter dabao'
    return
}
$cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json
$uv = $cfg.uv
$py = Join-Path $Root 'venv\Scripts\python.exe'

Say '=============================================' Cyan
Say '        SAGAR VAANI - Voice Server' Cyan
Say '=============================================' Cyan

# ------------------------------------------------------------------ naya code
Say 'GitHub se naya code check ho raha hai...'
try {
    $ErrorActionPreference = 'Stop'
    $zip = Join-Path $Root 'code.zip'
    $tmp = Join-Path $Root 'code_tmp'
    Invoke-WebRequest 'https://github.com/1sagargamer-web/sagar-baby/archive/refs/heads/main.zip' -OutFile $zip -UseBasicParsing
    if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
    Expand-Archive $zip -DestinationPath $tmp -Force
    $src = Get-ChildItem $tmp -Directory | Select-Object -First 1
    $server = Join-Path $Root 'server'
    if (Test-Path $server) { Remove-Item $server -Recurse -Force }
    Move-Item (Join-Path $src.FullName 'voice-server') $server
    Copy-Item (Join-Path $src.FullName 'pc\run.ps1') (Join-Path $Root 'run.ps1') -Force
    Remove-Item $tmp -Recurse -Force
    Remove-Item $zip -Force
    Say 'Code updated.' Green
} catch {
    Say "Naya code nahi aaya ($($_.Exception.Message)). Purana code use hoga." Yellow
} finally {
    $ErrorActionPreference = 'Continue'
}

$server = Join-Path $Root 'server'
if (-not (Test-Path (Join-Path $server 'app.py'))) {
    Say 'Server ka code nahi mila. Internet check karke dobara chalao.' Red
    Read-Host 'Enter dabao'
    return
}

# ------------------------------------------------------------------ packages
Say 'Zaroori packages check ho rahe hain...'
& $uv pip install --python $py -r (Join-Path $server 'requirements-pc.txt') --quiet
if ($LASTEXITCODE -ne 0) {
    Say 'Packages install nahi hue. Is window ka screenshot Claude ko bhejo.' Red
    Read-Host 'Enter dabao'
    return
}

# torchaudio ka blocked native hissa hatao (Smart App Control) - pc_check isko khud karta hai
$check = (& $py (Join-Path $server 'pc_check.py') 2>&1 | Out-String)
if ($check -match 'GPU_BLOCKED') {
    Say 'GPU ki files Windows ne rok di - server CPU pe chalega (thoda dheere).' Yellow
    $env:VAANI_DEVICE = 'cpu'
}

# ------------------------------------------------------------------ settings
$env:GEMINI_API_KEY = $cfg.gemini
$env:HF_TOKEN = $cfg.hf
$env:VOICE_REPO = $cfg.voiceRepo
$env:VOICE_FILE = $cfg.voiceFile
$env:CLOUDFLARED = Join-Path $Root 'cloudflared.exe'
$env:CACHE_DIR = Join-Path $Root 'cache'
$env:HF_HOME = Join-Path $Root 'models'
$env:PORT = '7860'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUNBUFFERED = '1'
$fb = Join-Path $Root 'firebase-key.json'
if (Test-Path $fb) { $env:FIREBASE_SERVICE_ACCOUNT_FILE = $fb }

Say ''
Say 'Server chalu ho raha hai. Pehli baar AI model download hoga (~3 GB), thoda wait karo.' Green
Say 'Jab "Server ka internet link" dikhe, tab app mein awaaz chalne lagegi.' Green
Say 'Is window ko minimize kar sakte ho, par BAND MAT KARNA.' Yellow
Say ''

# ------------------------------------------------------------------ chalao (crash ho to dobara)
while ($true) {
    Push-Location $server
    & $py -m uvicorn app:app --host 127.0.0.1 --port 7860
    Pop-Location
    Say 'Server ruk gaya. 10 second mein dobara chalu ho raha hai...' Yellow
    Start-Sleep -Seconds 10
}
