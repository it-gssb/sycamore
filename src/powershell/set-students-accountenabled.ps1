<#
.SYNOPSIS
   Reads a list of students from CSV and enabled/disables accounts in Entra
.DESCRIPTION
   This script reads a list of students from a CSV file and loads existing
   students from Entra. It then enables students in Entra that exist
   in the CSV file and disables all students in Entra that do not exist
   in the CSV file.
.PARAMETER dryRun
   Whether to actually perform operations or use dry-run mode.
   Possible values: 0 = disable dry-run mode; 1 = enable
   Defaults to 1 (dry-run mode enabled).
.PARAMETER verboseOutput
   Whether to increase output verbosity.
   Possible values: 0 = disable verbose output; 1 = enable
   Defaults to 0 (verbose output disabled).
.PARAMETER csvFile
   The CSV file with students. Required columns:
   EmailAddress,SourceId,LastName,FirstName
#>
[CmdletBinding()]
param(
    [Parameter(HelpMessage="Whether to use dry-run mode")]
    [Boolean]$dryRun = $true,

    [Parameter(HelpMessage="Set to increase output verbosity")]
    [Boolean]$verboseOutput = $false,

    [Parameter(Mandatory, HelpMessage="Input CSV file")]
    [String]$csvFile
)

Import-Module Microsoft.Graph.Authentication

Connect-MgGraph -Scopes "Directory.AccessAsUser.All"

$csvUsers = Import-Csv $csvFile

$activeUsers=@{}
foreach ($user in $csvUsers) {
    $activeUsers[$user.EmailAddress.ToLower()] = $user.SourceId
}
    
$adUsers = Get-MgUser -All -Property UserPrincipalName, AccountEnabled
foreach ($user in $adUsers) {
    $userPrincipalName = $user.UserPrincipalName.ToLower()
    # Skip all users that are not in @student.gssb.org
    if (!($userPrincipalName.endsWith("@student.gssb.org"))) {
        if ($verboseOutput) {
            Write-Information -MessageData "Skipping user $userPrincipalName" -InformationAction Continue
        }
        continue
    }

    # We want to enable users that are in the activeUsers list and disable all others.
    $targetEnablement = $activeUsers.ContainsKey($userPrincipalName)

    # If the user already has the right "AcccountEnabled" setting, skip it
    if ($user.AccountEnabled -eq $targetEnablement) {
        if ($verboseOutput) {
            Write-Information -MessageData "User $userPrincipalName already $(If ($targetEnablement) {"enabled"} Else {"disabled"})" -InformationAction Continue
        }
        continue
    }

    # Update the user's "AcccountEnabled" setting
    $message = "$(If ($targetEnablement) {"Enabling"} Else {"Disabling"}) user $userPrincipalName"
    if ($dryRun) {
      $message = $message + ' (dry run mode)'
    }
    Write-Host $message -ForegroundColor Blue
    if (-not $dryRun) {
        Update-MgUser -UserId $userPrincipalName -AccountEnabled:$targetEnablement
    }
}

Write-Information "Done" -InformationAction Continue
