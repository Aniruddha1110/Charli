; installer.nsh — Custom NSIS installer additions

!macro customInstall
  ; Create desktop shortcut with icon
  CreateShortCut "$DESKTOP\Charli.lnk" "$INSTDIR\Charli.exe" "" "$INSTDIR\Charli.exe" 0

  ; Add to Windows startup (optional — user can disable in Settings)
  ; WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "Charli" "$INSTDIR\Charli.exe --hidden"
!macroend

!macro customUnInstall
  ; Remove desktop shortcut
  Delete "$DESKTOP\Charli.lnk"

  ; Remove from startup
  DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "Charli"
!macroend