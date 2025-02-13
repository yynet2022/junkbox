'
' WScript.Network の例
' ドメイン名、コンピュータ名、ユーザ名の取得
'

Option Explicit
On Error Resume Next

Dim objWshNetwork   ' WshNetwork オブジェクト

Set objWshNetwork = WScript.CreateObject("WScript.Network")
If Err.Number = 0 Then
    WScript.Echo "ドメイン：" & objWshNetwork.UserDomain
    WScript.Echo "コンピュータ：" & objWshNetwork.ComputerName
    WScript.Echo "ユーザー：" & objWshNetwork.UserName
Else
    WScript.Echo "エラー: " & Err.Description
End If

Set objWshNetwork = Nothing
MsgBox "こんにちわ、世界！"
MsgBox "こんばんわ、世の中！"
