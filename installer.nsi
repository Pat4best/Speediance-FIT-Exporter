Unicode True
Name "Speediance FIT Exporter 0.1.35-rc.1"
OutFile "dist\SpeedianceFITExporter-Setup.exe"
VIProductVersion "0.1.35.1"
VIAddVersionKey "ProductName" "Speediance FIT Exporter"
VIAddVersionKey "FileDescription" "Speediance FIT Exporter Release Candidate Installer"
VIAddVersionKey "ProductVersion" "0.1.35-rc.1"
InstallDir "$LOCALAPPDATA\Programs\Speediance FIT Exporter"
RequestExecutionLevel user
Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles
Section "Install"
 SetOutPath "$INSTDIR"
 File "dist\SpeedianceFITExporter.exe"
 File "README.md"
 File "CHANGELOG.md"
 SetOutPath "$INSTDIR\docs"
 File "docs\Benutzerhandbuch.md"
 File "docs\Quick_Start_EN.md"
 File "docs\Bekannte_Einschraenkungen.md"
 File "docs\Drittquellen.md"
 SetOutPath "$INSTDIR"
 WriteUninstaller "$INSTDIR\Uninstall.exe"
 CreateDirectory "$SMPROGRAMS\Speediance FIT Exporter"
 CreateShortCut "$SMPROGRAMS\Speediance FIT Exporter\Speediance FIT Exporter.lnk" "$INSTDIR\SpeedianceFITExporter.exe"
 CreateShortCut "$SMPROGRAMS\Speediance FIT Exporter\Benutzerhandbuch.lnk" "$WINDIR\notepad.exe" '$\"$INSTDIR\docs\Benutzerhandbuch.md$\"'
 CreateShortCut "$SMPROGRAMS\Speediance FIT Exporter\Quick Start (English).lnk" "$WINDIR\notepad.exe" '$\"$INSTDIR\docs\Quick_Start_EN.md$\"'
 CreateShortCut "$SMPROGRAMS\Speediance FIT Exporter\Deinstallieren.lnk" "$INSTDIR\Uninstall.exe"
SectionEnd
Section "Uninstall"
 Delete "$INSTDIR\SpeedianceFITExporter.exe"
 Delete "$INSTDIR\README.md"
 Delete "$INSTDIR\CHANGELOG.md"
 Delete "$INSTDIR\docs\Benutzerhandbuch.md"
 Delete "$INSTDIR\docs\Quick_Start_EN.md"
 Delete "$INSTDIR\docs\Bekannte_Einschraenkungen.md"
 Delete "$INSTDIR\docs\Drittquellen.md"
 RMDir "$INSTDIR\docs"
 Delete "$INSTDIR\Uninstall.exe"
 RMDir "$INSTDIR"
 RMDir /r "$SMPROGRAMS\Speediance FIT Exporter"
 ; User credentials, settings, completed-workout cache and FIT exports live
 ; separately and are deliberately not deleted by application uninstall.
SectionEnd
