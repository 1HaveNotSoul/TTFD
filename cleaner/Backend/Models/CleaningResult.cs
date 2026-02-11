using System.Collections.Generic;

namespace TTFD.Cleaner.Cli.Models;

public class CleaningResult
{
    public Dictionary<string, CategoryResult> Categories { get; set; } = new();
    public long TotalSize { get; set; }
    public int TotalFiles { get; set; }
}

public class CategoryResult
{
    public int Files { get; set; }
    public long Size { get; set; }
    public List<string> Paths { get; set; } = new();
}
