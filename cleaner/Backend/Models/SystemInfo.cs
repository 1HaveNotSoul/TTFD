using System.Collections.Generic;

namespace TTFD.Cleaner.Cli.Models;

public class SystemInfo
{
    public string WindowsVersion { get; set; } = string.Empty;
    public bool IsAdmin { get; set; }
    public string UserName { get; set; } = string.Empty;
    public string ComputerName { get; set; } = string.Empty;
    public List<string> Browsers { get; set; } = new();
}
