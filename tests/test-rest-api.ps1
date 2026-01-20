# Test script for REST API endpoint
# Tests the /api/extract-base64 endpoint with a sample document

param(
    [string]$ServerUrl = "http://localhost:8000",
    [string]$DocumentPath = "",
    [switch]$Help
)

if ($Help) {
    Write-Host @"
Document Image Extractor - REST API Test Script

Usage:
    .\test-rest-api.ps1 -DocumentPath "C:\path\to\document.pdf"
    .\test-rest-api.ps1 -DocumentPath "C:\path\to\document.docx" -ServerUrl "http://192.168.1.100:8000"

Parameters:
    -DocumentPath   Path to PDF or DOCX document to test
    -ServerUrl      Server URL (default: http://localhost:8000)
    -Help           Show this help message

Examples:
    .\test-rest-api.ps1 -DocumentPath "C:\Documents\invoice.pdf"
    .\test-rest-api.ps1 -DocumentPath "C:\Documents\report.docx" -ServerUrl "http://10.0.0.50:8000"
"@
    exit 0
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Document Image Extractor - REST API Test" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Test 1: Health Check
Write-Host "Test 1: Health Check" -ForegroundColor Yellow
Write-Host "Endpoint: GET $ServerUrl/api/health" -ForegroundColor Gray

try {
    $healthResponse = Invoke-RestMethod -Uri "$ServerUrl/api/health" -Method GET
    Write-Host "✓ Server is healthy" -ForegroundColor Green
    Write-Host "  Service: $($healthResponse.service)" -ForegroundColor Gray
    Write-Host "  Version: $($healthResponse.version)" -ForegroundColor Gray
    Write-Host "  Status: $($healthResponse.status)`n" -ForegroundColor Gray
}
catch {
    Write-Host "✗ Health check failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`nMake sure the server is running:" -ForegroundColor Yellow
    Write-Host "  document-image-extractor-mcp`n" -ForegroundColor White
    exit 1
}

# Test 2: Document Extraction
if ($DocumentPath) {
    Write-Host "Test 2: Extract Images from Document" -ForegroundColor Yellow
    Write-Host "Document: $DocumentPath" -ForegroundColor Gray
    Write-Host "Endpoint: POST $ServerUrl/api/extract-base64`n" -ForegroundColor Gray

    if (-not (Test-Path $DocumentPath)) {
        Write-Host "✗ File not found: $DocumentPath" -ForegroundColor Red
        exit 1
    }

    $fileExtension = [System.IO.Path]::GetExtension($DocumentPath).ToLower()
    if ($fileExtension -notin @('.pdf', '.docx')) {
        Write-Host "✗ Unsupported file type: $fileExtension" -ForegroundColor Red
        Write-Host "  Supported types: .pdf, .docx" -ForegroundColor Yellow
        exit 1
    }

    Write-Host "Reading file..." -ForegroundColor Gray
    $fileContent = [System.IO.File]::ReadAllBytes($DocumentPath)
    $fileSizeMB = [math]::Round($fileContent.Length / 1MB, 2)
    Write-Host "File size: $fileSizeMB MB" -ForegroundColor Gray

    Write-Host "Encoding to base64..." -ForegroundColor Gray
    $base64String = [System.Convert]::ToBase64String($fileContent)
    $base64SizeMB = [math]::Round($base64String.Length / 1MB, 2)
    Write-Host "Base64 size: $base64SizeMB MB`n" -ForegroundColor Gray

    Write-Host "Sending request to server..." -ForegroundColor Gray
    $body = @{
        document_base64 = $base64String
        document_name = [System.IO.Path]::GetFileName($DocumentPath)
        min_image_size = 10
        return_images_as_base64 = $true
    } | ConvertTo-Json

    try {
        $response = Invoke-RestMethod -Uri "$ServerUrl/api/extract-base64" `
            -Method POST `
            -ContentType "application/json" `
            -Body $body

        Write-Host "✓ Extraction successful!`n" -ForegroundColor Green
        
        Write-Host "Results:" -ForegroundColor Cyan
        Write-Host "  Status: $($response.status)" -ForegroundColor White
        Write-Host "  Document: $($response.document_name)" -ForegroundColor White
        Write-Host "  Images Extracted: $($response.extracted_images_count)" -ForegroundColor White
        
        if ($response.extracted_images_count -gt 0) {
            Write-Host "`n  Image Files:" -ForegroundColor Cyan
            foreach ($filename in $response.image_files) {
                Write-Host "    - $filename" -ForegroundColor White
            }

            if ($response.images) {
                Write-Host "`n  Base64 Images:" -ForegroundColor Cyan
                foreach ($img in $response.images) {
                    $imgSize = [math]::Round($img.base64.Length / 1024, 2)
                    Write-Host "    - $($img.filename) ($imgSize KB)" -ForegroundColor White
                }
            }

            if ($response.zip) {
                $zipSize = [math]::Round($response.zip.base64.Length / 1024, 2)
                Write-Host "`n  ZIP Archive:" -ForegroundColor Cyan
                Write-Host "    - $($response.zip.filename) ($zipSize KB)" -ForegroundColor White
            }

            # Option to save images
            Write-Host "`nDo you want to save the extracted images? (Y/N): " -ForegroundColor Yellow -NoNewline
            $save = Read-Host
            
            if ($save -eq 'Y' -or $save -eq 'y') {
                $outputDir = Join-Path (Split-Path $DocumentPath) "extracted_images"
                New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
                
                Write-Host "Saving images to: $outputDir" -ForegroundColor Gray
                
                foreach ($img in $response.images) {
                    $imagePath = Join-Path $outputDir $img.filename
                    $imageBytes = [System.Convert]::FromBase64String($img.base64)
                    [System.IO.File]::WriteAllBytes($imagePath, $imageBytes)
                    Write-Host "  ✓ Saved: $($img.filename)" -ForegroundColor Green
                }

                if ($response.zip) {
                    $zipPath = Join-Path (Split-Path $DocumentPath) $response.zip.filename
                    $zipBytes = [System.Convert]::FromBase64String($response.zip.base64)
                    [System.IO.File]::WriteAllBytes($zipPath, $zipBytes)
                    Write-Host "  ✓ Saved: $($response.zip.filename)" -ForegroundColor Green
                }

                Write-Host "`nImages saved successfully!" -ForegroundColor Green
            }
        }
        else {
            Write-Host "`n  No images found in document." -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "✗ Extraction failed: $($_.Exception.Message)" -ForegroundColor Red
        
        if ($_.ErrorDetails.Message) {
            $errorObj = $_.ErrorDetails.Message | ConvertFrom-Json
            Write-Host "  Error details: $($errorObj.error)" -ForegroundColor Red
        }
        exit 1
    }
}
else {
    Write-Host "Test 2: Skipped (no document provided)" -ForegroundColor Yellow
    Write-Host "Use -DocumentPath to test document extraction`n" -ForegroundColor Gray
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "All tests completed!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Show usage example
if (-not $DocumentPath) {
    Write-Host "To test document extraction, run:" -ForegroundColor Yellow
    Write-Host "  .\test-rest-api.ps1 -DocumentPath `"C:\path\to\document.pdf`"`n" -ForegroundColor White
}
