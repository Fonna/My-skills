param([Parameter(Mandatory=$true)][ValidateSet('protect','unprotect')][string]$Operation)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Security
$payload = [Console]::In.ReadToEnd()
try {
    if ($Operation -eq 'protect') {
        $bytes = [Text.Encoding]::UTF8.GetBytes($payload)
        $encrypted = [Security.Cryptography.ProtectedData]::Protect($bytes, $null, [Security.Cryptography.DataProtectionScope]::CurrentUser)
        [Console]::Out.Write([Convert]::ToBase64String($encrypted))
    } else {
        $bytes = [Convert]::FromBase64String($payload)
        $decrypted = [Security.Cryptography.ProtectedData]::Unprotect($bytes, $null, [Security.Cryptography.DataProtectionScope]::CurrentUser)
        [Console]::Out.Write([Text.Encoding]::UTF8.GetString($decrypted))
    }
} catch {
    [Console]::Error.WriteLine('Windows DPAPI operation failed')
    exit 1
}
