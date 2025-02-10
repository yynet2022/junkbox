
Option Explicit
WScript.Echo "WScript"
WScript.Echo " .Name:     " & WScript.Name     & vbCrLf & _
             " .Path:     " & WScript.Path     & vbCrLf & _
             " .FullName: " & WScript.FullName & vbCrLf & _
             " .VersionF " & WScript.Version

WScript.Sleep(1)

WScript.Echo "", _
 ".ScriptName:", WScript.ScriptName, vbCrLf, _
 ".ScriptFullName:", WScript.ScriptFullName, vbCrLf, _
 ".Interactive:", WScript.Interactive, vbCrLf, _
 ".TimeOut:", WScript.TimeOut, vbCrLf, _
 ".Arguments:", typename(WScript.Arguments), vbCrLf, _
 ".Arguments.Count :", WScript.Arguments.Count

Dim s, i
if WScript.Arguments.Count > 0 Then
   i = 0
   for each s in WScript.Arguments
      WScript.Echo "   arg" & i, s
      i = i + 1
   next
   for i = 0 to WScript.Arguments.Count - 1
      WScript.Echo "   arg" & i, _
                   WScript.Arguments(i), WScript.Arguments.Item(i)
   next
End if

if WScript.Arguments.Named.Exists("foo") Then
   WScript.Echo "   Named.foo:", WScript.Arguments.Named("foo")
End if
WScript.Echo "   Unnamed.count:", WScript.Arguments.Unnamed.Count
i = 0
for each s in WScript.Arguments.Unnamed
   WScript.Echo "     arg" & i, s
   i = i + 1
next

WScript.Echo "", _
 ".StdIn:", typename(WScript.StdIn), vbCrLf, _
 ".StdOut:", typename(WScript.StdOut), vbCrLf, _
 ".StdErr:", typename(WScript.StdErr), vbCrLf, _
 ""
