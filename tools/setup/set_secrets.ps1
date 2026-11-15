# sanatan-granth: saare GitHub secrets ek baar mein set karo.
#
# Chalane ka tareeka (PowerShell):
#   powershell -ExecutionPolicy Bypass -File E:\sanatan-granth\tools\setup\set_secrets.ps1
#
# Kya hota hai:
#   1. Ek khaali temp file Notepad mein khulti hai. Har line mein '=' ke baad apni key chipkao.
#   2. Save karke Notepad band karo.
#   3. Script bhari hui lines ko 'gh secret set -f' se GitHub secrets mein daalti hai.
#   4. FOREMAN_SHARED_SECRET khud random banakar daalti hai (agar pehle se nahin hai).
#   5. Temp file overwrite karke delete hoti hai. Keys kahin aur nahin jaatin: na repo mein, na chat mein.
#
# Yeh file ASCII mein hai taaki Windows PowerShell 5.1 ise sahi padhe.

$ErrorActionPreference = "Stop"
$repo = "manish91082-coder/sanatan-granth"
$names = @("KAGGLE_USERNAME", "KAGGLE_KEY", "GROQ_API_KEY", "CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID", "FOREMAN_DISPATCH_TOKEN")

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { Write-Host "gh CLI nahin mila."; exit 1 }

$file = Join-Path $env:TEMP ("sg-secrets-" + [guid]::NewGuid().ToString("N") + ".env")
$template = @(
    "# Har line mein = ke baad key chipkao. Jo abhi nahin hai, use khaali chhod do.",
    "# Quotes ya space mat lagao. Phir Save (Ctrl+S) karke Notepad band karo.",
    "#",
    "# KAGGLE_USERNAME, KAGGLE_KEY : kaggle.com/settings -> API -> Create New Token (kaggle.json ke andar)",
    "# GROQ_API_KEY               : console.groq.com/keys",
    "# CLOUDFLARE_API_TOKEN       : dash.cloudflare.com/profile/api-tokens (Edit Cloudflare Workers + D1 Edit)",
    "# CLOUDFLARE_ACCOUNT_ID      : Cloudflare dashboard -> Workers & Pages -> right side",
    "# FOREMAN_DISPATCH_TOKEN     : github.com/settings/personal-access-tokens/new (sirf sanatan-granth, Contents: Read and write)",
    ""
) + ($names | ForEach-Object { "$_=" })
[System.IO.File]::WriteAllLines($file, $template, (New-Object System.Text.UTF8Encoding($false)))

try {
    Write-Host "Notepad khul raha hai. Keys chipkao, Save karo, Notepad band karo..."
    Start-Process notepad.exe -ArgumentList "`"$file`"" -Wait

    $filled = @()
    foreach ($line in [System.IO.File]::ReadAllLines($file)) {
        $t = $line.Trim()
        if ($t -match '^([A-Z_]+)=(.+)$' -and ($names -contains $Matches[1])) {
            $filled += ($Matches[1] + "=" + $Matches[2].Trim())
        }
    }

    if ($filled.Count -gt 0) {
        [System.IO.File]::WriteAllLines($file, $filled, (New-Object System.Text.UTF8Encoding($false)))
        gh secret set -f $file --repo $repo
        if ($LASTEXITCODE -ne 0) { Write-Host "gh secret set fail hua." }
    } else {
        Write-Host "Koi key bhari nahin mili; kuch set nahin hua."
    }

    $existing = gh secret list --repo $repo --json name --jq ".[].name"
    if ($existing -notcontains "FOREMAN_SHARED_SECRET") {
        $bytes = New-Object byte[] 32
        [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
        $hex = -join ($bytes | ForEach-Object { $_.ToString("x2") })
        $hex | gh secret set FOREMAN_SHARED_SECRET --repo $repo
        $hex = $null
    }
}
finally {
    if (Test-Path $file) {
        $len = (Get-Item $file).Length
        [System.IO.File]::WriteAllBytes($file, (New-Object byte[] ([Math]::Max($len, 1))))
        Remove-Item $file -Force
    }
}

Write-Host ""
Write-Host "Ab GitHub mein yeh secrets hain (sirf naam; maan kisi ko nahin dikhte):"
gh secret list --repo $repo
$have = gh secret list --repo $repo --json name --jq ".[].name"
$missing = (@("GEMINI_API_KEY") + $names + @("FOREMAN_SHARED_SECRET")) | Where-Object { $have -notcontains $_ }
if ($missing) { Write-Host ("Abhi baaki: " + ($missing -join ", ")) } else { Write-Host "Saare secrets lag gaye." }
