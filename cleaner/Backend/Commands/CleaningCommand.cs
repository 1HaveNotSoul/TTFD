using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using TTFD.Cleaner.Cli.Models;
using TTFD.Cleaner.Cli.Utils;

namespace TTFD.Cleaner.Cli.Commands;

public static class CleaningCommand
{
    public static int Scan(string[] args)
    {
        try
        {
            var categories = ParseCategories(args);
            var result = new CleaningResult();

            foreach (var category in categories)
            {
                var categoryResult = ScanCategory(category);
                result.Categories[category] = categoryResult;
                result.TotalFiles += categoryResult.Files;
                result.TotalSize += categoryResult.Size;
            }

            JsonHelper.WriteSuccess(result);
            return 0;
        }
        catch (Exception ex)
        {
            JsonHelper.WriteError($"Scan failed: {ex.Message}");
            return 1;
        }
    }

    public static int Apply(string[] args)
    {
        try
        {
            var categories = ParseCategories(args);
            var result = new CleaningResult();

            foreach (var category in categories)
            {
                var categoryResult = CleanCategory(category);
                result.Categories[category] = categoryResult;
                result.TotalFiles += categoryResult.Files;
                result.TotalSize += categoryResult.Size;
            }

            JsonHelper.WriteSuccess(result);
            return 0;
        }
        catch (Exception ex)
        {
            JsonHelper.WriteError($"Cleaning failed: {ex.Message}");
            return 1;
        }
    }


    private static List<string> ParseCategories(string[] args)
    {
        for (int i = 0; i < args.Length; i++)
        {
            if (args[i] == "--categories" && i + 1 < args.Length)
            {
                return args[i + 1].Split(',').Select(c => c.Trim()).ToList();
            }
        }
        return new List<string>();
    }

    private static CategoryResult ScanCategory(string category)
    {
        var result = new CategoryResult();
        var paths = GetCategoryPaths(category);

        foreach (var path in paths)
        {
            if (Directory.Exists(path))
            {
                try
                {
                    var files = Directory.GetFiles(path, "*", SearchOption.AllDirectories);
                    foreach (var file in files)
                    {
                        try
                        {
                            var fileInfo = new FileInfo(file);
                            result.Files++;
                            result.Size += fileInfo.Length;
                        }
                        catch { }
                    }
                    result.Paths.Add(path);
                }
                catch { }
            }
        }

        return result;
    }

    private static CategoryResult CleanCategory(string category)
    {
        var result = new CategoryResult();
        var paths = GetCategoryPaths(category);

        foreach (var path in paths)
        {
            if (Directory.Exists(path))
            {
                try
                {
                    var files = Directory.GetFiles(path, "*", SearchOption.AllDirectories);
                    foreach (var file in files)
                    {
                        try
                        {
                            var fileInfo = new FileInfo(file);
                            result.Files++;
                            result.Size += fileInfo.Length;
                            File.Delete(file);
                        }
                        catch { }
                    }
                    result.Paths.Add(path);
                }
                catch { }
            }
        }

        return result;
    }


    private static List<string> GetCategoryPaths(string category)
    {
        var paths = new List<string>();
        var temp = Path.GetTempPath();
        var localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        var programData = Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData);
        var winDir = Environment.GetFolderPath(Environment.SpecialFolder.Windows);

        switch (category.ToLower())
        {
            case "temp":
                paths.Add(temp);
                paths.Add(Path.Combine(localAppData, "Temp"));
                break;

            case "cache":
                paths.Add(Path.Combine(localAppData, "Microsoft", "Windows", "INetCache"));
                paths.Add(Path.Combine(localAppData, "Microsoft", "Windows", "WebCache"));
                break;

            case "recycle":
                // Recycle bin - special handling needed
                break;

            case "dumps":
                paths.Add(Path.Combine(localAppData, "CrashDumps"));
                paths.Add(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "AppData", "Local", "CrashDumps"));
                break;

            case "logs":
                paths.Add(Path.Combine(localAppData, "Logs"));
                break;

            case "downloads":
                paths.Add(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile) + "\\Downloads");
                break;

            // NEW CATEGORIES
            
            case "windows-update":
                // Windows Update Cache (requires admin + service stop)
                paths.Add(Path.Combine(winDir, "SoftwareDistribution", "Download"));
                paths.Add(Path.Combine(winDir, "DeliveryOptimization"));
                break;

            case "thumbnails":
                // Thumbnail cache (safe)
                paths.Add(Path.Combine(localAppData, "Microsoft", "Windows", "Explorer"));
                break;

            case "nvidia-cache":
                // NVIDIA driver cache (safe)
                paths.Add(Path.Combine(programData, "NVIDIA Corporation", "Downloader"));
                paths.Add(Path.Combine(programData, "NVIDIA Corporation", "NvBackend"));
                paths.Add(Path.Combine(localAppData, "NVIDIA", "DXCache"));
                paths.Add(Path.Combine(localAppData, "NVIDIA", "GLCache"));
                break;

            case "amd-cache":
                // AMD driver cache (safe)
                paths.Add("C:\\AMD");
                paths.Add(Path.Combine(programData, "AMD"));
                paths.Add(Path.Combine(localAppData, "AMD"));
                break;

            case "intel-cache":
                // Intel driver cache (safe)
                paths.Add(Path.Combine(programData, "Intel"));
                paths.Add(Path.Combine(localAppData, "Intel"));
                break;

            case "windows-search":
                // Windows Search index (will rebuild)
                paths.Add(Path.Combine(programData, "Microsoft", "Search", "Data"));
                break;

            case "store-cache":
                // Microsoft Store cache (safe, fixes issues)
                var packages = Path.Combine(localAppData, "Packages");
                if (Directory.Exists(packages))
                {
                    var storeDirs = Directory.GetDirectories(packages, "Microsoft.WindowsStore_*");
                    foreach (var dir in storeDirs)
                    {
                        paths.Add(Path.Combine(dir, "LocalCache"));
                        paths.Add(Path.Combine(dir, "AC", "Temp"));
                    }
                }
                break;

            case "event-logs":
                // Windows Event Logs (requires admin)
                paths.Add(Path.Combine(winDir, "System32", "winevt", "Logs"));
                break;

            case "delivery-optimization":
                // Delivery Optimization files
                paths.Add(Path.Combine(winDir, "ServiceProfiles", "NetworkService", "AppData", "Local", "Microsoft", "Windows", "DeliveryOptimization"));
                break;

            case "font-cache":
                // Font cache (safe to rebuild)
                paths.Add(Path.Combine(winDir, "ServiceProfiles", "LocalService", "AppData", "Local", "FontCache"));
                break;

            case "icon-cache":
                // Icon cache (safe)
                paths.Add(Path.Combine(localAppData, "IconCache.db"));
                break;

            case "shader-cache":
                // DirectX shader cache (safe, will rebuild)
                paths.Add(Path.Combine(localAppData, "D3DSCache"));
                paths.Add(Path.Combine(localAppData, "NVIDIA", "DXCache"));
                paths.Add(Path.Combine(localAppData, "AMD", "DxCache"));
                break;

            case "memory-dumps":
                // Memory dumps (safe if not debugging)
                paths.Add(Path.Combine(winDir, "Minidump"));
                paths.Add(Path.Combine(winDir, "MEMORY.DMP"));
                break;

            case "error-reports":
                // Windows Error Reporting
                paths.Add(Path.Combine(programData, "Microsoft", "Windows", "WER"));
                paths.Add(Path.Combine(localAppData, "Microsoft", "Windows", "WER"));
                break;
        }

        return paths.Where(p => !string.IsNullOrEmpty(p)).ToList();
    }
}
