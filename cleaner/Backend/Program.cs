using System;
using System.Text.Json;
using TTFD.Cleaner.Cli.Commands;
using TTFD.Cleaner.Cli.Utils;
using TTFD.Cleaner.Commands;

namespace TTFD.Cleaner.Cli;

class Program
{
    static int Main(string[] args)
    {
        try
        {
            if (args.Length == 0)
            {
                PrintHelp();
                return 0;
            }

            var command = args[0].ToLower();

            return command switch
            {
                "status" => StatusCommand.Execute(args),
                "scan-cleaning" => CleaningCommand.Scan(args),
                "apply-cleaning" => CleaningCommand.Apply(args),
                "list-startup" => StartupCommand.List(args),
                "set-startup" => StartupCommand.Set(args),
                "services" => ServicesCommand.Execute(args),
                "list-apps" => AppsCommand.List(args),
                "remove-uwp" => AppsCommand.RemoveUwp(args),
                "export-baseline" => BaselineCommand.Export(args),
                "restore-baseline" => BaselineCommand.Restore(args),
                "help" or "--help" or "-h" => PrintHelp(),
                _ => PrintError($"Unknown command: {command}")
            };
        }
        catch (Exception ex)
        {
            return PrintError($"Fatal error: {ex.Message}");
        }
    }

    static int PrintHelp()
    {
        Console.WriteLine("TTFD-Cleaner CLI v1.3.0");
        Console.WriteLine();
        Console.WriteLine("Commands:");
        Console.WriteLine("  status                    - System information");
        Console.WriteLine("  scan-cleaning             - Scan for cleaning (dry-run)");
        Console.WriteLine("  apply-cleaning            - Apply cleaning");
        Console.WriteLine("  list-startup              - List startup items");
        Console.WriteLine("  set-startup               - Enable/disable startup item");
        Console.WriteLine("  services list [category]  - List services");
        Console.WriteLine("  services set-status       - Enable/disable service");
        Console.WriteLine("  services categories       - List service categories");
        Console.WriteLine("  list-apps                 - List installed apps");
        Console.WriteLine("  remove-uwp                - Remove UWP app");
        Console.WriteLine("  export-baseline           - Export system baseline");
        Console.WriteLine("  restore-baseline          - Restore from baseline");
        return 0;
    }

    static int PrintError(string message)
    {
        var response = new { success = false, error = message };
        Console.WriteLine(JsonSerializer.Serialize(response));
        return 1;
    }
}
