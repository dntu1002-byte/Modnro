$ErrorActionPreference = 'Stop'
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path -LiteralPath $compiler)) {
    $compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework\v4.0.30319\csc.exe'
}
if (-not (Test-Path -LiteralPath $compiler)) { throw '.NET Framework C# compiler not found.' }
& $compiler /nologo /optimize+ /target:exe "/out:$PSScriptRoot\AutoCaptcha.exe" "$PSScriptRoot\CaptchaQueue.cs"
if ($LASTEXITCODE -ne 0) { throw "Build failed: $LASTEXITCODE" }
Write-Output 'BUILD PASS: exit=0, errors=0'
