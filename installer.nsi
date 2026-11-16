Unicode True
Name "Speediance FIT Exporter"
OutFile "dist\SpeedianceFITExporter-Setup.exe"
InstallDir "$LOCALAPPDATA\Programs\Speediance FIT Exporter"
RequestExecutionLevel user
Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles
Section "Install"
 SetOutPath "$INSTDIR"
 File "dist\SpeedianceFITExporter.exe"
 WriteUninstaller "$INSTDIR\Uninstall.exe"
 CreateDirectory "$SMPROGRAMS\Speediance FIT Exporter"
 CreateShortCut "$SMPROGRAMS\Speediance FIT Exporter\Speediance FIT Exporter.lnk" "$INSTDIR\SpeedianceFITExporter.exe"
 CreateShortCut "$SMPROGRAMS\Speediance FIT Exporter\Deinstallieren.lnk" "$INSTDIR\Uninstall.exe"
SectionEnd
Section "Uninstall"
 Delete "$INSTDIR\SpeedianceFITExporter.exe"
 Delete "$INSTDIR\Uninstall.exe"
 RMDir "$INSTDIR"
 RMDir /r "$SMPROGRAMS\Speediance FIT Exporter"
SectionEnd
