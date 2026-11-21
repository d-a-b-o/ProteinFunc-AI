; Instalador de Windows para ProteinFunc AI Desktop (Inno Setup 6).
; Compilar desde la raíz del repositorio, después de PyInstaller:
;   ISCC.exe /DMyAppVersion=0.1.0 /DDistDir=C:\ruta\dist\ProteinFuncAI installer\windows\ProteinFuncAI.iss
; No requiere permisos de administrador: se instala para el usuario actual.

#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif
#ifndef DistDir
  #define DistDir "..\..\dist\ProteinFuncAI"
#endif
#define MyAppName "ProteinFunc AI Desktop"
#define MyAppExe "ProteinFuncAI.exe"

[Setup]
AppId={{6B0C6E1E-2F3A-4C59-9C1B-7E1E5A0F4D21}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher=Bioinformática USIL
DefaultDirName={autopf}\ProteinFuncAI
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\..\out
OutputBaseFilename=ProteinFuncAI-{#MyAppVersion}-windows-x64-setup
SetupIconFile=..\icon.ico
UninstallDisplayIcon={app}\{#MyAppExe}
WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"
Name: "{group}\Verificar instalación"; Filename: "{cmd}"; Parameters: "/k ""{app}\proteinfunc-check.exe"""; WorkingDir: "{app}"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExe}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
