# sanatan-granth: Drive ka pul (kadam 0.7) ek baar mein.
#
# Chalane ka tareeka (PowerShell):
#   powershell -ExecutionPolicy Bypass -File E:\sanatan-granth\tools\setup\setup_drive.ps1
#
# Pehle kadam 0.6 poora ho: Google Cloud mein Desktop OAuth client bana ho (client ID aur secret haath mein).
#
# Agar laptop par pehle se koi rclone Drive remote apne OAuth client ke saath bana hai, to usi client ko
# dobara istemal karo (kuch chipkana nahin padega):
#   powershell -ExecutionPolicy Bypass -File E:\sanatan-granth\tools\setup\setup_drive.ps1 -ReuseFrom <us remote ka naam>
# Naya remote phir bhi alag hota hai aur sirf 'drive.file' scope leta hai; purana remote chhua nahin jaata.
#
# Kya hota hai:
#   1. Script client ID aur client secret poochhti hai (secret screen par nahin dikhta).
#   2. rclone remote 'granth' banta hai, sirf 'drive.file' scope ke saath. Browser mein Google login khulega.
#   3. Drive mein Sanatan_Library/ ka tree banta hai aur 06_runs/ mein ek chhoti test file likhi jaati hai.
#   4. Pehle se bane doosre remotes chhue nahin jaate.
# ID, secret aur token sirf is laptop ke rclone config mein rehte hain: na repo mein, na chat mein.
#
# Yeh file ASCII mein hai taaki Windows PowerShell 5.1 ise sahi padhe.

param([string]$ReuseFrom = "")

$ErrorActionPreference = "Stop"
$remote = "granth"
$root = "${remote}:Sanatan_Library"
$dirs = @("00_admin", "01_sources_raw", "02_canonical", "03_releases", "04_media", "05_review", "06_runs", "07_tickets/colab", "99_trash_staging")

if (-not (Get-Command rclone -ErrorAction SilentlyContinue)) { Write-Host "rclone nahin mila."; exit 1 }

$before = @(rclone listremotes)
if ($before -contains "${remote}:") {
    Write-Host "Remote '$remote' pehle se hai; naya nahin banaya. Seedhe tree aur test par ja rahe hain."
} elseif ($ReuseFrom) {
    if ($before -notcontains "${ReuseFrom}:") { Write-Host "Remote '$ReuseFrom' nahin mila."; exit 1 }
    # purane remote ke client ID/secret sirf memory mein padhe jaate hain; kuch chhapta nahin
    $id = ""; $plain = ""
    foreach ($line in @(rclone config show $ReuseFrom)) {
        if ($line -match '^client_id\s*=\s*(\S+)') { $id = $Matches[1] }
        if ($line -match '^client_secret\s*=\s*(\S+)') { $plain = $Matches[1] }
    }
    if (-not $id.EndsWith(".apps.googleusercontent.com") -or -not $plain) { Write-Host "Remote '$ReuseFrom' mein apna OAuth client nahin hai; ruk rahe hain."; exit 1 }
    try {
        Write-Host "Browser mein Google login khulega. Apna khaata chuno aur 'Allow' dabao..."
        rclone config create $remote drive "scope=drive.file" "client_id=$id" "client_secret=$plain" | Out-Null
        if ($LASTEXITCODE -ne 0) { Write-Host "rclone config create fail hua."; exit 1 }
    }
    finally { $plain = $null }
} else {
    $id = (Read-Host "Client ID chipkao (....apps.googleusercontent.com)").Trim()
    $sec = Read-Host "Client secret chipkao (dikhega nahin)" -AsSecureString
    if (-not $id.EndsWith(".apps.googleusercontent.com")) { Write-Host "Yeh client ID jaisa nahin dikhta; ruk rahe hain."; exit 1 }
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
    try {
        $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr).Trim()
        if (-not $plain) { Write-Host "Secret khaali hai; ruk rahe hain."; exit 1 }
        Write-Host "Browser mein Google login khulega. Apna khaata chuno aur 'Allow' dabao..."
        # stdout mein rclone poora config (token ke saath) chhaapta hai, isliye use phenk dete hain
        rclone config create $remote drive "scope=drive.file" "client_id=$id" "client_secret=$plain" | Out-Null
        if ($LASTEXITCODE -ne 0) { Write-Host "rclone config create fail hua."; exit 1 }
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
        $plain = $null
    }
}

Write-Host ""
Write-Host "Tree ban raha hai..."
foreach ($d in $dirs) {
    rclone mkdir "$root/$d"
    if ($LASTEXITCODE -ne 0) { Write-Host "mkdir fail: $d"; exit 1 }
    Write-Host "ok  $d"
}

$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$tmp = Join-Path $env:TEMP "sg-drive-test-$stamp.txt"
[System.IO.File]::WriteAllText($tmp, "sanatan-granth drive.file setup test $stamp`n")
try {
    rclone copyto $tmp "$root/06_runs/setup_test_$stamp.txt"
    if ($LASTEXITCODE -ne 0) { Write-Host "Test file nahin likhi ja saki."; exit 1 }
}
finally { Remove-Item $tmp -Force -ErrorAction SilentlyContinue }

Write-Host ""
Write-Host "Drive mein ab yeh hai:"
rclone lsd $root
rclone ls "$root/06_runs"

$after = @(rclone listremotes)
$lost = $before | Where-Object { $after -notcontains $_ }
if ($lost) { Write-Host ("DHYAN: yeh remotes ab nahin dikhte: " + ($lost -join ", ")) } else { Write-Host "Pehle ke saare remotes jaise the waise hain." }
Write-Host ""
Write-Host "HO GAYA. Ab Claude ko 'done' likho."
