$ErrorActionPreference = 'Stop'
$result = @{}
foreach ($name in @('IMA_OPENAPI_APIKEY', 'IMA_API_KEY', 'IMA_OPENAPI_CLIENTID', 'IMA_CLIENT_ID')) {
    foreach ($scope in @('Process', 'User', 'Machine')) {
        $value = [Environment]::GetEnvironmentVariable($name, $scope)
        if (-not [string]::IsNullOrWhiteSpace($value)) {
            $result[$name] = $value
            break
        }
    }
}
# This output is consumed privately by the parent process; never invoke this helper directly in logs.
[Console]::Out.Write(($result | ConvertTo-Json -Compress))
