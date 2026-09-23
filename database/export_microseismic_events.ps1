param(
    [string]$Source = '',
    [string]$Destination = (Join-Path $PSScriptRoot '..\public\defaults\hongyang-microseismic-events.json')
)

$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
if (-not $Source) {
    $sourceItem = Get-ChildItem -LiteralPath $repoRoot -Recurse -File -Filter '*.xls' |
        Where-Object { $_.Length -eq 123904 -and $_.FullName -notmatch '[\\/]server[\\/]uploads[\\/]' } |
        Select-Object -First 1
    if (-not $sourceItem) { throw 'Default microseismic workbook was not found.' }
    $Source = $sourceItem.FullName
}

$sourcePath = [IO.Path]::GetFullPath($Source)
$destinationPath = [IO.Path]::GetFullPath($Destination)
$excel = $null
$workbook = $null
$worksheet = $null
$usedRange = $null

try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $workbook = $excel.Workbooks.Open($sourcePath, 0, $true)
    $worksheet = $workbook.Worksheets.Item(1)
    $usedRange = $worksheet.UsedRange
    $values = $usedRange.Value2
    $events = [Collections.Generic.List[object]]::new()

    for ($row = 2; $row -le $usedRange.Rows.Count; $row += 1) {
        $x = $values[$row, 3]
        $y = $values[$row, 4]
        if ($null -eq $x -or $null -eq $y) { continue }

        $events.Add([ordered]@{
            id = 'MS-{0:D3}' -f ($events.Count + 1)
            x = [Math]::Round([double]$x, 4)
            y = [Math]::Round([double]$y, 4)
            z = [Math]::Round([double]($values[$row, 5]), 4)
            energy_j = [Math]::Round([double]($values[$row, 6]), 6)
            risk_value = [Math]::Round([double]($values[$row, 7]), 6)
        })
    }

    $xs = $events | ForEach-Object { $_.x }
    $ys = $events | ForEach-Object { $_.y }
    $payload = [ordered]@{
        meta = [ordered]@{
            source = [IO.Path]::GetFileName($sourcePath)
            event_count = $events.Count
            bounds = [ordered]@{
                xMin = ($xs | Measure-Object -Minimum).Minimum
                xMax = ($xs | Measure-Object -Maximum).Maximum
                yMin = ($ys | Measure-Object -Minimum).Minimum
                yMax = ($ys | Measure-Object -Maximum).Maximum
            }
            mapping = 'u=normalized(x), v=1-normalized(y); matches the clockwise-rotated Surfer texture'
        }
        events = $events
    }

    $json = $payload | ConvertTo-Json -Depth 5
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($destinationPath)) | Out-Null
    [IO.File]::WriteAllText($destinationPath, $json, [Text.UTF8Encoding]::new($false))
    Write-Output "Exported $($events.Count) events to $destinationPath"
}
finally {
    if ($workbook) { $workbook.Close($false) }
    if ($excel) { $excel.Quit() }
    foreach ($item in @($usedRange, $worksheet, $workbook, $excel)) {
        if ($item) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($item) }
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
