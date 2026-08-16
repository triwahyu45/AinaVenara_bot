param(
    [string]$PackRoot = (Split-Path -Parent $PSScriptRoot)
)

Add-Type -AssemblyName System.Drawing

$W = 2000
$H = 1500
$bg = [System.Drawing.Color]::FromArgb(250, 252, 255)
$ink = [System.Drawing.Color]::FromArgb(25, 32, 42)
$muted = [System.Drawing.Color]::FromArgb(72, 86, 104)
$line = [System.Drawing.Color]::FromArgb(210, 220, 232)
$panel = [System.Drawing.Color]::White
$accent = [System.Drawing.Color]::FromArgb(92, 183, 230)
$cyan = [System.Drawing.Color]::FromArgb(126, 216, 242)
$mint = [System.Drawing.Color]::FromArgb(141, 230, 201)
$violet = [System.Drawing.Color]::FromArgb(126, 140, 207)
$pink = [System.Drawing.Color]::FromArgb(245, 164, 200)
$charcoal = [System.Drawing.Color]::FromArgb(59, 63, 69)

function New-Font([float]$size, [System.Drawing.FontStyle]$style = [System.Drawing.FontStyle]::Regular) {
    return [System.Drawing.Font]::new("Arial", $size, $style, [System.Drawing.GraphicsUnit]::Pixel)
}

function New-Canvas {
    $bmp = [System.Drawing.Bitmap]::new($W, $H)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.Clear($bg)
    return @($bmp, $g)
}

function Draw-Header($g, [string]$number, [string]$title, [string]$subtitle) {
    $titleFont = New-Font 35 ([System.Drawing.FontStyle]::Bold)
    $subFont = New-Font 17
    $g.DrawString("$number  AINA VENARA  |  $title", $titleFont, [System.Drawing.Brushes]::Black, 50, 30)
    $g.DrawString($subtitle, $subFont, [System.Drawing.SolidBrush]::new($muted), 52, 82)
    $g.DrawLine([System.Drawing.Pen]::new($line, 2), 50, 120, 1950, 120)
    $titleFont.Dispose()
    $subFont.Dispose()
}

function Draw-Panel($g, [int]$x, [int]$y, [int]$width, [int]$height) {
    $brush = [System.Drawing.SolidBrush]::new($panel)
    $pen = [System.Drawing.Pen]::new($line, 2)
    $g.FillRectangle($brush, $x, $y, $width, $height)
    $g.DrawRectangle($pen, $x, $y, $width, $height)
    $brush.Dispose()
    $pen.Dispose()
}

function Draw-ImageFit($g, [string]$path, [int]$x, [int]$y, [int]$width, [int]$height) {
    $img = [System.Drawing.Image]::FromFile($path)
    try {
        $scale = [Math]::Min($width / $img.Width, $height / $img.Height)
        $dw = [int]($img.Width * $scale)
        $dh = [int]($img.Height * $scale)
        $dx = $x + [int](($width - $dw) / 2)
        $dy = $y + [int](($height - $dh) / 2)
        $g.DrawImage($img, $dx, $dy, $dw, $dh)
    } finally {
        $img.Dispose()
    }
}

function Draw-Table($g, [string]$heading, [array]$rows, [int]$x, [int]$y, [int]$width, [int]$rowHeight = 29) {
    $headingFont = New-Font 19 ([System.Drawing.FontStyle]::Bold)
    $bodyFont = New-Font 15
    $smallFont = New-Font 14
    $headingBrush = [System.Drawing.SolidBrush]::new($charcoal)
    $textBrush = [System.Drawing.SolidBrush]::new($ink)
    $mutedBrush = [System.Drawing.SolidBrush]::new($muted)
    $rulePen = [System.Drawing.Pen]::new($line, 1)
    $g.DrawString($heading, $headingFont, $headingBrush, $x, $y)
    $cursorY = $y + 32
    foreach ($row in $rows) {
        $g.DrawLine($rulePen, $x, $cursorY + $rowHeight - 2, $x + $width, $cursorY + $rowHeight - 2)
        $g.DrawString($row[0], $bodyFont, $textBrush, $x, $cursorY + 4)
        $g.DrawString($row[1], $bodyFont, $textBrush, $x + [int]($width * 0.58), $cursorY + 4)
        if ($row.Count -gt 2 -and $row[2]) {
            $g.DrawString($row[2], $smallFont, $mutedBrush, $x + [int]($width * 0.76), $cursorY + 5)
        }
        $cursorY += $rowHeight
    }
    $headingFont.Dispose()
    $bodyFont.Dispose()
    $smallFont.Dispose()
    $headingBrush.Dispose()
    $textBrush.Dispose()
    $mutedBrush.Dispose()
    $rulePen.Dispose()
    return $cursorY
}

function Draw-Note($g, [string]$text, [int]$x, [int]$y, [int]$width) {
    $font = New-Font 15
    $brush = [System.Drawing.SolidBrush]::new($muted)
    $format = [System.Drawing.StringFormat]::new()
    $format.Alignment = [System.Drawing.StringAlignment]::Near
    $format.LineAlignment = [System.Drawing.StringAlignment]::Near
    $g.DrawString($text, $font, $brush, [System.Drawing.RectangleF]::new($x, $y, $width, 90), $format)
    $format.Dispose()
    $font.Dispose()
    $brush.Dispose()
}

function Draw-Footer($g) {
    $font = New-Font 14
    $bold = New-Font 14 ([System.Drawing.FontStyle]::Bold)
    $brush = [System.Drawing.SolidBrush]::new($muted)
    $g.DrawLine([System.Drawing.Pen]::new($line, 2), 50, 1425, 1950, 1425)
    $g.DrawString("CONCEPTUAL MODELING TARGETS", $bold, [System.Drawing.SolidBrush]::new($charcoal), 50, 1440)
    $g.DrawString("Use as consistent Blender / VRoid proportions. Values are design targets, not real-person measurements.", $font, $brush, 340, 1440)
    $font.Dispose()
    $bold.Dispose()
    $brush.Dispose()
}

function Save-Canvas($canvas, [string]$path) {
    $canvas[1].Dispose()
    $canvas[0].Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $canvas[0].Dispose()
}

$fullBody = Join-Path $PackRoot "05_Aina_Silhouette_Proportions.png"
$head = Join-Path $PackRoot "02_Aina_Head_Face_Detail.png"
$hairGarment = Join-Path $PackRoot "_source\generated\09_Aina_Hair_Garment_Micro_Detail_raw.png"
$handsFeet = Join-Path $PackRoot "_source\generated\10_Aina_Hands_Feet_Micro_Detail_raw.png"

$canvas = New-Canvas
$g = $canvas[1]
Draw-Header $g "07" "BODY DIMENSION SPEC" "Conceptual metric targets | petite young-adult anime VRM body | canonical height 152 cm"
Draw-Panel $g 50 145 965 1245
Draw-ImageFit $g $fullBody 70 165 925 1205
Draw-Panel $g 1040 145 910 1245
$bodyA = @(
    @("Height, barefoot", "152 cm", "LOCK"),
    @("Overall height with ahoge", "158 cm", "approx."),
    @("Target body mass", "44 kg", "concept"),
    @("Head units", "7.1 heads", "stylized"),
    @("Shoulder width", "35 cm", "bone span"),
    @("Neck circumference", "29 cm", "approx."),
    @("Bust circumference", "78 cm", "approx."),
    @("Underbust circumference", "68 cm", "approx."),
    @("Waist circumference", "58 cm", "approx."),
    @("Hip circumference", "83 cm", "approx.")
)
$bodyB = @(
    @("Upper-arm circumference", "23 cm", "approx."),
    @("Wrist circumference", "14 cm", "approx."),
    @("Thigh circumference", "46 cm", "approx."),
    @("Calf circumference", "31 cm", "approx."),
    @("Arm length: shoulder-wrist", "52 cm", "approx."),
    @("Hand length", "16.5 cm", "approx."),
    @("Inseam", "70 cm", "approx."),
    @("Leg length: hip-floor", "86 cm", "approx."),
    @("Foot length", "22.5 cm", "JP size"),
    @("Pose baseline", "Relaxed A-pose", "LOCK")
)
$next = Draw-Table $g "PRIMARY BODY TARGETS" $bodyA 1070 180 850
$next = Draw-Table $g "LIMBS + RIG BASELINE" $bodyB 1070 ($next + 28) 850
Draw-Note $g "Rig note: keep the center of mass natural and the limbs slim-relaxed. The oversized hoodie creates visual width; do not widen the torso mesh to imitate the garment silhouette." 1070 ($next + 30) 830
Draw-Footer $g
Save-Canvas $canvas (Join-Path $PackRoot "07_Aina_Body_Dimension_Spec.png")

$canvas = New-Canvas
$g = $canvas[1]
Draw-Header $g "08" "HEAD + FACE MEASUREMENTS" "Face construction targets | hairline, eyes, glasses, ears, and head-accessory placement"
Draw-Panel $g 50 145 1120 1245
Draw-ImageFit $g $head 70 165 1080 1205
Draw-Panel $g 1195 145 755 1245
$faceA = @(
    @("Head height: chin-crown", "20.0 cm", "approx."),
    @("Head circumference", "53 cm", "approx."),
    @("Face height: chin-hairline", "16.0 cm", "approx."),
    @("Head width: cheek line", "14.5 cm", "approx."),
    @("Eye width", "3.2 cm", "stylized"),
    @("Visible iris diameter", "1.8 cm", "stylized"),
    @("Interocular gap", "3.0 cm", "approx."),
    @("Ear height", "5.0 cm", "approx.")
)
$faceB = @(
    @("Glasses total width", "13.0 cm", "LOCK"),
    @("Lens outer size", "5.2 x 3.6 cm", "approx."),
    @("Bridge width", "1.4 cm", "approx."),
    @("Frame thickness", "0.20 cm", "target"),
    @("Hairclip size", "5.2 x 2.4 cm", "LOCK"),
    @("Hairclip depth", "0.40 cm", "target"),
    @("Hairclip side", "Front-left hair", "LOCK"),
    @("Blush region", "Under-eye subtle", "LOCK")
)
$next = Draw-Table $g "HEAD + FACE" $faceA 1225 185 690
$next = Draw-Table $g "GLASSES + HAIRCLIP" $faceB 1225 ($next + 32) 690
Draw-Note $g "Identity note: retain soft cheek line, large teal-green irises, thin rounded pink frames, and a restrained blush. Keep the number-3 clip readable from the front and three-quarter views." 1225 ($next + 34) 680
Draw-Footer $g
Save-Canvas $canvas (Join-Path $PackRoot "08_Aina_Head_Face_Measurements.png")

$canvas = New-Canvas
$g = $canvas[1]
Draw-Header $g "09" "HAIR + GARMENT DIMENSIONS" "Micro-detail plate | bob layers, ahoge, clip, hoodie collar, cuffs, shirt, shorts, and shoe targets"
Draw-Panel $g 50 145 1150 1245
Draw-ImageFit $g $hairGarment 70 165 1110 1205
Draw-Panel $g 1225 145 725 1245
$hairA = @(
    @("Bob crown-back length", "23 cm", "approx."),
    @("Front bang length", "13-16 cm", "range"),
    @("Side-lock length", "20 cm", "approx."),
    @("Gradient tip depth", "3-5 cm", "LOCK"),
    @("Ahoge height", "13 cm", "LOCK"),
    @("Ahoge width", "5 cm", "approx."),
    @("Hairclip size", "5.2 x 2.4 cm", "LOCK")
)
$garmentA = @(
    @("Hoodie chest circumference", "104 cm", "oversized"),
    @("Hoodie back length", "58 cm", "approx."),
    @("Dropped shoulder span", "47 cm", "approx."),
    @("Sleeve: neck seam-cuff", "67 cm", "approx."),
    @("Collar fold depth", "12 cm", "LOCK"),
    @("Cuff height", "7 cm", "approx."),
    @("Pocket opening", "13 x 2.5 cm", "approx."),
    @("Shirt body length", "56 cm", "approx."),
    @("Shorts outseam / inseam", "27 / 7 cm", "approx."),
    @("Sock shaft height", "18 cm", "approx."),
    @("Sneaker external length", "24.5 cm", "approx.")
)
$next = Draw-Table $g "HAIR CONSTRUCTION" $hairA 1255 180 660
$next = Draw-Table $g "GARMENT + FOOTWEAR" $garmentA 1255 ($next + 26) 660
Draw-Note $g "Construction note: create the bob as layered clumps with separate lower-tip material. Treat the hoodie as garment volume around a slim torso; preserve the off-shoulder charcoal collar as the signature silhouette." 1255 ($next + 28) 650
Draw-Footer $g
Save-Canvas $canvas (Join-Path $PackRoot "09_Aina_Hair_Garment_Dimensions.png")

$canvas = New-Canvas
$g = $canvas[1]
Draw-Header $g "10" "HANDS + FEET MICRO DETAIL" "Extremity reference | relaxed hand topology, ribbed socks, and simple white low-top sneakers"
Draw-Panel $g 50 145 1320 1245
Draw-ImageFit $g $handsFeet 70 165 1280 1205
Draw-Panel $g 1395 145 555 1245
$extremity = @(
    @("Hand length", "16.5 cm", "approx."),
    @("Palm width", "7.0 cm", "approx."),
    @("Finger style", "Soft tapered", ""),
    @("Foot length", "22.5 cm", "JP size"),
    @("Sneaker external length", "24.5 cm", "approx."),
    @("Sole thickness", "2.3 cm", "approx."),
    @("Sock shaft height", "18 cm", "approx."),
    @("Sock material", "White rib knit", ""),
    @("Sneaker material", "Off-white matte", ""),
    @("Lacing", "Simple white", "")
)
$next = Draw-Table $g "EXTREMITY TARGETS" $extremity 1420 190 505
Draw-Note $g "Topology note: preserve five readable fingers and a relaxed neutral pose. Footwear should remain simple and lightweight so it does not compete with the hoodie and hair silhouette." 1420 ($next + 36) 490
Draw-Footer $g
Save-Canvas $canvas (Join-Path $PackRoot "10_Aina_Hands_Feet_Micro_Detail.png")

$sheetFiles = @(
    "01_Aina_FullBody_Orthographic.png",
    "02_Aina_Head_Face_Detail.png",
    "03_Aina_Outfit_Construction.png",
    "04_Aina_Accessories_Materials.png",
    "05_Aina_Silhouette_Proportions.png",
    "06_Aina_Hair_Construction.png",
    "07_Aina_Body_Dimension_Spec.png",
    "08_Aina_Head_Face_Measurements.png",
    "09_Aina_Hair_Garment_Dimensions.png",
    "10_Aina_Hands_Feet_Micro_Detail.png"
)

$indexW = 2000
$indexH = 2200
$bmp = [System.Drawing.Bitmap]::new($indexW, $indexH)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.Clear($bg)
$titleFont = New-Font 38 ([System.Drawing.FontStyle]::Bold)
$subFont = New-Font 18
$labelFont = New-Font 18 ([System.Drawing.FontStyle]::Bold)
$g.DrawString("AINA VENARA | DETAILED 3D REFERENCE INDEX", $titleFont, [System.Drawing.Brushes]::Black, 55, 35)
$g.DrawString("Canonical VRoid / Blender modeling pack | 10 visual sheets + written metric specification", $subFont, [System.Drawing.SolidBrush]::new($muted), 58, 90)

for ($i = 0; $i -lt $sheetFiles.Count; $i++) {
    $col = $i % 2
    $row = [Math]::Floor($i / 2)
    $x = 55 + ($col * 965)
    $y = 145 + ($row * 395)
    Draw-Panel $g $x $y 925 355
    Draw-ImageFit $g (Join-Path $PackRoot $sheetFiles[$i]) ($x + 14) ($y + 14) 897 295
    $g.DrawString($sheetFiles[$i], $labelFont, [System.Drawing.SolidBrush]::new($charcoal), ($x + 16), ($y + 316))
}
$g.DrawString("All metrics are conceptual modeling targets. Canonical design lock: cyan bob + blue-violet tips / pink glasses / number-3 clip / zigzag ahoge / cyan-mint off-shoulder hoodie.", $subFont, [System.Drawing.SolidBrush]::new($muted), 58, 2140)
$g.Dispose()
$bmp.Save((Join-Path $PackRoot "Aina_Venara_3D_Reference_Index_Extended.png"), [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
