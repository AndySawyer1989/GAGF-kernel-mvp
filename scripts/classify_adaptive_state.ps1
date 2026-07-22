param(
    [string]$RepositoryRoot = (Resolve-Path ".").Path,
    [string]$OutputDirectory = ".\artifacts\repository_inventory"
)

$ErrorActionPreference = "Stop"

$OutputPath = Join-Path `
    $RepositoryRoot `
    "$OutputDirectory\adaptive_state_classification.txt"

New-Item `
    -ItemType Directory `
    -Force `
    -Path (Split-Path $OutputPath) |
Out-Null

$AdaptiveFields = @(
    @{
        Name = "risk_index"
        Classification = "HEURISTIC_DERIVED_INDICATOR"
        ExpectedDefault = "0.10"
        Authority = "NON_AUTHORITATIVE"
        Description = "Estimated operational risk derived from legacy event-to-delta rules."
    },
    @{
        Name = "uncertainty"
        Classification = "HEURISTIC_DERIVED_INDICATOR"
        ExpectedDefault = "0.10"
        Authority = "NON_AUTHORITATIVE"
        Description = "Estimated uncertainty derived from selected event types."
    },
    @{
        Name = "coherence_psi"
        Classification = "HEURISTIC_RESEARCH_CONSTRUCT"
        ExpectedDefault = "0.85"
        Authority = "NON_AUTHORITATIVE"
        Description = "Research construct adjusted through fixed normalization deltas."
    },
    @{
        Name = "revision_pressure"
        Classification = "HEURISTIC_RESEARCH_CONSTRUCT"
        ExpectedDefault = "0.10"
        Authority = "NON_AUTHORITATIVE"
        Description = "Research construct representing pressure to revise strategy or policy."
    },
    @{
        Name = "governance_momentum"
        Classification = "LEGACY_HEURISTIC_INDICATOR"
        ExpectedDefault = "0.50"
        Authority = "NON_AUTHORITATIVE"
        Description = "Legacy heuristic indicator; not the future scientific Governance Momentum metric."
    }
)

$KnownFieldNames = @(
    $AdaptiveFields |
    ForEach-Object {
        $_.Name
    }
)

$Patterns = @(
    "AdaptiveState",
    "risk_index",
    "uncertainty",
    "coherence_psi",
    "revision_pressure",
    "governance_momentum",
    "NORMALIZATION_DELTAS",
    "NormalizationApplied",
    "MetricAdapterResult"
)

$PythonFiles = @(
    Get-ChildItem `
        -Path $RepositoryRoot `
        -Recurse `
        -File `
        -Filter "*.py" `
        -ErrorAction SilentlyContinue |
    Where-Object {
        $_.FullName -notmatch "\\\.venv\\" -and
        $_.FullName -notmatch "\\venv\\" -and
        $_.FullName -notmatch "\\__pycache__\\"
    }
)

$CallerMatches = @(
    $PythonFiles |
    Select-String `
        -Pattern $Patterns `
        -SimpleMatch `
        -ErrorAction SilentlyContinue |
    Sort-Object Path, LineNumber
)

$FieldUsage = foreach ($Field in $AdaptiveFields) {
    $FieldMatches = @(
        $CallerMatches |
        Where-Object {
            $_.Line -like "*$($Field.Name)*"
        }
    )

    [PSCustomObject]@{
        Field = $Field.Name
        Classification = $Field.Classification
        ExpectedDefault = $Field.ExpectedDefault
        Authority = $Field.Authority
        MatchCount = $FieldMatches.Count
        Description = $Field.Description
    }
}

$SchemaFile = Join-Path `
    $RepositoryRoot `
    "backend\app\gagf\schemas.py"

$SchemaDefaults = @()

if (Test-Path $SchemaFile) {
    foreach ($Line in Get-Content $SchemaFile) {
        foreach ($FieldName in $KnownFieldNames) {
            $Pattern = "^\s*$([regex]::Escape($FieldName))\s*:\s*float\s*=\s*([-0-9.]+)"

            if ($Line -match $Pattern) {
                $SchemaDefaults += [PSCustomObject]@{
                    Field = $FieldName
                    ActualDefault = $Matches[1]
                }
            }
        }
    }
}

$DefaultVerification = foreach ($Field in $AdaptiveFields) {
    $Actual = (
        $SchemaDefaults |
        Where-Object {
            $_.Field -eq $Field.Name
        } |
        Select-Object -First 1
    )

    $ActualDefault = if ($null -eq $Actual) {
        "NOT_FOUND"
    }
    else {
        $Actual.ActualDefault
    }

    [PSCustomObject]@{
        Field = $Field.Name
        ExpectedDefault = $Field.ExpectedDefault
        ActualDefault = $ActualDefault
        MatchesExpected = (
            $ActualDefault -eq $Field.ExpectedDefault -or
            [double]$ActualDefault -eq [double]$Field.ExpectedDefault
        )
    }
}

$DefaultMismatches = @(
    $DefaultVerification |
    Where-Object {
        $_.MatchesExpected -ne $true
    }
)

$NormalizationFile = Join-Path `
    $RepositoryRoot `
    "backend\app\gagf\metric_adapter.py"

$NormalizationRules = @()

if (Test-Path $NormalizationFile) {
    $InsideRules = $false

    foreach ($Line in Get-Content $NormalizationFile) {
        if ($Line -match "^\s*NORMALIZATION_DELTAS\s*=\s*\{") {
            $InsideRules = $true
            continue
        }

        if ($InsideRules -and $Line -match "^\s*\}") {
            $InsideRules = $false
            break
        }

        if (
            $InsideRules -and
            $Line -match '^\s*"([^"]+)":\s*\("([^"]+)",\s*([-0-9.]+)\),'
        ) {
            $NormalizationRules += [PSCustomObject]@{
                EventType = $Matches[1]
                Indicator = $Matches[2]
                Delta = [double]$Matches[3]
                RuleStatus = "LEGACY_UNVERSIONED_HEURISTIC"
                Authority = "NON_AUTHORITATIVE"
            }
        }
    }
}

$UnknownIndicators = @(
    $NormalizationRules |
    Where-Object {
        $_.Indicator -notin $KnownFieldNames
    }
)

$FieldsWithoutCallers = @(
    $FieldUsage |
    Where-Object {
        $_.MatchCount -eq 0
    }
)

& {
    Write-Output "ADAPTIVE STATE EPISTEMIC CLASSIFICATION"
    Write-Output "Generated: $([DateTimeOffset]::UtcNow.ToString('o'))"
    Write-Output ""

    Write-Output "SUMMARY"
    Write-Output ("-" * 80)
    Write-Output "Python files scanned: $($PythonFiles.Count)"
    Write-Output "Caller matches found: $($CallerMatches.Count)"
    Write-Output "AdaptiveState fields classified: $($AdaptiveFields.Count)"
    Write-Output "Normalization rules found: $($NormalizationRules.Count)"
    Write-Output "Unknown rule targets: $($UnknownIndicators.Count)"
    Write-Output "Default mismatches: $($DefaultMismatches.Count)"
    Write-Output "Fields without callers: $($FieldsWithoutCallers.Count)"
    Write-Output ""

    Write-Output "GOVERNING RULE"
    Write-Output ("-" * 80)
    Write-Output "Current AdaptiveState values are legacy heuristic indicators or research constructs."
    Write-Output "They are non-authoritative and are not empirically validated constitutional metrics."
    Write-Output ""

    Write-Output "FIELD CLASSIFICATION"
    Write-Output ("-" * 80)

    $FieldUsage |
    Format-Table `
        Field,
        Classification,
        ExpectedDefault,
        Authority,
        MatchCount,
        Description `
        -AutoSize `
        -Wrap

    Write-Output ""
    Write-Output "SCHEMA DEFAULT VERIFICATION"
    Write-Output ("-" * 80)

    $DefaultVerification |
    Format-Table `
        Field,
        ExpectedDefault,
        ActualDefault,
        MatchesExpected `
        -AutoSize

    Write-Output ""
    Write-Output "NORMALIZATION RULES"
    Write-Output ("-" * 80)

    if ($NormalizationRules.Count -eq 0) {
        Write-Output "No normalization rules found."
    }
    else {
        $NormalizationRules |
        Format-Table `
            EventType,
            Indicator,
            Delta,
            RuleStatus,
            Authority `
            -AutoSize
    }

    Write-Output ""
    Write-Output "UNKNOWN RULE TARGETS"
    Write-Output ("-" * 80)

    if ($UnknownIndicators.Count -eq 0) {
        Write-Output "None"
    }
    else {
        $UnknownIndicators |
        Format-Table `
            EventType,
            Indicator,
            Delta `
            -AutoSize
    }

    Write-Output ""
    Write-Output "FIELDS WITHOUT CALLERS"
    Write-Output ("-" * 80)

    if ($FieldsWithoutCallers.Count -eq 0) {
        Write-Output "None"
    }
    else {
        $FieldsWithoutCallers |
        Format-Table `
            Field,
            Classification,
            MatchCount `
            -AutoSize
    }

    Write-Output ""
    Write-Output "DETAILED CALLERS"
    Write-Output ("-" * 80)

    $CallerMatches |
    Select-Object Path, LineNumber, Line |
    Format-Table `
        Path,
        LineNumber,
        Line `
        -AutoSize `
        -Wrap
} | Out-File `
    -FilePath $OutputPath `
    -Encoding utf8 `
    -Width 500

Write-Host ""
Write-Host "AdaptiveState classification complete." -ForegroundColor Green
Write-Host "Caller matches found: $($CallerMatches.Count)" -ForegroundColor Cyan
Write-Host "Normalization rules found: $($NormalizationRules.Count)" -ForegroundColor Cyan
Write-Host "Unknown rule targets: $($UnknownIndicators.Count)" -ForegroundColor Cyan
Write-Host "Default mismatches: $($DefaultMismatches.Count)" -ForegroundColor Cyan
Write-Host "Fields without callers: $($FieldsWithoutCallers.Count)" -ForegroundColor Cyan
Write-Host $OutputPath -ForegroundColor Cyan

if ($NormalizationRules.Count -eq 0) {
    Write-Warning "No NORMALIZATION_DELTAS entries were detected."
    exit 1
}

if ($UnknownIndicators.Count -gt 0) {
    Write-Warning "One or more normalization rules target unknown AdaptiveState fields."
    exit 1
}

if ($DefaultMismatches.Count -gt 0) {
    Write-Warning "One or more AdaptiveState defaults do not match the expected classification."
    exit 1
}

if ($FieldsWithoutCallers.Count -gt 0) {
    Write-Warning "One or more AdaptiveState fields have no detected callers."
    exit 1
}

exit 0
