#Requires -Version 7.0
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
if (-not $IsWindows) { throw 'Dropbox directory ignore markers require Windows and NTFS.' }

$siteRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
if (-not (Test-Path -LiteralPath (Join-Path $siteRoot 'package.json') -PathType Leaf)) {
  throw 'Run this helper from the course site repository.'
}

$localFolders = @('node_modules', '.pnpm-store', '.cache', '.verification', 'dist', '.astro', '.pages-publish', '.git')
foreach ($folderName in $localFolders) {
  $folderPath = Join-Path $siteRoot $folderName
  if (-not (Test-Path -LiteralPath $folderPath)) {
    if ($folderName -eq '.git') { continue }
    New-Item -ItemType Directory -Path $folderPath | Out-Null
  }

  $folder = Get-Item -LiteralPath $folderPath -Force
  if (-not $folder.PSIsContainer -or $folder.LinkType) {
    throw "Expected a local directory: $folderPath"
  }

  # Existing and future children remain local while this parent is ignored.
  Set-Content -LiteralPath $folderPath -Stream 'com.dropbox.ignored' -Value 1
  if ((Get-Content -LiteralPath $folderPath -Stream 'com.dropbox.ignored').Trim() -ne '1') {
    throw "Could not verify the Dropbox ignore marker: $folderPath"
  }
  Write-Output "Local-only in Dropbox: $folderName"
}
