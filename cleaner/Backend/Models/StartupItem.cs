namespace TTFD.Cleaner.Cli.Models;

public class StartupItem
{
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string Location { get; set; } = string.Empty;
    public bool Enabled { get; set; }
    public string Type { get; set; } = string.Empty;
    public bool IsSystemProtected { get; set; }
}
