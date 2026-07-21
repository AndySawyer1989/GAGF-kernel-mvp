param(
    [string]$RepositoryRoot = (Resolve-Path ".").Path,
    [string]$OutputDirectory = ".\artifacts\repository_inventory"
)

$ErrorActionPreference = "Stop"

$ResolvedOutputDirectory = Join-Path $RepositoryRoot $OutputDirectory

New-Item `
    -ItemType Directory `
    -Force `
    -Path $ResolvedOutputDirectory |
Out-Null

function Write-Section {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Title
    )

    Write-Output ""
    Write-Output ("=" * 80)
    Write-Output $Title
    Write-Output ("=" * 80)
}

function Get-PythonFiles {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Root
    )

    Get-ChildItem `
        -Path $Root `
        -Recurse `
        -File `
        -Filter "*.py" `
        -ErrorAction SilentlyContinue |
    Where-Object {
        $_.FullName -notmatch "\\\.venv\\" -and
        $_.FullName -notmatch "\\venv\\" -and
        $_.FullName -notmatch "\\__pycache__\\"
    }
}

$PythonFiles = @(Get-PythonFiles -Root $RepositoryRoot)

$TestFiles = @(
    $PythonFiles |
    Where-Object {
        $_.Name -like "test_*.py" -or
        $_.Name -like "*_test.py"
    } |
    Sort-Object FullName
)

$EvidencePatterns = @(
    "EvidenceConfidence",
    "EvidenceConfidenceAdapter",
    "build_confidence",
    "_calculate_evidence_confidence",
    "confidence_score",
    "confidence_band",
    "EvidenceDiagnosticsService",
    "EvidenceQualityService",
    "CrossSourceAgreementService",
    "EvidenceConflictService",
    "SourceCoverageService"
)

$AdaptiveStatePatterns = @(
    "AdaptiveState",
    "risk_index",
    "uncertainty",
    "coherence_psi",
    "revision_pressure",
    "governance_momentum",
    "NORMALIZATION_DELTAS",
    "MetricAdapter",
    "MetricAdapterResult"
)

$ConstitutionalPatterns = @(
    "CanonicalEvidenceCandidate",
    "SequenceReceipt",
    "ConstitutionalCommitRequest",
    "ConstitutionalCommitResult",
    "ReplayVerificationResult",
    "lifecycle_instance_id",
    "ordering_policy_version",
    "candidate_hash",
    "receipt_hash",
    "decision_hash",
    "resulting_state_hash"
)

$EvidenceMatches = @(
    $PythonFiles |
    Select-String `
        -Pattern $EvidencePatterns `
        -SimpleMatch `
        -ErrorAction SilentlyContinue
)

$AdaptiveStateMatches = @(
    $PythonFiles |
    Select-String `
        -Pattern $AdaptiveStatePatterns `
        -SimpleMatch `
        -ErrorAction SilentlyContinue
)

$ConstitutionalMatches = @(
    $PythonFiles |
    Select-String `
        -Pattern $ConstitutionalPatterns `
        -SimpleMatch `
        -ErrorAction SilentlyContinue
)

$ProjectFiles = @(
    Get-ChildItem `
        -Path $RepositoryRoot `
        -Recurse `
        -File `
        -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -in @(
            "pyproject.toml",
            "pytest.ini",
            "setup.cfg",
            "setup.py",
            "tox.ini",
            ".python-version"
        ) -or
        $_.Name -like "requirements*.txt"
    } |
    Sort-Object FullName
)

$SummaryPath = Join-Path $ResolvedOutputDirectory "summary.txt"
$TestFilesPath = Join-Path $ResolvedOutputDirectory "test_files.txt"
$EvidencePath = Join-Path $ResolvedOutputDirectory "evidence_confidence_callers.txt"
$AdaptiveStatePath = Join-Path $ResolvedOutputDirectory "adaptive_state_callers.txt"
$ConstitutionalPath = Join-Path $ResolvedOutputDirectory "constitutional_callers.txt"
$ProjectFilesPath = Join-Path $ResolvedOutputDirectory "project_files.txt"

& {
    Write-Section "REPOSITORY INVENTORY SUMMARY"

    Write-Output "Repository root: $RepositoryRoot"
    Write-Output "Generated at: $([DateTimeOffset]::UtcNow.ToString('o'))"
    Write-Output ""
    Write-Output "Python files: $($PythonFiles.Count)"
    Write-Output "Test files: $($TestFiles.Count)"
    Write-Output "Evidence-confidence matches: $($EvidenceMatches.Count)"
    Write-Output "AdaptiveState matches: $($AdaptiveStateMatches.Count)"
    Write-Output "Constitutional matches: $($ConstitutionalMatches.Count)"
    Write-Output "Python project files: $($ProjectFiles.Count)"

    Write-Section "GIT STATUS"

    Push-Location $RepositoryRoot

    try {
        Write-Output "Branch:"
        git branch --show-current

        Write-Output ""
        Write-Output "Working tree:"
        git status --short

        Write-Output ""
        Write-Output "Recent commits:"
        git log -5 --oneline
    }
    finally {
        Pop-Location
    }
} | Out-File `
    -FilePath $SummaryPath `
    -Encoding utf8 `
    -Width 500

& {
    Write-Section "TEST FILES"

    foreach ($File in $TestFiles) {
        Write-Output $File.FullName
    }
} | Out-File `
    -FilePath $TestFilesPath `
    -Encoding utf8 `
    -Width 500

& {
    Write-Section "EVIDENCE CONFIDENCE CALLERS"

    $EvidenceMatches |
    Sort-Object Path, LineNumber |
    Select-Object Path, LineNumber, Line
} | Out-File `
    -FilePath $EvidencePath `
    -Encoding utf8 `
    -Width 500

& {
    Write-Section "ADAPTIVE STATE CALLERS"

    $AdaptiveStateMatches |
    Sort-Object Path, LineNumber |
    Select-Object Path, LineNumber, Line
} | Out-File `
    -FilePath $AdaptiveStatePath `
    -Encoding utf8 `
    -Width 500

& {
    Write-Section "CONSTITUTIONAL CALLERS"

    $ConstitutionalMatches |
    Sort-Object Path, LineNumber |
    Select-Object Path, LineNumber, Line
} | Out-File `
    -FilePath $ConstitutionalPath `
    -Encoding utf8 `
    -Width 500

& {
    Write-Section "PYTHON PROJECT FILES"

    foreach ($File in $ProjectFiles) {
        Write-Output $File.FullName
    }
} | Out-File `
    -FilePath $ProjectFilesPath `
    -Encoding utf8 `
    -Width 500

Write-Host ""
Write-Host "Repository inventory complete." -ForegroundColor Green
Write-Host "Output directory:" -ForegroundColor Cyan
Write-Host $ResolvedOutputDirectory
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Get-Content $SummaryPath
