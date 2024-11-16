<#
.SYNOPSIS
   Reads a list of students from CSV and creates missing accounts in Entra
.DESCRIPTION
   This script reads a list of students from a CSV file and loads existing
   students from Entra. It then creates all students in Entra that exist
   in the CSV file but are missing in Entra.
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
.PARAMETER addToGroup
   The group to add students to. Leave empty / unset to not do this.
#>
[CmdletBinding()]
param(
  [Parameter(HelpMessage="Whether to use dry-run mode")]
  [Boolean]$dryRun = $true,

  [Parameter(HelpMessage="Set to increase output verbosity")]
  [Boolean]$verboseOutput = $false,

  [Parameter(Mandatory, HelpMessage="The CSV file with students.")]
  [String]$csvFile,

  [Parameter(HelpMessage="The group to add students to.")]
  [String]$addToGroup
)

Import-Module Microsoft.Graph.Authentication

Connect-MgGraph -Scopes "Directory.AccessAsUser.All"

$csvUsers = Import-Csv $csvFile

$existingUsers=@{}

$studentLicenseSku = Get-MgSubscribedSku -All | Where SkuPartNumber -eq 'STANDARDWOFFPACK_STUDENT'

$addToGroupObj = $null
if ($addToGroup) {
  $addToGroupObj = Get-MgGroup -Filter "DisplayName eq '$addToGroup'"
  if (-not $addToGroupObj) {
    write-error "Could not find group '$addToGroup'."
    exit 1
  }
}

$adUsers = Get-MgUser -All -Property UserPrincipalName, AccountEnabled
foreach ($user in $adUsers) {
    $existingUsers[$user.UserPrincipalName.ToLower()] = $user
}
    
foreach ($user in $csvUsers) {
    $userPrincipalName = $user.EmailAddress.ToLower()

    # Skip all users that are not in @student.gssb.org
    if (!($userPrincipalName.endsWith("@student.gssb.org"))) {
      if ($verboseOutput) {
        Write-Information -MessageData "Skipping user $userPrincipalName" -InformationAction Continue
      }
      continue
    }

    # Skip all users that already exist
    if ($existingUsers.ContainsKey($userPrincipalName)) {
      if ($verboseOutput) {
        Write-Information -MessageData "Skipping existing user $userPrincipalName" -InformationAction Continue
      }
      continue
    }

    # Create the user
    $message = "Creating user $userPrincipalName"
    if ($dryRun) {
      $message = $message + ' (dry run mode)'
    }
    Write-Host $message -ForegroundColor Blue
    
    $userPassword = $user.SourceId
    $userDisplayName = "{0} {1}" -f $user.FirstName, $user.LastName
    $mailNickname = $userPrincipalName.Remove($userPrincipalName.IndexOf("@"))
    $passwordProfile = @{ Password = $userPassword }

    if (-not $dryRun) {
      # Create user and set password
      $createdUser = New-MgUser -AccountEnabled -GivenName $user.FirstName -Surname $user.LastName -UserPrincipalName $userPrincipalName -PasswordProfile $passwordProfile -DisplayName $userDisplayName -MailNickname $mailNickname -PasswordPolicies "DisableStrongPassword" -AgeGroup "Minor" -UsageLocation US

      # Add license for user
      Set-MgUserLicense -UserId $userPrincipalName -AddLicenses @{SkuId = $studentLicenseSku.SkuId} -RemoveLicenses @()

      # Optionall add new students to a group
      if ($addToGroupObj) {
        New-MgGroupMember -GroupId $addToGroupObj.Id -DirectoryObjectId $createdUser.Id
      }
    }
}

Write-Information "Done" -InformationAction Continue
