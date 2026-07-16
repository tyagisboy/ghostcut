!define APP_NAME "GhostCut Offline"
!define COMP_NAME "OpenSourceDev"
!define VERSION "1.0.0"
!define INSTALL_DIR "$PROGRAMFILES64\GhostCutOffline"

Name "${APP_NAME}"
OutFile "GhostCut_Offline_Setup_v${VERSION}.exe"
InstallDir "${INSTALL_DIR}"
Icon "..\\src\\gui\\assets\\app_icon.ico"

SetCompressor /SOLID lzma
Page Directory
Page InstFiles

Section "Install Components"
    SetOutPath "$INSTDIR"
    
    ; Ingest full build output directory from PyInstaller distribution bundle
    File /r "..\\dist\\GhostCutOffline\\*"

    ; Establish clean Windows system shortcuts
    CreateDirectory "$SMPROGRAMS\GhostCut Offline"
    CreateShortCut "$SMPROGRAMS\GhostCut Offline\GhostCut Offline.lnk" "$INSTDIR\GhostCutOffline.exe"
    CreateShortCut "$DESKTOP\GhostCut Offline.lnk" "$INSTDIR\GhostCutOffline.exe"

    ; Write registry entries for native Windows uninstallation routing
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\GhostCutOffline" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\GhostCutOffline" "UninstallString" "$INSTDIR\uninstall.exe"
    
    WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

Section "Uninstall"
    ; Remove system links
    Delete "$DESKTOP\GhostCut Offline.lnk"
    Delete "$SMPROGRAMS\GhostCut Offline\*.lnk"
    RMDir "$SMPROGRAMS\GhostCut Offline"

    ; Clean out full structural directory trees
    RMDir /r "$INSTDIR"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\GhostCutOffline"
SectionEnd
