using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using Microsoft.Win32;
using TTFD.Cleaner.Cli.Models;
using TTFD.Cleaner.Cli.Utils;

namespace TTFD.Cleaner.Cli.Commands;

public static class StartupCommand
{
    private static readonly string[] ProtectedNames = new[]
    {
        "SecurityHealth", "Windows Defender", "OneDrive", "WindowsDefender", "MsMpEng"
    };

    public static int List(string[] args)
    {
        try
        {
            var items = new List<StartupItem>();

            // LOGON - Registry Run keys
            items.AddRange(GetRegistryStartupItems(@"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", "HKCU Run", false));
            items.AddRange(GetRegistryStartupItems(@"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce", "HKCU RunOnce", false));
            
            if (AdminChecker.IsAdmin())
            {
                items.AddRange(GetRegistryStartupItems(@"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", "HKLM Run", true));
                items.AddRange(GetRegistryStartupItems(@"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce", "HKLM RunOnce", true));
            }

            // LOGON - Startup folders
            var startupUser = Environment.GetFolderPath(Environment.SpecialFolder.Startup);
            var startupCommon = Environment.GetFolderPath(Environment.SpecialFolder.CommonStartup);
            items.AddRange(GetFolderStartupItems(startupUser, "User Startup"));
            if (AdminChecker.IsAdmin())
            {
                items.AddRange(GetFolderStartupItems(startupCommon, "Common Startup"));
            }

            // EXPLORER - Shell folders
            items.AddRange(GetRegistryStartupItems(@"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders", "Shell Folders", false));
            items.AddRange(GetRegistryStartupItems(@"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders", "User Shell Folders", false));

            // SERVICES - Windows Services (только если админ)
            if (AdminChecker.IsAdmin())
            {
                items.AddRange(StartupCommandHelpers.GetServicesStartupItems());
            }

            // SCHEDULED TASKS
            items.AddRange(StartupCommandHelpers.GetScheduledTasksStartupItems());

            // DRIVERS (только если админ)
            if (AdminChecker.IsAdmin())
            {
                items.AddRange(StartupCommandHelpers.GetDriversStartupItems());
            }

            // WINLOGON
            items.AddRange(StartupCommandHelpers.GetWinlogonStartupItems());

            // BROWSER HELPER OBJECTS
            items.AddRange(StartupCommandHelpers.GetBHOStartupItems());

            // CODECS
            items.AddRange(StartupCommandHelpers.GetCodecsStartupItems());

            // PRINT MONITORS
            if (AdminChecker.IsAdmin())
            {
                items.AddRange(StartupCommandHelpers.GetPrintMonitorsStartupItems());
            }

            // LSA PROVIDERS (read-only)
            items.AddRange(StartupCommandHelpers.GetLSAProvidersStartupItems());

            // BOOT EXECUTE
            if (AdminChecker.IsAdmin())
            {
                items.AddRange(StartupCommandHelpers.GetBootExecuteStartupItems());
            }

            JsonHelper.WriteSuccess(items);
            return 0;
        }
        catch (Exception ex)
        {
            JsonHelper.WriteError($"Failed to list startup items: {ex.Message}");
            return 1;
        }
    }

    public static int Set(string[] args)
    {
        try
        {
            string? id = null;
            bool? enabled = null;

            for (int i = 0; i < args.Length; i++)
            {
                if (args[i] == "--id" && i + 1 < args.Length)
                    id = args[i + 1];
                if (args[i] == "--enabled" && i + 1 < args.Length)
                    enabled = bool.Parse(args[i + 1]);
            }

            if (string.IsNullOrEmpty(id) || !enabled.HasValue)
            {
                JsonHelper.WriteError("Missing --id or --enabled parameter");
                return 1;
            }

            // Parse ID: "type:name"
            var parts = id.Split(':', 2);
            if (parts.Length != 2)
            {
                JsonHelper.WriteError("Invalid ID format");
                return 1;
            }

            var type = parts[0];
            var name = parts[1];

            // Disable by renaming registry value or moving file
            if (type.Contains("Run"))
            {
                var isHKLM = type.Contains("HKLM");
                var keyPath = type.Contains("RunOnce") 
                    ? @"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"
                    : @"SOFTWARE\Microsoft\Windows\CurrentVersion\Run";
                
                var baseKey = isHKLM ? Registry.LocalMachine : Registry.CurrentUser;
                using var key = baseKey.OpenSubKey(keyPath, true);
                
                if (key != null)
                {
                    if (enabled.Value)
                    {
                        // Enable: rename from "name_disabled" to "name"
                        var disabledName = name + "_disabled";
                        var value = key.GetValue(disabledName);
                        if (value != null)
                        {
                            key.SetValue(name, value);
                            key.DeleteValue(disabledName);
                        }
                    }
                    else
                    {
                        // Disable: rename from "name" to "name_disabled"
                        var value = key.GetValue(name);
                        if (value != null)
                        {
                            key.SetValue(name + "_disabled", value);
                            key.DeleteValue(name);
                        }
                    }
                }
            }

            JsonHelper.WriteSuccess(new { message = "Startup item updated" });
            return 0;
        }
        catch (Exception ex)
        {
            JsonHelper.WriteError($"Failed to set startup item: {ex.Message}");
            return 1;
        }
    }


    private static List<StartupItem> GetRegistryStartupItems(string keyPath, string type, bool useLM = false)
    {
        var items = new List<StartupItem>();

        try
        {
            var baseKey = useLM ? Registry.LocalMachine : Registry.CurrentUser;
            using var key = baseKey.OpenSubKey(keyPath);
            
            if (key != null)
            {
                foreach (var valueName in key.GetValueNames())
                {
                    var value = key.GetValue(valueName)?.ToString() ?? "";
                    var isProtected = ProtectedNames.Any(p => valueName.Contains(p, StringComparison.OrdinalIgnoreCase));

                    items.Add(new StartupItem
                    {
                        Id = $"{type}:{valueName}",
                        Name = valueName,
                        Location = value,
                        Enabled = true,
                        Type = type,
                        IsSystemProtected = isProtected
                    });
                }
            }
        }
        catch { }

        return items;
    }

    private static List<StartupItem> GetFolderStartupItems(string folderPath, string type)
    {
        var items = new List<StartupItem>();

        try
        {
            if (Directory.Exists(folderPath))
            {
                foreach (var file in Directory.GetFiles(folderPath))
                {
                    var fileName = Path.GetFileName(file);
                    items.Add(new StartupItem
                    {
                        Id = $"{type}:{fileName}",
                        Name = fileName,
                        Location = file,
                        Enabled = true,
                        Type = type,
                        IsSystemProtected = false
                    });
                }
            }
        }
        catch { }

        return items;
    }
}
