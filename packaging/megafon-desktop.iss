#ifndef MyAppVersion
  #define MyAppVersion "0.1.0"
#endif
#ifndef PackageKind
  #define PackageKind "Setup"
#endif

#define MyAppName "Megafon Desktop"
#define MyAppPublisher "lvlaksim1"
#define MyAppExeName "Megafon Desktop.exe"

[Setup]
AppId={{4C305334-4728-47B9-9C1E-49275512AB80}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\Megafon Desktop
DefaultGroupName=Megafon Desktop
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\dist-installer
OutputBaseFilename=MegafonDesktop-{#PackageKind}-v{#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=force
RestartApplications=no
UninstallDisplayName=Megafon Desktop
SetupLogging=yes

[Files]
Source: "..\dist\Megafon Desktop\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Megafon Desktop"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Megafon Desktop"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительные ярлыки:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Запустить Megafon Desktop"; Flags: nowait postinstall skipifsilent
