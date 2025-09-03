$FilePath = "C:\Users\sumed\Downloads\resume.pdf"
$Url = "http://127.0.0.1:5000/upload_resume"

# Generate a boundary
$boundary = [System.Guid]::NewGuid().ToString()

# Read the file as bytes
$fileBytes = [System.IO.File]::ReadAllBytes($FilePath)
$fileEnc = [System.Text.Encoding]::GetEncoding("ISO-8859-1").GetString($fileBytes)

# Build multipart body
$bodyLines = @(
    "--$boundary",
    "Content-Disposition: form-data; name=`"file`"; filename=`"$(Split-Path $FilePath -Leaf)`"",
    "Content-Type: application/pdf",
    "",
    $fileEnc,
    "--$boundary--",
    ""
)

$body = ($bodyLines -join "`r`n")

# Headers
$headers = @{ "Content-Type" = "multipart/form-data; boundary=$boundary" }

# Send request
$response = Invoke-RestMethod -Uri $Url -Method POST -Headers $headers -Body $body

$response | ConvertTo-Json -Depth 5
