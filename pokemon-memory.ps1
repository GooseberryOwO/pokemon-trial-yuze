param(
    [Parameter(Mandatory)][ValidatePattern('^[a-zA-Z0-9][a-zA-Z0-9_-]{0,47}$')][string]$Trial,
    [Parameter(Mandatory)][ValidateSet('1','2')][string]$Game
)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    # Scope variables to the child, without changing the caller's environment.
    & cmd.exe /d /c "set POKEMON_TRIAL_ID=$Trial&&set POKEMON_TRIAL_STAGE=$Game&&.venv\Scripts\python.exe -m agent --match --agent examples.pokemon_memory_agent"
    exit $LASTEXITCODE
} finally { Pop-Location }
