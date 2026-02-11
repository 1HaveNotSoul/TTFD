using System;
using System.IO;
using System.Collections.Generic;
using TTFD.Cleaner.Cli.Models;
using TTFD.Cleaner.Cli.Utils;

namespace TTFD.Cleaner.Cli.Commands;

public static class StatusCommand
{
    public static int Execute(string[] args)
    {
        try
        {
            var info = new SystemInfo
            {
                WindowsVersion = WindowsVersion.GetVersion(),
                IsAdmin = AdminChecker.IsAdmin(),
                UserName = Environment.UserName,
                ComputerName = Environment.MachineName,
                Browsers = DetectBrowsers()
            };

            JsonHelper.WriteSuccess(info);
            return 0;
        }
        catch (Exception ex)
        {
            JsonHelper.WriteError($"Failed to get system info: {ex.Message}");
            return 1;
        }
    }

    private static List<string> DetectBrowsers()
    {
        var browsers = new List<string>();
        var paths = new Dictionary<string, string>
        {
            { "Chrome", @"Google\Chrome\Application\chrome.exe" },
            { "Firefox", @"Mozilla Firefox\firefox.exe" },
            { "Edge", @"Microsoft\Edge\Application\msedge.exe" },
            { "Opera", @"Opera\launcher.exe" },
            { "Brave", @"BraveSoftware\Brave-Browser\Application\brave.exe" }
        };

        var programFiles = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles);
        var programFilesX86 = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86);

        foreach (var (name, relativePath) in paths)
        {
            var path1 = Path.Combine(programFiles, relativePath);
            var path2 = Path.Combine(programFilesX86, relativePath);

            if (File.Exists(path1) || File.Exists(path2))
            {
                browsers.Add(name);
            }
        }

        return browsers;
    }
}
