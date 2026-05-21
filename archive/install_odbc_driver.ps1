# ODBC Driver for SQL Server ইনস্টল করার স্ক্রিপ্ট

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "ODBC Driver for SQL Server ইনস্টলার" -ForegroundColor Yellow
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

# Check if already installed
$odbcDrivers = Get-OdbcDriver -Name "*SQL Server*" -ErrorAction SilentlyContinue

if ($odbcDrivers) {
    Write-Host "✅ ODBC Driver ইতিমধ্যে ইনস্টল আছে:" -ForegroundColor Green
    $odbcDrivers | ForEach-Object { Write-Host "   - $($_.Name)" -ForegroundColor Gray }
    Write-Host ""
    Write-Host "এখন 'python read_with_localdb.py' চালান" -ForegroundColor Yellow
    exit 0
}

Write-Host "⚠️ ODBC Driver পাওয়া যায়নি" -ForegroundColor Yellow
Write-Host ""
Write-Host "ডাউনলোড করা হচ্ছে..." -ForegroundColor Cyan

# Download ODBC Driver 17
$url = "https://go.microsoft.com/fwlink/?linkid=2249004"
$output = "$env:TEMP\msodbcsql.msi"

try {
    Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing
    Write-Host "✅ ডাউনলোড সম্পন্ন!" -ForegroundColor Green
    Write-Host ""
    Write-Host "ইনস্টল করা হচ্ছে..." -ForegroundColor Cyan
    
    # Install silently
    Start-Process msiexec.exe -ArgumentList "/i `"$output`" /qn IACCEPTMSODBCSQLLICENSETERMS=YES" -Wait
    
    Write-Host "✅ ইনস্টল সম্পন্ন!" -ForegroundColor Green
    Write-Host ""
    Write-Host "এখন 'python read_with_localdb.py' চালান" -ForegroundColor Yellow
    
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "ম্যানুয়ালি ইনস্টল করুন:" -ForegroundColor Yellow
    Write-Host "1. এই লিংক থেকে ডাউনলোড করুন:" -ForegroundColor Gray
    Write-Host "   https://go.microsoft.com/fwlink/?linkid=2249004" -ForegroundColor Cyan
    Write-Host "2. ডাউনলোড হওয়া .msi ফাইল রান করুন" -ForegroundColor Gray
    Write-Host "3. তারপর 'python read_with_localdb.py' চালান" -ForegroundColor Gray
}
