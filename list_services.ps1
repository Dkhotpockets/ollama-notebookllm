Get-Service | Where-Object {$_.Name -like '*postgres*'} | Select-Object Name, Status, DisplayName
