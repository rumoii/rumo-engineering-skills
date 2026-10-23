<#
.SYNOPSIS
Validates this skills repository and links its default skills, plus any requested optional skills, into each detected agent client.

.PARAMETER Repo
Local skills repository. Defaults to RUMO_SKILLS_REPO, then this script's checkout, then ~/.rumo-engineering-skills.

.PARAMETER ProfilesRepo
Optional private project profiles repository to save in ~/.rumo-engineering-skills/config.json.

.PARAMETER CodexHome
Codex home directory. Defaults to CODEX_HOME, then ~/.codex.

.PARAMETER ClaudeHome
Claude Code home directory. Defaults to CLAUDE_HOME, then ~/.claude.

.PARAMETER AgentsHome
Shared agent skills home directory. Defaults to AGENTS_HOME, then ~/.agents.

.PARAMETER Remote
Clone URL used when the repository is absent. Defaults to RUMO_SKILLS_REMOTE.

.PARAMETER Extras
Also install these optional skills, for example rumo-diagram,rumo-document-writing.

.PARAMETER RemoveExtras
Remove these optional skills.

.PARAMETER ListExtras
List optional skills without changing anything.

.PARAMETER NoPull
Do not update an existing checkout.

.PARAMETER DryRun
Print operations without changing links.

.PARAMETER ReplaceForeignLinks
Replace same-name links that point into another repository.

.PARAMETER Baseline
Add the always-on baseline block to CLAUDE.md and AGENTS.md of each detected Claude Code and Codex home. Later runs keep it current.

.PARAMETER RemoveBaseline
Remove the always-on baseline block from those files.

.PARAMETER Uninstall
Remove every rumo-* link that points into this repository from each detected client, and the baseline block. Keeps the repository, its configuration, and project profiles.

.PARAMETER Help
Print this help and exit without checking or changing anything.

.EXAMPLE
.\install.ps1 -NoPull

.EXAMPLE
.\install.ps1 -NoPull -ListExtras

.EXAMPLE
.\install.ps1 -NoPull -Extras rumo-diagram,rumo-document-writing

.EXAMPLE
.\install.ps1 -NoPull -Baseline

.EXAMPLE
.\install.ps1 -Uninstall -DryRun
#>
# Named parameters only: a stray word such as --help must fail instead of becoming -Repo.
[CmdletBinding(PositionalBinding = $false)]
param(
  [string]$Repo = $env:RUMO_SKILLS_REPO,
  [string]$ProfilesRepo = "",
  [string]$CodexHome = $env:CODEX_HOME,
  [string]$ClaudeHome = $env:CLAUDE_HOME,
  [string]$AgentsHome = $env:AGENTS_HOME,
  [string]$Remote = $(if ($env:RUMO_SKILLS_REMOTE) { $env:RUMO_SKILLS_REMOTE } else { "https://github.com/rumoii/rumo-engineering-skills.git" }),
  [string[]]$Extras = @(),
  [string[]]$RemoveExtras = @(),
  [switch]$ListExtras,
  [switch]$NoPull,
  [switch]$DryRun,
  [switch]$ReplaceForeignLinks,
  [switch]$Baseline,
  [switch]$RemoveBaseline,
  [switch]$Uninstall,
  [Alias("h")][switch]$Help
)

if ($Help) {
  Get-Help $PSCommandPath -Detailed | Out-String -Width 120 | Write-Host
  exit 0
}

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$CodexHomeExplicit = -not [string]::IsNullOrWhiteSpace($CodexHome)
$ClaudeHomeExplicit = -not [string]::IsNullOrWhiteSpace($ClaudeHome)
$AgentsHomeExplicit = -not [string]::IsNullOrWhiteSpace($AgentsHome)
$ProfilesRepoExplicit = -not [string]::IsNullOrWhiteSpace($ProfilesRepo)
if (-not $ProfilesRepo) { $ProfilesRepo = $env:RUMO_SKILL_PROFILES_REPO }
$PythonInstallHint = "Install Python 3 (Windows: winget install --id Python.Python.3.12; macOS or Linux: your package manager), then rerun."

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
  else { throw "Python 3 is required to validate skills before installation. $PythonInstallHint No skill links were changed." }
  if ($LASTEXITCODE -ne 0) { throw "Skill validation failed; no skill links were changed." }
}

function Sync-BaselineBlock {
  param([Parameter(Mandatory = $true)][string]$Target, [Parameter(Mandatory = $true)][string]$Mode)
  if (-not (Test-Path $BaselineScript -PathType Leaf)) { return "skipped" }
  $Arguments = @($BaselineScript, "--target", $Target, "--$Mode")
  if ($DryRun) { $Arguments += "--dry-run" }
  if (Get-Command py -ErrorAction SilentlyContinue) { $Output = & py -3 @Arguments }
  elseif (Get-Command python3 -ErrorAction SilentlyContinue) { $Output = & python3 @Arguments }
  else { $Output = & python @Arguments }
  if ($LASTEXITCODE -ne 0) { throw "Baseline block update failed for $Target; skill links were already synced." }
  $Action = "$Output".Trim()
  if ($Action -in @("added", "updated", "removed")) {
    $Prefix = if ($DryRun) { "Would update baseline" } else { "Baseline" }
    Write-Host "$Prefix ($Action): $Target"
  }
  return $Action
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

function Split-NameList {
  param([string[]]$Values)
  return @($Values | ForEach-Object { $_ -split "," } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
}

function Get-SkillDirs {
  param([Parameter(Mandatory = $true)][string]$Root)
  if (-not (Test-Path $Root -PathType Container)) { return @() }
  return @(Get-ChildItem -Path $Root -Directory | Where-Object { $_.Name -like "rumo-*" } | Sort-Object Name)
}

function Test-PathWithin {
  param([string]$Path, [Parameter(Mandatory = $true)][string]$Root)
  if (-not $Path) { return $false }
  $Prefix = ([IO.Path]::GetFullPath($Root)).TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
  return $Path.StartsWith($Prefix, [StringComparison]::OrdinalIgnoreCase)
}

function Test-OwnedLinkTarget {
  param([string]$Target)
  return (Test-PathWithin $Target $RepoSkills) -or (Test-PathWithin $Target $RepoExtras)
}

function Get-RumoLinks {
  param([Parameter(Mandatory = $true)][string]$TargetSkillsPath)
  return @(Get-ChildItem -Path $TargetSkillsPath -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "rumo-*" -and $_.LinkType -in @("SymbolicLink", "Junction") })
}

function Get-DesiredSkillDirs {
  param([Parameter(Mandatory = $true)][string]$TargetSkillsPath)
  # Default skills, requested extras, and extras this checkout already installed here.
  $Selected = [System.Collections.Generic.SortedSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
  foreach ($Name in $ExtraNames) { [void]$Selected.Add($Name) }
  foreach ($Link in (Get-RumoLinks $TargetSkillsPath)) {
    if ($ExtraDirs.ContainsKey($Link.Name) -and (Test-PathWithin (Get-LinkTarget $Link) $RepoExtras)) {
      [void]$Selected.Add($Link.Name)
    }
  }
  foreach ($Name in $RemoveExtraNames) { [void]$Selected.Remove($Name) }

  $Desired = [ordered]@{}
  foreach ($Dir in $CoreDirs) { $Desired[$Dir.Name] = $Dir.FullName }
  foreach ($Name in $Selected) { $Desired[$Name] = $ExtraDirs[$Name] }
  return $Desired
}

function Get-RemovalNotice {
  param([Parameter(Mandatory = $true)][string]$Name)
  if ($RemoveExtraNames -contains $Name) { return "Removed optional skill $Name." }
  if ($ExtraDirs.ContainsKey($Name)) { return "$Name is optional now; reinstall it with -Extras $Name." }
  return "Removed stale link $Name."
}

function Assert-SkillLinksSafe {
  param([Parameter(Mandatory = $true)][string[]]$TargetSkillsPaths)
  $Issues = [System.Collections.Generic.List[string]]::new()
  foreach ($TargetSkillsPath in $TargetSkillsPaths) {
    $Desired = Get-DesiredSkillDirs $TargetSkillsPath
    foreach ($Name in $Desired.Keys) {
      $LinkPath = Join-Path $TargetSkillsPath $Name
      $Existing = Get-Item -LiteralPath $LinkPath -Force -ErrorAction SilentlyContinue
      if (-not $Existing) { continue }
      if ($Existing.LinkType -notin @("SymbolicLink", "Junction")) {
        $Issues.Add("$LinkPath exists as a real file or directory; move or rename it, then rerun")
        continue
      }
      $Expected = [IO.Path]::GetFullPath($Desired[$Name])
      $Actual = Get-LinkTarget $Existing
      if ($Actual -and -not (Test-OwnedLinkTarget $Actual) -and -not $ReplaceForeignLinks) {
        $Issues.Add("$LinkPath points to $Actual (expected $Expected); use -ReplaceForeignLinks to replace it")
      }
    }
  }
  if ($Issues.Count -gt 0) {
    throw "Skill link preflight failed; no links were changed:`n- $($Issues -join "`n- ")"
  }
}

function Sync-SkillLinks {
  param([Parameter(Mandatory = $true)][string]$TargetSkillsPath)
  $Desired = Get-DesiredSkillDirs $TargetSkillsPath
  Invoke-Step "New-Item -ItemType Directory -Force -Path `"$TargetSkillsPath`"" {
    New-Item -ItemType Directory -Force -Path $TargetSkillsPath | Out-Null
  }
  foreach ($Name in $Desired.Keys) {
    $LinkPath = Join-Path $TargetSkillsPath $Name
    $Source = $Desired[$Name]
    $Existing = Get-Item -LiteralPath $LinkPath -Force -ErrorAction SilentlyContinue
    if ($Existing) {
      if ($Existing.LinkType -notin @("SymbolicLink", "Junction")) {
        throw "Refusing to replace non-link skill path: $LinkPath"
      }
      Invoke-Step "Remove link `"$LinkPath`"" { Remove-SkillLink $Existing }
    }
    Invoke-Step "New-Item -ItemType Junction -Path `"$LinkPath`" -Target `"$Source`"" {
      New-Item -ItemType Junction -Path $LinkPath -Target $Source | Out-Null
    }
  }
  foreach ($Link in (Get-RumoLinks $TargetSkillsPath)) {
    if ($Desired.Contains($Link.Name) -or -not (Test-OwnedLinkTarget (Get-LinkTarget $Link))) { continue }
    Write-Host (Get-RemovalNotice $Link.Name)
    Invoke-Step "Remove link `"$($Link.FullName)`"" { Remove-SkillLink $Link }
  }
  return $Desired.Count
}

function Assert-ExtraNames {
  foreach ($Name in @($ExtraNames + $RemoveExtraNames)) {
    if (-not $ExtraDirs.ContainsKey($Name)) {
      throw "Unknown optional skill: $Name. Run with -ListExtras to see available names; nothing was changed."
    }
  }
}

function Show-Extras {
  if ($ExtraDirs.Count -eq 0) {
    Write-Host "No optional skills are available in $Repo."
    return
  }
  Write-Host "Optional skills (install with -Extras <name>[,<name>]):"
  foreach ($Name in ($ExtraDirs.Keys | Sort-Object)) {
    $SkillText = Get-Content -LiteralPath (Join-Path $ExtraDirs[$Name] "SKILL.md") -Raw -Encoding UTF8
    $Description = if ($SkillText -match "(?m)^description:\s*(.+?)\s*$") { $Matches[1].Trim('"', "'") } else { "" }
    $Description = ($Description -split "(?<=\.)\s", 2)[0]
    Write-Host "  $Name  $Description"
  }
}

$ScriptRoot = $PSScriptRoot
if (-not $Repo) { $Repo = if (Test-Path (Join-Path $ScriptRoot "skills")) { $ScriptRoot } else { Join-Path $HOME ".rumo-engineering-skills" } }
$Repo = [IO.Path]::GetFullPath($Repo)
$CodexHome = if ($CodexHome) { $CodexHome } else { Join-Path $HOME ".codex" }
$ClaudeHome = if ($ClaudeHome) { $ClaudeHome } else { Join-Path $HOME ".claude" }
$AgentsHome = if ($AgentsHome) { $AgentsHome } else { Join-Path $HOME ".agents" }
$RepoSkills = Join-Path $Repo "skills"
$RepoExtras = Join-Path $Repo "extras"
$ExtraDirs = @{}
foreach ($Dir in (Get-SkillDirs $RepoExtras)) { $ExtraDirs[$Dir.Name] = $Dir.FullName }

$ExtraNames = @(Split-NameList $Extras)
$RemoveExtraNames = @(Split-NameList $RemoveExtras)
foreach ($Name in $ExtraNames) {
  if ($RemoveExtraNames -contains $Name) { throw "$Name was passed to both -Extras and -RemoveExtras; nothing was changed." }
}
if ($Baseline -and $RemoveBaseline) { throw "-Baseline and -RemoveBaseline cannot be combined; nothing was changed." }
if ($Uninstall -and ($ExtraNames -or $RemoveExtraNames -or $Baseline -or $RemoveBaseline -or $ProfilesRepoExplicit -or $ReplaceForeignLinks -or $ListExtras)) {
  throw "-Uninstall cannot be combined with options that install or configure skills; nothing was changed."
}

if ($ListExtras) {
  if (-not (Test-Path $RepoSkills)) { throw "Skills repository not found: $Repo. Install once before listing optional skills." }
  Show-Extras
  exit 0
}

$SyncCodex = $CodexHomeExplicit -or (Get-Command codex -ErrorAction SilentlyContinue) -or (Test-Path $CodexHome)
$SyncClaude = $ClaudeHomeExplicit -or (Get-Command claude -ErrorAction SilentlyContinue) -or (Test-Path $ClaudeHome)
$SyncAgents = $AgentsHomeExplicit -or (Test-Path $AgentsHome) -or (Get-Command grok -ErrorAction SilentlyContinue) -or (Test-Path (Join-Path $HOME ".grok"))
$TargetSkillsPaths = [System.Collections.Generic.List[string]]::new()
if ($SyncCodex) { $TargetSkillsPaths.Add((Join-Path $CodexHome "skills")) }
if ($SyncClaude) { $TargetSkillsPaths.Add((Join-Path $ClaudeHome "skills")) }
if ($SyncAgents) { $TargetSkillsPaths.Add((Join-Path $AgentsHome "skills")) }
$BaselineScript = Join-Path $RepoSkills "rumo-coding-guidelines\scripts\baseline_block.py"

# Uninstall needs neither Git nor a valid checkout, so it runs before both checks.
if ($Uninstall) {
  if ($TargetSkillsPaths.Count -eq 0) {
    Write-Host "No supported agent client was detected; nothing to uninstall."
    exit 0
  }
  foreach ($TargetSkillsPath in $TargetSkillsPaths) {
    $Owned = @(Get-RumoLinks $TargetSkillsPath | Where-Object { Test-OwnedLinkTarget (Get-LinkTarget $_) })
    foreach ($Link in $Owned) {
      Invoke-Step "Remove link `"$($Link.FullName)`"" { Remove-SkillLink $Link }
    }
    $Verb = if ($DryRun) { "would be removed" } else { "removed" }
    Write-Host "$($Owned.Count) skill links $Verb from $TargetSkillsPath"
  }
  $BaselineTargets = @()
  if ($SyncCodex) { $BaselineTargets += Join-Path $CodexHome "AGENTS.md" }
  if ($SyncClaude) { $BaselineTargets += Join-Path $ClaudeHome "CLAUDE.md" }
  if ($BaselineTargets -and -not (Get-Command py, python3, python -ErrorAction SilentlyContinue)) {
    Write-Host "Python 3 was not found; remove any rumo-engineering-skills:baseline block from $($BaselineTargets -join ', ') by hand."
  }
  else {
    foreach ($Target in $BaselineTargets) { [void](Sync-BaselineBlock $Target "remove") }
  }
  if ($DryRun) {
    Write-Host "Dry run finished; nothing was changed."
    exit 0
  }
  Write-Host "Rumo skills uninstalled."
  Write-Host "Kept: the repository at $Repo, ~/.rumo-engineering-skills/config.json, and any project profiles. Delete them by hand if you no longer need them."
  exit 0
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  throw "Git is required. Install it (Windows: winget install --id Git.Git; macOS: xcode-select --install; Linux: your package manager), then rerun. Nothing was changed."
}
if (Test-Path $RepoSkills) { Assert-ExtraNames }

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

if (-not (Test-Path $RepoSkills)) { throw "Skills directory not found: $RepoSkills" }
Invoke-SkillValidation $Repo

if (($Baseline -or $RemoveBaseline) -and -not (Test-Path $BaselineScript -PathType Leaf)) {
  throw "Baseline helper not found: $BaselineScript; nothing was changed."
}

$CoreDirs = @(Get-SkillDirs $RepoSkills)
$ExtraDirs = @{}
foreach ($Dir in (Get-SkillDirs $RepoExtras)) { $ExtraDirs[$Dir.Name] = $Dir.FullName }
Assert-ExtraNames

if ($ProfilesRepoExplicit) {
  $ProfileConfig = Join-Path $Repo "skills\rumo-project-profile\scripts\profile_config.py"
  $ProfileArgs = @("--profiles-repo", $ProfilesRepo, "--dry-run")
  if (Get-Command py -ErrorAction SilentlyContinue) { & py -3 $ProfileConfig @ProfileArgs }
  elseif (Get-Command python3 -ErrorAction SilentlyContinue) { & python3 $ProfileConfig @ProfileArgs }
  elseif (Get-Command python -ErrorAction SilentlyContinue) { & python $ProfileConfig @ProfileArgs }
  else { throw "Python 3 is required to configure the profiles repository. $PythonInstallHint No skill links were changed." }
  if ($LASTEXITCODE -ne 0) { throw "Profiles repository configuration failed; no skill links were changed." }
}

if ($TargetSkillsPaths.Count -eq 0) {
  throw "No supported agent client was detected; no links were changed. Pass -CodexHome, -ClaudeHome, or -AgentsHome to choose a target explicitly."
}
Assert-SkillLinksSafe $TargetSkillsPaths
if ($ProfilesRepoExplicit -and -not $DryRun) {
  if (Get-Command py -ErrorAction SilentlyContinue) { & py -3 $ProfileConfig --profiles-repo $ProfilesRepo }
  elseif (Get-Command python3 -ErrorAction SilentlyContinue) { & python3 $ProfileConfig --profiles-repo $ProfilesRepo }
  else { & python $ProfileConfig --profiles-repo $ProfilesRepo }
  if ($LASTEXITCODE -ne 0) { throw "Profiles repository configuration failed; no skill links were changed." }
}
$LinkedCounts = [ordered]@{}
foreach ($TargetSkillsPath in $TargetSkillsPaths) {
  $LinkedCounts[$TargetSkillsPath] = Sync-SkillLinks $TargetSkillsPath
}
if (-not $SyncCodex) { Write-Host "Codex was not detected; skipping." }
if (-not $SyncClaude) { Write-Host "Claude Code was not detected; skipping." }
if (-not $SyncAgents) { Write-Host "A shared agent client was not detected; skipping." }

$BaselineMode = if ($Baseline) { "install" } elseif ($RemoveBaseline) { "remove" } else { "refresh" }
$BaselineMissing = [System.Collections.Generic.List[string]]::new()
$BaselineTargets = [System.Collections.Generic.List[string]]::new()
if ($SyncCodex) { $BaselineTargets.Add((Join-Path $CodexHome "AGENTS.md")) }
if ($SyncClaude) { $BaselineTargets.Add((Join-Path $ClaudeHome "CLAUDE.md")) }
foreach ($Target in $BaselineTargets) {
  if ((Sync-BaselineBlock $Target $BaselineMode) -eq "absent" -and $BaselineMode -eq "refresh") { $BaselineMissing.Add($Target) }
}

if ($DryRun) {
  Write-Host "Dry run finished; nothing was changed."
  exit 0
}
Write-Host "Rumo skills installation completed."
foreach ($TargetSkillsPath in $LinkedCounts.Keys) {
  Write-Host "$($LinkedCounts[$TargetSkillsPath]) skills linked in $TargetSkillsPath"
}
Write-Host "Repository: $Repo"
if (-not [string]::Equals($Repo, [IO.Path]::GetFullPath($ScriptRoot), [StringComparison]::OrdinalIgnoreCase)) {
  Write-Host "Recommended: set RUMO_SKILLS_REPO=$Repo so later runs from another copy of this script use the same checkout."
}
Write-Host 'Next: start a new agent session, then run /rumo-setup (Claude Code) or $rumo-setup (Codex) to choose agents, models, and reasoning effort.'
if ($ProfilesRepo) { Write-Host "Project profiles: $ProfilesRepo" }
else { Write-Host "Optional: set RUMO_SKILL_PROFILES_REPO to a private profiles checkout." }
if ($BaselineMissing.Count -gt 0) {
  Write-Host "Optional: rerun with -Baseline to keep the core rules always on in $($BaselineMissing -join ', '); see README."
}
if ($Baseline -and $SyncAgents) {
  Write-Host "Clients reading only the shared agents directory have no user-level instruction file here; paste skills\rumo-coding-guidelines\references\agents-snippet.md into their instructions by hand."
}
