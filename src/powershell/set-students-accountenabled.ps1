[CmdletBinding()]
param(
  [Parameter(Mandatory, ParameterSetName="csv", HelpMessage="Input CSV file")]
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
        #Write-Information -MessageData "Skipping user $userPrincipalName" -InformationAction Continue
        continue
    }

    # We want to enable users that are in the activeUsers list and disable all others.
    $targetEnablement = $activeUsers.ContainsKey($userPrincipalName)

    # If the user already has the right "AcccountEnabled" setting, skip it
    if ($user.AccountEnabled -eq $targetEnablement) {
        Write-Information -MessageData "User $userPrincipalName already $(If ($targetEnablement) {"enabled"} Else {"disabled"})" -InformationAction Continue
        continue
    }

    # Update the user's "AcccountEnabled" setting
    Write-Information -MessageData "$(If ($targetEnablement) {"Enabling"} Else {"Disabling"}) user $userPrincipalName" -InformationAction Continue
    Update-MgUser -UserId $userPrincipalName -AccountEnabled:$targetEnablement
}

Write-Information "Done" -InformationAction Continue
