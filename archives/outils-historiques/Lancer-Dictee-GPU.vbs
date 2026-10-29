Option Explicit
Dim shell, fs, dossier, code, commande, python, pythonw
Set shell = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")
dossier = fs.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = dossier
shell.Environment("PROCESS")("DICTEE_GPU_LIGHT") = "1"
python = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python311\python.exe"
pythonw = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python311\pythonw.exe"
If fs.FileExists(python) And fs.FileExists(pythonw) Then
    commande = """" & pythonw & """
Else
    code = shell.Run("cmd /c py -3.11 -c ""import sys""", 0, True)
    If code <> 0 Then
        MsgBox "Python 3.11 et le lanceur Python pour Windows sont nécessaires. Voir LIRE-MOI.txt.", 16, "Dictée LinTO GPU"
        WScript.Quit 1
    End If
    commande = "pyw -3.11"
End If
commande = commande & " """ & dossier & "\lancer-dictee.pyw"""
shell.Run commande, 0, False
