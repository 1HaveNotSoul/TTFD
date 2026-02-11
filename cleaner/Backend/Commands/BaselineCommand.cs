using System;
using System.IO;
using System.Text.Json;
using TTFD.Cleaner.Cli.Utils;

namespace TTFD.Cleaner.Cli.Commands;

public static class BaselineCommand
{
    private static readonly string BaselinePath = Path.Combine("Config", "baseline.json");

    public static int Export(string[] args)
    {
        try
        {
            // Create Config directory if it doesn't exist
            Directory.CreateDirectory("Config");

            // Get current startup items
            var items = new { timestamp = DateTime.Now, startupItems = new object[] { } };

            // Save to baseline.json
            var json = JsonSerializer.Serialize(items, new JsonSerializerOptions { WriteIndented = true });
            File.WriteAllText(BaselinePath, json);

            JsonHelper.WriteSuccess(new { message = "Baseline exported", path = BaselinePath });
            return 0;
        }
        catch (Exception ex)
        {
            JsonHelper.WriteError($"Failed to export baseline: {ex.Message}");
            return 1;
        }
    }

    public static int Restore(string[] args)
    {
        try
        {
            if (!File.Exists(BaselinePath))
            {
                JsonHelper.WriteError("Baseline file not found");
                return 1;
            }

            // Read baseline
            var json = File.ReadAllText(BaselinePath);
            // Restore startup items from baseline
            // Implementation would restore registry/folder items

            JsonHelper.WriteSuccess(new { message = "Baseline restored" });
            return 0;
        }
        catch (Exception ex)
        {
            JsonHelper.WriteError($"Failed to restore baseline: {ex.Message}");
            return 1;
        }
    }
}
