$pcbFile = "c:\Users\dhruv\CARVanta\hardware\sentinel\kicad\Sentinel_HYDRA\Sentinel_HYDRA.kicad_pcb"
$lines = [System.IO.File]::ReadAllLines($pcbFile)
Write-Output "Read $($lines.Count) lines"

# Second pass fixes — spread out remaining conflicts
$moves = [ordered]@{
    # USB area — move everything RIGHT away from J1 shield pins (extend to X=10.3)
    "R1"   = "13 42"
    "R2"   = "13 48"
    "C21"  = "13 45"
    "C10"  = "13 50"
    "C11"  = "13 47"
    "C2"   = "13 43"

    # WS2812B LEDs — 5x5mm packages need 8mm spacing
    "D1"   = "54 3"
    "D2"   = "62 3"
    "D3"   = "70 3"
    "D4"   = "78 3"
    "C60"  = "54 7"
    "C61"  = "62 7"
    "C62"  = "70 7"
    "C63"  = "78 7"

    # R5/R8 overlap — separate them
    "R5"   = "9 32"
    "R8"   = "9 35"
    "C5"   = "11 32"

    # L3/C5/SW2 cluster — spread
    "L3"   = "16 34"

    # C4 too close to L4
    "C4"   = "24 39"

    # C26/C27 overlap
    "C26"  = "26 31"
    "C27"  = "30 31"

    # C8 too close to C3
    "C3"   = "22 45"
    "C8"   = "27 45"

    # C16/C20 overlap + C12/C19 overlap
    "C16"  = "27 54"
    "C20"  = "22 54"
    "C19"  = "27 46"
    "C12"  = "22 46"

    # C1 too close to L3
    "C1"   = "12 39"

    # R10 away from J13 NPTH holes
    "R10"  = "85 11"

    # Y1 crystal — must be near U2 XIN but not ON the pads
    "Y1"   = "58 17"
    "C34"  = "55 15"
    "C35"  = "55 19"
    "R9"   = "55 21"

    # C32/C33 away from U3
    "C32"  = "73 14"
    "C33"  = "73 26"

    # LED2 too close to U6 — spread optical zone vertically
    "LED1" = "81 41"
    "LED2" = "85 41"
    "LED3" = "89 41"
    "Q3"   = "81 34"
    "Q4"   = "85 34"
    "Q5"   = "89 34"
    "R15"  = "79 32"
    "R16"  = "83 32"
    "R17"  = "87 32"
    "R18"  = "79 48"
    "R19"  = "83 48"
    "R20"  = "87 48"
    "C53"  = "90 48"

    # C57 too close to U10
    "C57"  = "62 50"
    "C58"  = "78 50"
    "C55"  = "62 31"
    "C56"  = "78 31"
    "C54"  = "52 50"

    # R7 away from SW1
    "R7"   = "16 28"

    # C13 away from J12
    "C13"  = "12 60"

    # BZ1/Q1/R24 spread
    "BZ1"  = "92 3"
    "Q1"   = "90 7"
    "R24"  = "88 9"

    # R3 away from C3
    "R3"   = "22 47"
    "R4"   = "14 42"

    # R21/R22 away from heater trace
    "R21"  = "77 74"
    "R22"  = "83 74"

    # C59 away from heater trace
    "C59"  = "88 84"

    # Q3 away from U9
    # (already moved above to 81, 34)

    # C36/R11 away from J13
    "C36"  = "80 24"
    "R11"  = "80 26"
    "R12"  = "72 26"
}

$moved = 0
$notFound = @()

foreach ($ref in $moves.Keys) {
    $coords = $moves[$ref] -split ' '
    $newX = $coords[0]
    $newY = $coords[1]
    
    $found = $false
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match "^\t\t\(property `"Reference`" `"$([regex]::Escape($ref))`"") {
            for ($j = $i - 1; $j -ge 0; $j--) {
                $tabCount = 0
                foreach ($c in $lines[$j].ToCharArray()) {
                    if ($c -eq "`t") { $tabCount++ } else { break }
                }
                $trimmed = $lines[$j].TrimStart()
                if ($tabCount -eq 2 -and $trimmed.StartsWith("(at ")) {
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
                if ($tabCount -eq 1 -and $trimmed.StartsWith("(footprint ")) { break }
            }
            if ($found) { break }
        }
    }
    if (-not $found) { $notFound += $ref }
}

Write-Output "Moved: $moved components"
if ($notFound.Count -gt 0) { Write-Output "Not found: $($notFound -join ', ')" }

[System.IO.File]::WriteAllLines($pcbFile, $lines)
Write-Output "Saved! Close and reopen KiCad, then run DRC again."
