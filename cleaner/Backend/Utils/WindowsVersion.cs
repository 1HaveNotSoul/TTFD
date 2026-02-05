using System;
using Microsoft.Win32;

namespace TTFD.Cleaner.Cli.Utils;

public static class WindowsVersion
{
    public static string GetVersion()
    {
        try
        {
            using var key = Registry.LocalMachine.OpenSubKey(@"SOFTWARE\Microsoft\Windows NT\CurrentVersion");
            if (key != null)
            {
                var productName = key.GetValue("ProductName")?.ToString() ?? "Unknown";
                var build = key.GetValue("CurrentBuild")?.ToString() ?? "";
                return $"{productName} (Build {build})";
            }
        }
        catch { }
        
        return Environment.OSVersion.ToString();
    }
}
