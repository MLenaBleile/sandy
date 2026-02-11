# PowerShell script to rename all Reuben references to Sandy
# Run this from the project root directory

$ErrorActionPreference = "Continue"

Write-Host "=== Renaming Reuben to Sandy ===" -ForegroundColor Green

# Files to process
$filesToProcess = @(
    'src\sandwich\agent\reuben.py',
    'src\sandwich\agent\identifier.py',
    'src\sandwich\main.py',
    'src\sandwich\llm\anthropic.py',
    'src\sandwich\llm\interface.py',
    'src\sandwich\sources\wikipedia.py',
    'tests\test_reuben.py',
    'tests\test_assembler.py',
    'tests\test_pipeline.py',
    'tests\test_validator.py',
    'dashboard\app.py',
    'dashboard\components\sandwich_card.py',
    'dashboard\components\rating_widget.py',
    'dashboard\utils\queries.py',
    'dashboard\README.md',
    'README.md',
    'DEPLOYMENT.md',
    'DEPLOYMENT_CHECKLIST.md',
    'scripts\browse.py',
    'streamlit_app.py'
)

# Process each file
foreach ($file in $filesToProcess) {
    if (Test-Path $file) {
        Write-Host "Processing: $file" -ForegroundColor Cyan

        $content = Get-Content $file -Raw -ErrorAction SilentlyContinue

        if ($content) {
            # Apply replacements
            $content = $content -replace 'reuben_commentary', 'sandy_commentary'
            $content = $content -replace 'class Reuben\b', 'class Sandy'
            $content = $content -replace 'from sandwich\.agent\.reuben import Reuben', 'from sandwich.agent.sandy import Sandy'
            $content = $content -replace '\breuben = Reuben', 'sandy = Sandy'
            $content = $content -replace 'test_reuben', 'test_sandy'
            $content = $content -replace '\bReuben''s\b', 'Sandy''s'
            $content = $content -replace '"Reuben', '"Sandy'
            $content = $content -replace "'Reuben", "'Sandy"
            $content = $content -replace 'Reuben:', 'Sandy:'
            $content = $content -replace 'Reuben\.', 'Sandy.'
            $content = $content -replace '\bReuben ', 'Sandy '

            Set-Content -Path $file -Value $content -NoNewline
            Write-Host "  Updated" -ForegroundColor Green
        }
    } else {
        Write-Host "  File not found: $file" -ForegroundColor Yellow
    }
}

# Process dashboard pages with emoji names separately
Get-ChildItem -Path "dashboard\pages" -Filter "*.py" -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "Processing: dashboard\pages\$($_.Name)" -ForegroundColor Cyan
    $content = Get-Content $_.FullName -Raw
    if ($content) {
        $content = $content -replace 'reuben_commentary', 'sandy_commentary'
        $content = $content -replace '\bReuben''s\b', 'Sandy''s'
        $content = $content -replace '"Reuben', '"Sandy'
        $content = $content -replace "'Reuben", "'Sandy"
        $content = $content -replace 'Reuben:', 'Sandy:'
        $content = $content -replace 'Reuben\.', 'Sandy.'
        $content = $content -replace '\bReuben ', 'Sandy '
        Set-Content -Path $_.FullName -Value $content -NoNewline
        Write-Host "  Updated" -ForegroundColor Green
    }
}

# Process root pages with emoji names
Get-ChildItem -Path "pages" -Filter "*.py" -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "Processing: pages\$($_.Name)" -ForegroundColor Cyan
    $content = Get-Content $_.FullName -Raw
    if ($content) {
        $content = $content -replace 'reuben_commentary', 'sandy_commentary'
        $content = $content -replace '\bReuben''s\b', 'Sandy''s'
        $content = $content -replace '"Reuben', '"Sandy'
        $content = $content -replace "'Reuben", "'Sandy"
        $content = $content -replace 'Reuben:', 'Sandy:'
        $content = $content -replace 'Reuben\.', 'Sandy.'
        $content = $content -replace '\bReuben ', 'Sandy '
        Set-Content -Path $_.FullName -Value $content -NoNewline
        Write-Host "  Updated" -ForegroundColor Green
    }
}

# Rename the main agent file
if (Test-Path 'src\sandwich\agent\reuben.py') {
    Write-Host "`nRenaming src\sandwich\agent\reuben.py to sandy.py..." -ForegroundColor Cyan
    Move-Item 'src\sandwich\agent\reuben.py' 'src\sandwich\agent\sandy.py' -Force
    Write-Host "  Renamed" -ForegroundColor Green
}

# Rename test file
if (Test-Path 'tests\test_reuben.py') {
    Write-Host "Renaming tests\test_reuben.py to test_sandy.py..." -ForegroundColor Cyan
    Move-Item 'tests\test_reuben.py' 'tests\test_sandy.py' -Force
    Write-Host "  Renamed" -ForegroundColor Green
}

Write-Host "`n=== Rename Complete! ===" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Review the changes with: git diff" -ForegroundColor White
Write-Host "2. Test the application: python -m sandwich.main --max-sandwiches 1" -ForegroundColor White
Write-Host "3. Run tests: pytest tests/" -ForegroundColor White
Write-Host "4. Update any remaining manual references" -ForegroundColor White
