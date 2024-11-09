<#
.SYNOPSIS
   Reads a list of students from CSV and sets passwords in Entra
.DESCRIPTION
   This script reads a list of students from a CSV file. It then
   attempts to read the corresponding student from Entra. If the
   student exists in Entra, the account's password is reset to
   the value from the CSV file.
.PARAMETER dryRun
   Whether to actually perform operations or use dry-run mode.
   Possible values: 0 = disable dry-run mode; 1 = enable
   Defaults to 1 (dry-run mode enabled).
.PARAMETER csvFile
   The CSV file with students. Required columns:
   EmailAddress,SourceId,LastName,FirstName
#>
[CmdletBinding()]
param(
  [Parameter(HelpMessage="Whether to use dry-run mode")]
  [Boolean]$dryRun = $true,

  [Parameter(Mandatory, HelpMessage="Input CSV file")]
  [String]$csvFile
)

Import-Module Microsoft.Graph.Authentication

Connect-MgGraph -Scopes "Directory.AccessAsUser.All"

$allUsers = Import-Csv $csvFile

if (-not $allUsers) {
  Write-Error "Could not load CSV file."
  exit 1
}

$caption = 'Resetting passwords for all students in "' + $csvFile + '"'
if ($dryRun) {
    $caption = $caption + ' (dry run mode)'
}

$decision = $Host.UI.PromptForChoice(
    $caption,
    'Are you sure you want to proceed?',
    @('&Yes', '&No'), 1)
if ($decision -ne 0) {
    Write-Error "Cancelling on user's request."
    exit 1
}

foreach ($user in $allUsers) {
  $userPrincipalName = $user.EmailAddress.ToLower()
  $newPassword = $user.SourceId

  # Skip all users that are not in @student.gssb.org
  if (!($userPrincipalName.endsWith("@student.gssb.org"))) {
      Write-Warning -Message "Skipping user $userPrincipalName"
      continue
  }

  try
  {
    $null = Get-MgUser -UserId $userPrincipalName -ErrorAction Stop
  }
  catch
  {
    Write-Warning -Message "User $userPrincipalName does not exist"
    continue
  }

  $message = "Changing password for $userPrincipalName to $newPassword"
  if ($dryRun) {
    $message = $message + ' (dry run mode)'
  }
  Write-Host $message -ForegroundColor Blue

  if (-not $dryRun) {
      # Reset Password
    Update-MgUser -UserId $userPrincipalName -PasswordProfile @{ ForceChangePasswordNextSignIn = $false; Password = $newPassword }
  }
}

Write-Information "Done" -InformationAction Continue
