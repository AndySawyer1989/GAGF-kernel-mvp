param(
    [string]$RepositoryRoot = (Resolve-Path ".").Path,
    [string]$OutputDirectory = ".\artifacts\repository_inventory"
)

$ErrorActionPreference = "Stop"

$OutputPath = Join-Path `
    $RepositoryRoot `
    "$OutputDirectory\evidence_confidence_classification.txt"

New-Item `
    -ItemType Directory `
    -Force `
    -Path (Split-Path $OutputPath) |
Out-Null

$Patterns = @(
    "EvidenceConfidence",
    "EvidenceConfidenceAdapter",
    "build_confidence",
    "_calculate_evidence_confidence",
    "confidence_score",
    "confidence_band",
    "evidence_confidence"
)

$PythonFiles = Get-ChildItem `
    -Path $RepositoryRoot `
    -Recurse `
    -File `
    -Filter "*.py" |
Where-Object {
    $_.FullName -notmatch "\\\.venv\\" -and
    $_.FullName -notmatch "\\venv\\" -and
    $_.FullName -notmatch "\\__pycache__\\"
}

$Matches = $PythonFiles |
Select-String `
    -Pattern $Patterns `
    -SimpleMatch |
Sort-Object Path, LineNumber

function Get-CallerClassification {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $NormalizedPath = $Path.ToLowerInvariant()

    if ($NormalizedPath -match "\\tests?\\") {
        return "TEST"
    }

    if ($NormalizedPath -match "\\snapshot_ledger\.py$") {
        return "PERSISTENCE"
    }

    if ($NormalizedPath -match "\\main\.py$") {
        return "API_ORCHESTRATION"
    }

    if ($NormalizedPath -match "\\evidence_confidence_adapter\.py$") {
        return "CANONICAL_CANDIDATE"
    }

    if (
        $NormalizedPath -match "\\evidence_diagnostics_service\.py$" -or
        $NormalizedPath -match "\\evidence_quality_service\.py$" -or
        $NormalizedPath -match "\\cross_source_agreement_service\.py$" -or
        $NormalizedPath -match "\\evidence_conflict_service\.py$" -or
        $NormalizedPath -match "\\source_coverage_service\.py$"
    ) {
        return "CANONICAL_DEPENDENCY"
    }

    if ($NormalizedPath -match "\\metric_adapter\.py$") {
        return "LEGACY_LOCAL_CALCULATOR"
    }

    if ($NormalizedPath -match "\\schemas\.py$") {
        return "SHARED_SCHEMA"
    }

    if ($NormalizedPath -match "\\ingestion_service\.py$") {
        return "SERVICE_CONSUMER"
    }

    if ($NormalizedPath -match "\\dashboard_service\.py$") {
        return "PRESENTATION_CONSUMER"
    }

    return "UNCLASSIFIED"
}

$ClassifiedMatches = foreach ($Match in $Matches) {
    [PSCustomObject]@{
        Classification = Get-CallerClassification -Path $Match.Path
        Path           = $Match.Path
        LineNumber     = $Match.LineNumber
        Line           = $Match.Line.Trim()
    }
}

& {
    Write-Output "EVIDENCE CONFIDENCE CALLER CLASSIFICATION"
    Write-Output "Generated: $([DateTimeOffset]::UtcNow.ToString('o'))"
    Write-Output ""

    $ClassifiedMatches |
    Group-Object Classification |
    Sort-Object Name |
    Select-Object Name, Count

    Write-Output ""
    Write-Output "DETAILED CALLERS"
    Write-Output ("-" * 80)

    $ClassifiedMatches |
    Format-Table `
        Classification,
        Path,
        LineNumber,
        Line `
        -AutoSize `
        -Wrap
} | Out-File `
    -FilePath $OutputPath `
    -Encoding utf8 `
    -Width 500

Write-Host "Caller classification complete." -ForegroundColor Green
Write-Host $OutputPath -ForegroundColor Cyan
