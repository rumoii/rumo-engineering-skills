param(
  [string]$Repo = $env:RUMO_SKILLS_REPO,
  [string]$ProfilesRepo = "",
  [string]$CodexHome = $env:CODEX_HOME,
  [string]$ClaudeHome = $env:CLAUDE_HOME,
  [string]$AgentsHome = $env:AGENTS_HOME,
  [string]$Remote = $(if ($env:RUMO_SKILLS_REMOTE) { $env:RUMO_SKILLS_REMOTE } else { "https://github.com/rumoii/rumo-engineering-skills.git" }),
  [switch]$NoPull,
  [switch]$DryRun,
  [switch]$ReplaceForeignLinks
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ClaudeHomeExplicit = -not [string]::IsNullOrWhiteSpace($ClaudeHome)
$AgentsHomeExplicit = -not [string]::IsNullOrWhiteSpace($AgentsHome)
$ProfilesRepoExplicit = -not [string]::IsNullOrWhiteSpace($ProfilesRepo)
if (-not $ProfilesRepo) { $ProfilesRepo = $env:RUMO_SKILL_PROFILES_REPO }

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

function Get-LinkTarget {
  param([Parameter(Mandatory = $true)][System.IO.FileSystemInfo]$Item)
  $Target = if ($Item.Target -is [array]) { $Item.Target[0] } else { $Item.Target }
  if (-not $Target) { return "" }
  try {
    if ([IO.Path]::IsPathRooted([string]$Target)) { return [IO.Path]::GetFullPath([string]$Target) }
    return [IO.Path]::GetFullPath((Join-Path $Item.DirectoryName ([string]$Target)))
  }
  catch { return [string]$Target }
}

function Assert-SkillLinksSafe {
  param(
    [Parameter(Mandatory = $true)][string]$RepoSkillsPath,
    [Parameter(Mandatory = $true)][string[]]$TargetSkillsPaths
  )
  $Issues = [System.Collections.Generic.List[string]]::new()
  $SkillDirs = Get-ChildItem -Path $RepoSkillsPath -Directory | Where-Object { $_.Name -like "rumo-*" }
  foreach ($TargetSkillsPath in $TargetSkillsPaths) {
    foreach ($SkillDir in $SkillDirs) {
      $LinkPath = Join-Path $TargetSkillsPath $SkillDir.Name
      $Existing = Get-Item -LiteralPath $LinkPath -Force -ErrorAction SilentlyContinue
      if (-not $Existing) { continue }
      if ($Existing.LinkType -notin @("SymbolicLink", "Junction")) {
        $Issues.Add("$LinkPath exists as a real file or directory")
        continue
      }
      $Expected = [IO.Path]::GetFullPath($SkillDir.FullName)
      $Actual = Get-LinkTarget $Existing
      if ($Actual -and -not [StringComparer]::OrdinalIgnoreCase.Equals($Actual, $Expected) -and -not $ReplaceForeignLinks) {
        $Issues.Add("$LinkPath points to $Actual (expected $Expected); use -ReplaceForeignLinks to replace it")
      }
    }
  }
  if ($Issues.Count -gt 0) {
    throw "Skill link preflight failed; no links were changed:`n- $($Issues -join "`n- ")"
  }
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
        throw "Refusing to replace non-link skill path: $LinkPath"
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
      $Target = Get-LinkTarget $_
      $RepoPrefix = ([IO.Path]::GetFullPath($RepoSkillsPath)).TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
      if ($Target -and $Target.StartsWith($RepoPrefix, [StringComparison]::OrdinalIgnoreCase) -and -not (Test-Path $Target)) {
        $StaleLink = $_
        Invoke-Step "Remove stale link `"$($StaleLink.FullName)`"" { Remove-SkillLink $StaleLink }
      }
    }
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "Git is required." }
$ScriptRoot = $PSScriptRoot
if (-not $Repo) { $Repo = if (Test-Path (Join-Path $ScriptRoot "skills")) { $ScriptRoot } else { Join-Path $HOME ".rumo-engineering-skills" } }
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

if ($ProfilesRepoExplicit) {
  $ProfileConfig = Join-Path $Repo "skills\rumo-project-profile\scripts\profile_config.py"
  $ProfileArgs = @("--profiles-repo", $ProfilesRepo, "--dry-run")
  if (Get-Command py -ErrorAction SilentlyContinue) { & py -3 $ProfileConfig @ProfileArgs }
  elseif (Get-Command python3 -ErrorAction SilentlyContinue) { & python3 $ProfileConfig @ProfileArgs }
  elseif (Get-Command python -ErrorAction SilentlyContinue) { & python $ProfileConfig @ProfileArgs }
  else { throw "Python 3 is required to configure the profiles repository." }
  if ($LASTEXITCODE -ne 0) { throw "Profiles repository configuration failed; no skill links were changed." }
}

$SyncClaude = $ClaudeHomeExplicit -or (Get-Command claude -ErrorAction SilentlyContinue) -or (Test-Path $ClaudeHome)
$SyncAgents = $AgentsHomeExplicit -or (Get-Command grok -ErrorAction SilentlyContinue) -or (Test-Path (Join-Path $HOME ".grok"))
$TargetSkillsPaths = [System.Collections.Generic.List[string]]::new()
$TargetSkillsPaths.Add((Join-Path $CodexHome "skills"))
if ($SyncClaude) { $TargetSkillsPaths.Add((Join-Path $ClaudeHome "skills")) }
if ($SyncAgents) { $TargetSkillsPaths.Add((Join-Path $AgentsHome "skills")) }
Assert-SkillLinksSafe $RepoSkills $TargetSkillsPaths
if ($ProfilesRepoExplicit -and -not $DryRun) {
  if (Get-Command py -ErrorAction SilentlyContinue) { & py -3 $ProfileConfig --profiles-repo $ProfilesRepo }
  elseif (Get-Command python3 -ErrorAction SilentlyContinue) { & python3 $ProfileConfig --profiles-repo $ProfilesRepo }
  else { & python $ProfileConfig --profiles-repo $ProfilesRepo }
  if ($LASTEXITCODE -ne 0) { throw "Profiles repository configuration failed; no skill links were changed." }
}
foreach ($TargetSkillsPath in $TargetSkillsPaths) {
  Sync-SkillLinks $RepoSkills $TargetSkillsPath
}
if (-not $SyncClaude) { Write-Host "Claude Code was not detected; skipping." }
if (-not $SyncAgents) { Write-Host "A shared agent client was not detected; skipping." }

Write-Host "Rumo skills installation completed."
Write-Host "Repository: $Repo"
Write-Host "Recommended: set RUMO_SKILLS_REPO=$Repo"
if ($ProfilesRepo) { Write-Host "Project profiles: $ProfilesRepo" }
else { Write-Host "Optional: set RUMO_SKILL_PROFILES_REPO to a private profiles checkout." }
