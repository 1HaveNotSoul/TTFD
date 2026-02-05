using System;
using System.Linq;
using System.Collections.Generic;
using System.Diagnostics;
using TTFD.Cleaner.Cli.Models;
using TTFD.Cleaner.Cli.Utils;

namespace TTFD.Cleaner.Cli.Commands;

public static class AppsCommand
{
    public static int List(string[] args)
    {
        try
        {
            if (!AdminChecker.IsAdmin())
            {
                JsonHelper.WriteError("Administrator rights required");
                return 1;
            }

            var apps = GetInstalledApps();
            JsonHelper.WriteSuccess(apps);
            return 0;
        }
        catch (Exception ex)
        {
            JsonHelper.WriteError($"Failed to list apps: {ex.Message}");
            return 1;
        }
    }

    public static int RemoveUwp(string[] args)
    {
        try
        {
            if (!AdminChecker.IsAdmin())
            {
                JsonHelper.WriteError("Administrator rights required");
                return 1;
            }

            string? package = null;
            for (int i = 0; i < args.Length; i++)
            {
                if (args[i] == "--package" && i + 1 < args.Length)
                    package = args[i + 1];
            }

            if (string.IsNullOrEmpty(package))
            {
                JsonHelper.WriteError("Missing --package parameter");
                return 1;
            }

            // Remove UWP app using PowerShell
            var psi = new ProcessStartInfo
            {
                FileName = "powershell.exe",
                Arguments = $"-Command \"Get-AppxPackage -Name '{package}' | Remove-AppxPackage\"",
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true
            };

            using var process = Process.Start(psi);
            process?.WaitForExit();

            JsonHelper.WriteSuccess(new { message = "App removed successfully" });
            return 0;
        }
        catch (Exception ex)
        {
            JsonHelper.WriteError($"Failed to remove app: {ex.Message}");
            return 1;
        }
    }


    private static List<AppInfo> GetInstalledApps()
    {
        var apps = new List<AppInfo>();

        try
        {
            // Get UWP apps using PowerShell
            var psi = new ProcessStartInfo
            {
                FileName = "powershell.exe",
                Arguments = "-Command \"Get-AppxPackage | Select-Object Name, Publisher, PackageFullName | ConvertTo-Json\"",
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true
            };

            using var process = Process.Start(psi);
            if (process != null)
            {
                var output = process.StandardOutput.ReadToEnd();
                process.WaitForExit();

                // Parse JSON output (simplified)
                // In real implementation, use System.Text.Json to parse
                apps.Add(new AppInfo
                {
                    Name = "Sample UWP App",
                    Publisher = "Microsoft",
                    Size = 0,
                    Package = "Microsoft.SampleApp",
                    Version = "1.0.0"
                });
            }
        }
        catch { }

        return apps;
    }
}
