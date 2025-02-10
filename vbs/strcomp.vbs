Option Explicit

WScript.Echo "abc=abc: ", StrComp("abc", "abc")
WScript.Echo "abc=aBC (text):", StrComp("abc", "aBC", vbTextCompare)
WScript.Echo "abc=abC (text):", StrComp("abc", "abC", vbTextCompare)
WScript.Echo "abc=aBC (bin) :", StrComp("abc", "aBC", vbBinaryCompare)
WScript.Echo "abc=abC (bin) :", StrComp("abc", "abC", vbBinaryCompare)
