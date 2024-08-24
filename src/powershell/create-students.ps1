[CmdletBinding()]
param(
  [Parameter(Mandatory, ParameterSetName="csv", HelpMessage="Input CSV file")]
  [String]$csvFile
)

Import-Module Microsoft.Graph.Authentication

Connect-MgGraph -Scopes "Directory.AccessAsUser.All"

$csvUsers = Import-Csv $csvFile

$existingUsers=@{}

$studentLicenseSku = Get-MgSubscribedSku -All | Where SkuPartNumber -eq 'STANDARDWOFFPACK_STUDENT'
$allStudentsGroup = Get-MgGroup -Filter "DisplayName eq 'All Students'"

$adUsers = Get-MgUser -All -Property UserPrincipalName, AccountEnabled
foreach ($user in $adUsers) {
    $existingUsers[$user.UserPrincipalName.ToLower()] = $user
}
    
foreach ($user in $csvUsers) {
    $userPrincipalName = $user.EmailAddress.ToLower()

      # Skip all users that are not in @student.gssb.org
    if (!($userPrincipalName.endsWith("@student.gssb.org"))) {
        Write-Information -MessageData "Skipping user $userPrincipalName" -InformationAction Continue
        continue
    }

    # Skip all users that already exist
    if ($existingUsers.ContainsKey($userPrincipalName)) {
        Write-Information -MessageData "Skipping existing user $userPrincipalName" -InformationAction Continue
        continue
    }

    # Create the user
    Write-Information -MessageData "Creating user $userPrincipalName" -InformationAction Continue
    
    $userPassword = $user.SourceId
    $userDisplayName = "{0} {1}" -f $user.FirstName, $user.LastName
    $mailNickname = $userPrincipalName.Remove($userPrincipalName.IndexOf("@"))
    $passwordProfile = @{ Password = $userPassword }
    $createdUser = New-MgUser -AccountEnabled -GivenName $user.FirstName -Surname $user.LastName -UserPrincipalName $userPrincipalName -PasswordProfile $passwordProfile -DisplayName $userDisplayName -MailNickname $mailNickname -PasswordPolicies "DisableStrongPassword" -AgeGroup "Minor" -UsageLocation US
    Set-MgUserLicense -UserId $userPrincipalName -AddLicenses @{SkuId = $studentLicenseSku.SkuId} -RemoveLicenses @()
    New-MgGroupMember -GroupId $allStudentsGroup.Id -DirectoryObjectId $createdUser.Id
}

Write-Information "Done" -InformationAction Continue
