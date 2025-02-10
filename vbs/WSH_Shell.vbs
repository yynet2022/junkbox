Option Explicit

Dim shell
set shell = WScript.CreateObject("WScript.Shell")
WScript.Echo "", _
 "current directory:", shell.CurrentDirectory, vbCrLf, _
 ""

set shell = Nothing
