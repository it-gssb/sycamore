[CmdletBinding()]
param(
  [Parameter(Mandatory, ParameterSetName="csv", HelpMessage="Input CSV file")]
  [String]$csvFile
)

Import-Module Microsoft.Graph.Authentication

Connect-MgGraph -Scopes "Directory.AccessAsUser.All"

$allUsers = Import-Csv $csvFile

foreach ($user in $allUsers) {
  $userPrincipalName = $user.EmailAddress
  $newPassword = $user.SourceId

  try
  {
    $null = Get-MgUser -UserId $userPrincipalName -ErrorAction Stop
  }
  catch
  {
    Write-Warning -Message "User $userPrincipalName does not exist"
    continue
  }

  Write-Information -MessageData "Changing password for $userPrincipalName to $newPassword" -InformationAction Continue

  # Reset Password
  Update-MgUser -UserId $userPrincipalName -PasswordProfile @{ ForceChangePasswordNextSignIn = $false; Password = $newPassword }
}

Write-Information "Done" -InformationAction Continue
