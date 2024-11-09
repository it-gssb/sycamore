<#
.SYNOPSIS
   Deletes groups from Entra that start with a specific prefix.
.DESCRIPTION
   This script deletes groups from Entra identified by their name
   starting with a provided prefix. This script should be used at the
   end of a school year to clear groups from previous previous years.
.PARAMETER dryRun
   Whether to actually perform operations or use dry-run mode.
   Possible values: 0 = disable dry-run mode; 1 = enable
   Defaults to 1 (dry-run mode enabled).
.PARAMETER verboseOutput
   Whether to increase output verbosity.
   Possible values: 0 = disable verbose output; 1 = enable
   Defaults to 0 (verbose output disabled).
.PARAMETER prefixToDelete
   Prefix of Groups to delete.
#>
[CmdletBinding()]
param(
  [Parameter(HelpMessage="Whether to use dry-run mode")]
  [Boolean]$dryRun = $true,

  [Parameter(HelpMessage="Set to increase output verbosity")]
  [Boolean]$verboseOutput = $false,

  [Parameter(Mandatory, HelpMessage="Prefix of Groups to delete")]
  [String]$prefixToDelete
)

Import-Module Microsoft.Graph.Authentication

Connect-MgGraph -Scopes "Directory.AccessAsUser.All"

if (-not $prefixToDelete) {
    Write-Error "-prefix must not be empty"
}

$caption = 'Delete Groups starting with "' + $prefixToDelete + '"'
if ($dryRun) {
    $caption = $caption + ' (dry run mode)'
}

$decision = $Host.UI.PromptForChoice(
    $caption,
    'Are you sure you want to proceed?',
    @('&Yes', '&No'), 1)
if ($decision -ne 0) {
    Write-Error "Cancelling on user's request"
    exit 1
}

$groups = Get-MgGroup -All
foreach ($group in $groups) {
    # Skip all groups where the name does not start with the prefix
    $displayName = $group.DisplayName
    $groupId = $group.Id
    if (!($displayName.StartsWith($prefixToDelete))) {
        if ($verboseOutput) {
            Write-Information -MessageData "Skipping group '$displayName' (ID=$groupId)" -InformationAction Continue
        }
        continue
    }

    # Delete the matching group
    $message = "Deleting group '$displayName' (ID=$groupId)"
    if ($dryRun) {
        $message = $message + ' (dry run mode)'
    }
    Write-Host $message -ForegroundColor Blue
    if (-not $dryRun) {
        Remove-MgGroup -GroupId $groupId
    }
}

Write-Information "Done" -InformationAction Continue
