using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.ServiceProcess;
using Microsoft.Win32;
using TTFD.Cleaner.Cli.Models;

namespace TTFD.Cleaner.Cli.Commands;

public static class StartupCommandHelpers
{
    public static List<StartupItem> GetServicesStartupItems()
    {
        var items = new List<StartupItem>();
        try
        {
            var services = ServiceController.GetServices()
                .Where(s => s.StartType == ServiceStartMode.Automatic)
                .Take(50); // Limit to avoid too many items

            foreach (var service in services)
            {
                items.Add(new StartupItem
                {
                    Id = $"Service:{service.ServiceName}",
                    Name = service.DisplayName,
                    Location = service.ServiceName,
                    Enabled = service.Status == ServiceControllerStatus.Running,
                    Type = "Service",
                    IsSystemProtected = true // Services are protected
                });
            }
        }
        catch { }
        return items;
    }

    public static List<StartupItem> GetScheduledTasksStartupItems()
    {
        var items = new List<StartupItem>();
        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = "schtasks.exe",
                Arguments = "/query /fo CSV /v",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                CreateNoWindow = true
            };

            using var process = Process.Start(psi);
            if (process != null)
            {
                var output = process.StandardOutput.ReadToEnd();
                process.WaitForExit();

                // Parse CSV output (simplified)
                var lines = output.Split('\n').Skip(1).Take(20); // Limit
                foreach (var line in lines)
                {
                    if (!string.IsNullOrWhiteSpace(line))
                    {
                        var parts = line.Split(',');
                        if (parts.Length > 1)
                        {
                            items.Add(new StartupItem
                            {
                                Id = $"Task:{parts[0]}",
                                Name = parts[0].Trim('"'),
                                Location = "Scheduled Task",
                                Enabled = true,
                                Type = "Scheduled Task",
                                IsSystemProtected = false
                            });
                        }
                    }
                }
            }
        }
        catch { }
        return items;
    }

    public static List<StartupItem> GetDriversStartupItems()
    {
        var items = new List<StartupItem>();
        try
        {
            using var key = Registry.LocalMachine.OpenSubKey(@"SYSTEM\CurrentControlSet\Services");
            if (key != null)
            {
                foreach (var subKeyName in key.GetSubKeyNames().Take(30)) // Limit
                {
                    using var subKey = key.OpenSubKey(subKeyName);
                    if (subKey != null)
                    {
                        var type = subKey.GetValue("Type");
                        if (type != null && (int)type == 1) // Kernel driver
                        {
                            items.Add(new StartupItem
                            {
                                Id = $"Driver:{subKeyName}",
                                Name = subKeyName,
                                Location = "Kernel Driver",
                                Enabled = true,
                                Type = "Driver",
                                IsSystemProtected = true
                            });
                        }
                    }
                }
            }
        }
        catch { }
        return items;
    }

    public static List<StartupItem> GetWinlogonStartupItems()
    {
        var items = new List<StartupItem>();
        try
        {
            using var key = Registry.LocalMachine.OpenSubKey(@"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon");
            if (key != null)
            {
                foreach (var valueName in new[] { "Shell", "Userinit", "UIHost" })
                {
                    var value = key.GetValue(valueName)?.ToString();
                    if (!string.IsNullOrEmpty(value))
                    {
                        items.Add(new StartupItem
                        {
                            Id = $"Winlogon:{valueName}",
                            Name = valueName,
                            Location = value,
                            Enabled = true,
                            Type = "Winlogon",
                            IsSystemProtected = true // Winlogon is protected
                        });
                    }
                }
            }
        }
        catch { }
        return items;
    }

    public static List<StartupItem> GetBHOStartupItems()
    {
        var items = new List<StartupItem>();
        try
        {
            using var key = Registry.LocalMachine.OpenSubKey(@"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Browser Helper Objects");
            if (key != null)
            {
                foreach (var subKeyName in key.GetSubKeyNames().Take(20))
                {
                    items.Add(new StartupItem
                    {
                        Id = $"BHO:{subKeyName}",
                        Name = subKeyName,
                        Location = "Browser Helper Object",
                        Enabled = true,
                        Type = "BHO",
                        IsSystemProtected = false
                    });
                }
            }
        }
        catch { }
        return items;
    }

    public static List<StartupItem> GetCodecsStartupItems()
    {
        var items = new List<StartupItem>();
        try
        {
            using var key = Registry.LocalMachine.OpenSubKey(@"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Drivers32");
            if (key != null)
            {
                foreach (var valueName in key.GetValueNames().Take(15))
                {
                    var value = key.GetValue(valueName)?.ToString();
                    items.Add(new StartupItem
                    {
                        Id = $"Codec:{valueName}",
                        Name = valueName,
                        Location = value ?? "",
                        Enabled = true,
                        Type = "Codec",
                        IsSystemProtected = false
                    });
                }
            }
        }
        catch { }
        return items;
    }

    public static List<StartupItem> GetPrintMonitorsStartupItems()
    {
        var items = new List<StartupItem>();
        try
        {
            using var key = Registry.LocalMachine.OpenSubKey(@"SYSTEM\CurrentControlSet\Control\Print\Monitors");
            if (key != null)
            {
                foreach (var subKeyName in key.GetSubKeyNames().Take(10))
                {
                    items.Add(new StartupItem
                    {
                        Id = $"PrintMonitor:{subKeyName}",
                        Name = subKeyName,
                        Location = "Print Monitor",
                        Enabled = true,
                        Type = "Print Monitor",
                        IsSystemProtected = true
                    });
                }
            }
        }
        catch { }
        return items;
    }

    public static List<StartupItem> GetLSAProvidersStartupItems()
    {
        var items = new List<StartupItem>();
        try
        {
            using var key = Registry.LocalMachine.OpenSubKey(@"SYSTEM\CurrentControlSet\Control\SecurityProviders");
            if (key != null)
            {
                var value = key.GetValue("SecurityProviders")?.ToString();
                if (!string.IsNullOrEmpty(value))
                {
                    items.Add(new StartupItem
                    {
                        Id = "LSA:SecurityProviders",
                        Name = "LSA Security Providers",
                        Location = value,
                        Enabled = true,
                        Type = "LSA Provider",
                        IsSystemProtected = true // LSA is protected
                    });
                }
            }
        }
        catch { }
        return items;
    }

    public static List<StartupItem> GetBootExecuteStartupItems()
    {
        var items = new List<StartupItem>();
        try
        {
            using var key = Registry.LocalMachine.OpenSubKey(@"SYSTEM\CurrentControlSet\Control\Session Manager");
            if (key != null)
            {
                var value = key.GetValue("BootExecute");
                if (value != null)
                {
                    items.Add(new StartupItem
                    {
                        Id = "Boot:BootExecute",
                        Name = "Boot Execute",
                        Location = value.ToString() ?? "",
                        Enabled = true,
                        Type = "Boot Execute",
                        IsSystemProtected = true // Boot execute is protected
                    });
                }
            }
        }
        catch { }
        return items;
    }
}
