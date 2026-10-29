Option Explicit
Dim shell, files, folder, pythonw, command
Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
folder = files.GetParentFolderName(WScript.ScriptFullName)
pythonw = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python311\pythonw.exe"
If files.FileExists(pythonw) Then
    command = Chr(34) & pythonw & Chr(34)
Else
    command = "pyw.exe -3.11"
End If
shell.CurrentDirectory = folder
shell.Run command & " " & Chr(34) & folder & "\lancer-dictee.pyw" & Chr(34), 0, False
