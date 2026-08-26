param(
  [string]$Repo = $env:RUMO_SKILLS_REPO,
  [string]$ProfilesRepo = $env:RUMO_SKILL_PROFILES_REPO,
  [string]$CodexHome = $env:CODEX_HOME,
  [string]$ClaudeHome = $env:CLAUDE_HOME,
  [string]$AgentsHome = $env:AGENTS_HOME,
  [string]$Remote = $(if ($env:RUMO_SKILLS_REMOTE) { $env:RUMO_SKILLS_REMOTE } else { "https://github.com/rumoii/rumo-engineering-skills.git" }),
  [switch]$NoPull,
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ClaudeHomeExplicit = -not [string]::IsNullOrWhiteSpace($ClaudeHome)
$AgentsHomeExplicit = -not [string]::IsNullOrWhiteSpace($AgentsHome)

function Invoke-Step {
  param([Parameter(Mandatory = $true)][string]$Display, [Parameter(Mandatory = $true)][scriptblock]$Command)
  if ($DryRun) { Write-Host "+ $Display" } else { & $Command }
}

function Invoke-SkillValidation {
  param([Parameter(Mandatory = $true)][string]$RepoPath)
  $Validator = Join-Path $RepoPath "scripts\verify_skills.py"
  if (-not (Test-Path $Validator -PathType Leaf)) { throw "Skill validator not found: $Validator" }
  if (Get-Command py -ErrorAction SilentlyContinue) { & py -3 $Validator --repo-root $RepoPath }
  elseif (Get-Command python3 -ErrorAction SilentlyContinue) { & python3 $Validator --repo-root $RepoPath }
  elseif (Get-Command python -ErrorAction SilentlyContinue) { & python $Validator --repo-root $RepoPath }
  else { throw "Python 3 is required to validate skills before installation." }
  if ($LASTEXITCODE -ne 0) { throw "Skill validation failed; no skill links were changed." }
}

function Remove-SkillLink {
  param([Parameter(Mandatory = $true)][System.IO.FileSystemInfo]$Item)
  if ($Item.LinkType -notin @("SymbolicLink", "Junction")) {
    throw "Refusing to remove a non-link skill path: $($Item.FullName)"
  }
  if ($Item.PSIsContainer) { [System.IO.Directory]::Delete($Item.FullName) }
  else { [System.IO.File]::Delete($Item.FullName) }
}

function Sync-SkillLinks {
  param([Parameter(Mandatory = $true)][string]$RepoSkillsPath, [Parameter(Mandatory = $true)][string]$TargetSkillsPath)
  Invoke-Step "New-Item -ItemType Directory -Force -Path `"$TargetSkillsPath`"" {
    New-Item -ItemType Directory -Force -Path $TargetSkillsPath | Out-Null
  }
  $SkillDirs = Get-ChildItem -Path $RepoSkillsPath -Directory | Where-Object { $_.Name -like "rumo-*" }
  foreach ($SkillDir in $SkillDirs) {
    $LinkPath = Join-Path $TargetSkillsPath $SkillDir.Name
    $Existing = Get-Item -LiteralPath $LinkPath -Force -ErrorAction SilentlyContinue
    if ($Existing) {
      if ($Existing.LinkType -notin @("SymbolicLink", "Junction")) {
        Write-Warning "Skipping $LinkPath because it exists and is not a link."
        continue
      }
      Invoke-Step "Remove link `"$LinkPath`"" { Remove-SkillLink $Existing }
    }
    Invoke-Step "New-Item -ItemType Junction -Path `"$LinkPath`" -Target `"$($SkillDir.FullName)`"" {
      New-Item -ItemType Junction -Path $LinkPath -Target $SkillDir.FullName | Out-Null
    }
  }
  Get-ChildItem -Path $TargetSkillsPath -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "rumo-*" -and $_.LinkType -in @("SymbolicLink", "Junction") } |
    ForEach-Object {
      $Target = if ($_.Target -is [array]) { $_.Target[0] } else { $_.Target }
      if ($Target -and $Target.StartsWith($RepoSkillsPath, [StringComparison]::OrdinalIgnoreCase) -and -not (Test-Path $Target)) {
        $StaleLink = $_
        Invoke-Step "Remove stale link `"$($StaleLink.FullName)`"" { Remove-SkillLink $StaleLink }
      }
    }
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "Git is required." }
$ScriptRoot = $PSScriptRoot
if (-not $Repo) { $Repo = if (Test-Path (Join-Path $ScriptRoot "skills")) { $ScriptRoot } else { Join-Path $HOME ".rumo-skills" } }
$Repo = [IO.Path]::GetFullPath($Repo)
$CodexHome = if ($CodexHome) { $CodexHome } else { Join-Path $HOME ".codex" }
$ClaudeHome = if ($ClaudeHome) { $ClaudeHome } else { Join-Path $HOME ".claude" }
$AgentsHome = if ($AgentsHome) { $AgentsHome } else { Join-Path $HOME ".agents" }

if (Test-Path (Join-Path $Repo ".git")) {
  if (-not $NoPull) {
    Invoke-Step "git -C `"$Repo`" pull --ff-only" {
      git -C $Repo pull --ff-only
      if ($LASTEXITCODE -ne 0) { throw "git pull --ff-only failed." }
    }
  }
} elseif (-not (Test-Path (Join-Path $Repo "skills"))) {
  $Parent = Split-Path -Parent $Repo
  Invoke-Step "New-Item -ItemType Directory -Force -Path `"$Parent`"" { New-Item -ItemType Directory -Force -Path $Parent | Out-Null }
  Invoke-Step "git clone `"$Remote`" `"$Repo`"" {
    git clone $Remote $Repo
    if ($LASTEXITCODE -ne 0) { throw "git clone failed." }
  }
  if ($DryRun) { Write-Host "Dry-run stopped after previewing clone."; exit 0 }
}

$RepoSkills = Join-Path $Repo "skills"
if (-not (Test-Path $RepoSkills)) { throw "Skills directory not found: $RepoSkills" }
Invoke-SkillValidation $Repo
Sync-SkillLinks $RepoSkills (Join-Path $CodexHome "skills")

$SyncClaude = $ClaudeHomeExplicit -or (Get-Command claude -ErrorAction SilentlyContinue) -or (Test-Path $ClaudeHome)
if ($SyncClaude) { Sync-SkillLinks $RepoSkills (Join-Path $ClaudeHome "skills") }
else { Write-Host "Claude Code was not detected; skipping." }

$SyncAgents = $AgentsHomeExplicit -or (Get-Command grok -ErrorAction SilentlyContinue) -or (Test-Path (Join-Path $HOME ".grok"))
if ($SyncAgents) { Sync-SkillLinks $RepoSkills (Join-Path $AgentsHome "skills") }
else { Write-Host "A shared agent client was not detected; skipping." }

Write-Host "Rumo skills installation completed."
Write-Host "Repository: $Repo"
Write-Host "Recommended: set RUMO_SKILLS_REPO=$Repo"
if ($ProfilesRepo) { Write-Host "Project profiles: $ProfilesRepo" }
else { Write-Host "Optional: set RUMO_SKILL_PROFILES_REPO to a private profiles checkout." }
