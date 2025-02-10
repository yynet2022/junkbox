'
' Echo と配列の例
'

Dim a
Dim b(10)

b(0)="000"
b(2)=222
a = b

WScript.Echo "typename(a)= " & typename(a)
WScript.Echo "join(a)= " & join(a, ",")
WScript.Echo "typename(b)= " & typename(b)
WScript.Echo "typename(b(0))= " & typename(b(0))
WScript.Echo "typename(b(2))= " & typename(b(2))
WScript.Echo "join(b)= " & join(b, ",")

MsgBox "Hello, world! "
