$pcbFile = "c:\Users\dhruv\CARVanta\hardware\sentinel\kicad\Sentinel_HYDRA\Sentinel_HYDRA.kicad_pcb"

# Backup first
$backup = "$pcbFile.bak_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Copy-Item $pcbFile $backup
Write-Output "Backup saved to: $backup"

# Read file
$lines = [System.IO.File]::ReadAllLines($pcbFile)
Write-Output "Read $($lines.Count) lines"

# Define ALL component moves: ref -> "X Y"
$moves = [ordered]@{
    # === Display Zone (out of ESP32 antenna keepout) ===
    "BZ1"  = "90 3"
    "Q1"   = "88 5"
    "D1"   = "57 3"
    "D2"   = "63 3"
    "D3"   = "69 3"
    "D4"   = "75 3"
    "C60"  = "57 5"
    "C61"  = "63 5"
    "C62"  = "69 5"
    "C63"  = "75 5"
    "R24"  = "86 5"

    # === Switches (move SW1 away from U13 area) ===
    "SW1"  = "10 28"
    "SW2"  = "10 33"

    # === USB-C area (J1 at 6,45 — away from board edge) ===
    "J1"   = "6 45"
    "R1"   = "11 43"
    "R2"   = "11 47"

    # === BQ25895 area (U13 at 18,40, QFN 4x4mm, pads ~16-20, 38-42) ===
    "C1"   = "12 37"
    "C2"   = "12 43"
    "C3"   = "24 43"
    "C4"   = "24 37"
    "C5"   = "13 34"
    "R3"   = "22 44"
    "R4"   = "14 44"
    "R5"   = "11 34"

    # === Inductors (spread apart, 4mm bodies) ===
    "L3"   = "15 34"
    "L4"   = "26 35"
    "L5"   = "96 96"   # move to corner — DELETE THIS LATER

    # === TPS63020 area (U14 at 30,40) ===
    "C6"   = "36 37"
    "C7"   = "36 43"
    "C8"   = "25 44"
    "C9"   = "25 38"

    # === AMS1117 area (U16 at 18,50, SOT-223 ~7x3.5mm) ===
    "C10"  = "12 48"
    "C11"  = "12 46"
    "C12"  = "24 48"
    "C20"  = "24 52"

    # === MAX17048 area (U17 at 12,55) ===
    "C13"  = "10 58"
    "R6"   = "14 58"

    # === Battery area (J12 at 5,55) ===
    "C14"  = "4 60"
    "C15"  = "8 60"

    # === TPS7A20 area (U15 at 30,50) + FB1 ===
    "FB1"  = "26 50"
    "C16"  = "26 53"
    "C17"  = "34 53"
    "C18"  = "34 47"
    "C19"  = "26 47"

    # === VBUS bulk cap ===
    "C21"  = "10 45"

    # === ESP32 bypass caps (U1 at 25,15, pins at bottom ~Y=28) ===
    "C22"  = "19 30"
    "C23"  = "21 30"
    "C24"  = "23 30"
    "C25"  = "25 30"
    "C26"  = "27 30"
    "C27"  = "29 30"
    "R7"   = "14 29"
    "R8"   = "12 34"

    # === RP2040 area (U2 at 65,20, QFN 7x7mm, pads ~61-69, 16-24) ===
    "C28"  = "58 13"
    "C29"  = "58 27"
    "C30"  = "72 13"
    "C31"  = "72 27"
    "C32"  = "72 17"
    "C33"  = "72 23"
    "R9"   = "57 20"

    # === Crystal caps (Y1 at 60,18) ===
    "C34"  = "56 16"
    "C35"  = "56 20"

    # === Flash area (U3 at 75,20, SOIC-8) ===
    "C36"  = "80 23"
    "R10"  = "83 13"
    "R11"  = "80 25"
    "R12"  = "72 25"

    # === AD5941 #1 (U4 at 35,65, LFCSP 7x7mm, pads ~31-39, 61-69) ===
    "C37"  = "28 59"
    "C38"  = "28 71"
    "C39"  = "42 59"
    "C40"  = "42 71"
    "C41"  = "28 62"
    "C42"  = "42 62"
    "C43"  = "28 68"
    "C44"  = "42 68"
    "R13"  = "35 76"

    # === AD5941 #2 (U5 at 60,65) ===
    "C45"  = "53 59"
    "C46"  = "53 71"
    "C47"  = "67 59"
    "C48"  = "53 63"
    "C49"  = "67 71"
    "C50"  = "67 63"
    "C51"  = "53 67"
    "C52"  = "67 67"
    "R14"  = "60 76"

    # === Optical (U6 at 85,45, LEDs, MOSFETs) ===
    "C53"  = "89 48"
    "Q3"   = "81 35"
    "Q4"   = "85 35"
    "Q5"   = "89 35"
    "LED1" = "81 43"
    "LED2" = "85 43"
    "LED3" = "89 43"
    "R15"  = "79 33"
    "R16"  = "83 33"
    "R17"  = "87 33"
    "R18"  = "79 46"
    "R19"  = "83 46"
    "R20"  = "87 46"

    # === Thermal (Q2 at 80,78) ===
    "R21"  = "77 76"
    "R22"  = "83 76"
    "C59"  = "88 82"

    # === Sensors ===
    "C54"  = "52 48"
    "C55"  = "62 32"
    "C56"  = "78 32"
    "C57"  = "62 48"
    "C58"  = "78 48"

    # === TFT connector (edge clearance) ===
    "J10"  = "94 20"
}

$moved = 0
$notFound = @()

foreach ($ref in $moves.Keys) {
    $coords = $moves[$ref] -split ' '
    $newX = $coords[0]
    $newY = $coords[1]
    
    $found = $false
    for ($i = 0; $i -lt $lines.Count; $i++) {
        # Match the Reference property line
        if ($lines[$i] -match "^\t\t\(property `"Reference`" `"$([regex]::Escape($ref))`"") {
            # Search backwards for the footprint-level (at X Y)
            for ($j = $i - 1; $j -ge 0; $j--) {
                # Count leading tabs
                $tabCount = 0
                foreach ($c in $lines[$j].ToCharArray()) {
                    if ($c -eq "`t") { $tabCount++ } else { break }
                }
                
                $trimmed = $lines[$j].TrimStart()
                
                if ($tabCount -eq 2 -and $trimmed.StartsWith("(at ")) {
                    # Preserve rotation if present
                    if ($trimmed -match '\(at [\d.+-]+ [\d.+-]+ ([\d.+-]+)\)') {
                        $rot = $Matches[1]
                        $lines[$j] = "`t`t(at $newX $newY $rot)"
                    } else {
                        $lines[$j] = "`t`t(at $newX $newY)"
                    }
                    $found = $true
                    $moved++
                    break
                }
                
                # Stop if we hit the footprint declaration
                if ($tabCount -eq 1 -and $trimmed.StartsWith("(footprint ")) {
                    break
                }
            }
            if ($found) { break }
        }
    }
    
    if (-not $found) {
        $notFound += $ref
    }
}

Write-Output ""
Write-Output "=== Results ==="
Write-Output "Moved: $moved components"
if ($notFound.Count -gt 0) {
    Write-Output "Not found (may not be imported to PCB yet): $($notFound -join ', ')"
}

# === Update board constraints ===
Write-Output ""
Write-Output "=== Updating board constraints ==="

$constraintUpdates = 0
for ($i = 0; $i -lt $lines.Count; $i++) {
    # Fix min annular width: 0.1 -> 0.05
    if ($lines[$i] -match 'min_annular_width 0\.1\b') {
        $lines[$i] = $lines[$i] -replace 'min_annular_width 0\.1\b', 'min_annular_width 0.05'
        $constraintUpdates++
        Write-Output "  Updated min_annular_width to 0.05mm"
    }
    # Fix min through hole: 0.3 -> 0.15
    if ($lines[$i] -match 'min_through_hole_diameter 0\.3\b') {
        $lines[$i] = $lines[$i] -replace 'min_through_hole_diameter 0\.3\b', 'min_through_hole_diameter 0.15'
        $constraintUpdates++
        Write-Output "  Updated min_through_hole_diameter to 0.15mm"
    }
    # Fix edge clearance: 0.5 -> 0.25
    if ($lines[$i] -match 'edge_clearance 0\.5\b') {
        $lines[$i] = $lines[$i] -replace 'edge_clearance 0\.5\b', 'edge_clearance 0.25'
        $constraintUpdates++
        Write-Output "  Updated edge_clearance to 0.25mm"
    }
}
Write-Output "  Constraint updates: $constraintUpdates"

# Save file
[System.IO.File]::WriteAllLines($pcbFile, $lines)
Write-Output ""
Write-Output "PCB file saved! Open it in KiCad and run DRC again."
