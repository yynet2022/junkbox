Option Explicit

Dim f
f = WScript.ScriptFullName
WScript.Echo f

Dim fso
set fso = CreateObject("Scripting.FileSystemObject")
WScript.Echo "typename:", typename(fso)

with fso
  WScript.Echo "", _
   "BuildPath:", .BuildPath("a", "b"), vbCrLf, _
   "GetAbsolutePathName:", .GetAbsolutePathName("foo.vbs"), vbCrLf, _
   "GetParentFolderName:", .GetParentFolderName(f), vbCrLf, _
   "GetFileName:", .GetFileName(f), vbCrLf, _
   "GetBaseName:", .GetBaseName(f), vbCrLf, _
   "GetExtensionName:", .GetExtensionName(f), vbCrLf, _
   "GetDriveName:", .GetDriveName(f), vbCrLf, _
   "GetTempName:", .GetTempName(), vbCrLf, _
   "GetFileVersion:", .GetFileVersion(f), vbCrLf, _
   ""

  Dim p
  p = .GetParentFolderName(f)
  If .FolderExists(p) Then
   WScript.Echo p, "exist."
  Else
   WScript.Echo p, "not exists."
  End if

  Dim folder
  set folder = .getFolder(p)

  ' ファイル一覧
  Dim i
  for each i in folder.files
    WScript.Echo "file:", i.name
  next 

  ' サブフォルダ一覧
  for each i in folder.subfolders
    WScript.Echo "sub:", i.name
  next

  If .FileExists(f) Then
   WScript.Echo f, "exist."
  Else
   WScript.Echo f, "not exists."
  End if

  Dim ff
  ff = .GetAbsolutePathName("foo.vbs")
  If .FileExists(ff) Then
   WScript.Echo ff, "exist."
  Else
   WScript.Echo ff, "not exists."
  End if
End with

Set fso = Nothing
