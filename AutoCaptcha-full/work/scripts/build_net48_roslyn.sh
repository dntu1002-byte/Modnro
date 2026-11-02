#!/bin/bash
# Build work/src/AutoCaptcha.exe nhắm .NET Framework 4.8 TRÊN LINUX: Roslyn (dotnet SDK 8) + reference assemblies 4.8 của mono-devel.
# Cần: apt install dotnet-sdk-8.0 mono-devel. Thử chạy bằng `mono`, CHƯA thử trên Windows thật.
set -e
HERE="$(cd "$(dirname "$0")/.." && pwd)"
R=/usr/lib/mono/4.8-api
CSC=$(ls /usr/lib/dotnet/sdk/*/Roslyn/bincore/csc.dll | tail -1)
dotnet "$CSC" /noconfig /nostdlib+ /nologo /langversion:5 /optimize+ /target:exe "/out:$HERE/src/AutoCaptcha.exe" \
  /r:$R/mscorlib.dll /r:$R/System.dll /r:$R/System.Core.dll /r:$R/System.IO.Compression.dll \
  /r:$R/Facades/System.Runtime.dll /r:$R/Facades/System.Text.Encoding.dll /r:$R/Facades/System.IO.dll \
  /r:$R/Facades/System.Collections.dll /r:$R/Facades/System.Threading.dll /r:$R/Facades/System.Diagnostics.Debug.dll \
  /r:$R/Facades/System.Reflection.dll /r:$R/Facades/System.Globalization.dll /r:$R/Facades/System.Linq.dll \
  "$HERE/src/CaptchaQueue.cs"
sha256sum "$HERE/src/AutoCaptcha.exe"
