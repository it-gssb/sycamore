[CmdletBinding()]
param(
  [Parameter(Mandatory, ParameterSetName="prefix", HelpMessage="Prefix of Groups to delete")]
  [String]$prefixToDelete
)

Import-Module Microsoft.Graph.Authentication

Connect-MgGraph -Scopes "Directory.AccessAsUser.All"

if (-not $prefixToDelete) {
    Write-Error "-prefix must not be empty"
}

$groups = Get-MgGroup -All
foreach ($group in $groups) {
    # Skip all groups where the name does not start with the prefix
    $displayName = $group.DisplayName
    $groupId = $group.Id
    if (!($displayName.StartsWith($prefixToDelete))) {
        Write-Information -MessageData "Skipping group '$displayName' (ID=$groupId)" -InformationAction Continue
        continue
    }

    # Delete the matching group
    Write-Information -MessageData "Deleting group '$displayName' (ID=$groupId)" -InformationAction Continue
    Remove-MgGroup -GroupId $groupId
}

Write-Information "Done" -InformationAction Continue
