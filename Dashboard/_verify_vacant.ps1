$c = Get-Content 'Dashboard\data\api_data.json' -Raw
$yCount = ([regex]::Matches($c, '"vacant_status": "Y"')).Count
$nCount = ([regex]::Matches($c, '"vacant_status": "N"')).Count
$totalVac = ([regex]::Matches($c, '"vacant_status"')).Count
$isVacTrue = ([regex]::Matches($c, '"is_vacant": true')).Count
$isVacFalse = ([regex]::Matches($c, '"is_vacant": false')).Count
Write-Host "vacant_status total: $totalVac"
Write-Host "vacant_status Y: $yCount"
Write-Host "vacant_status N: $nCount"
Write-Host "is_vacant true: $isVacTrue"
Write-Host "is_vacant false: $isVacFalse"
