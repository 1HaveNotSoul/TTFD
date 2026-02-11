namespace TTFD.Cleaner.Cli.Models;

public class AppInfo
{
    public string Name { get; set; } = string.Empty;
    public string Publisher { get; set; } = string.Empty;
    public long Size { get; set; }
    public string Package { get; set; } = string.Empty;
    public string Version { get; set; } = string.Empty;
}
