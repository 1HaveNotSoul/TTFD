namespace TTFD.Cleaner.Models
{
    public class ServiceInfo
    {
        public string Name { get; set; } = "";
        public string DisplayName { get; set; } = "";
        public string Status { get; set; } = "";
        public string StartType { get; set; } = "";
        public string Category { get; set; } = "";
        public bool IsProtected { get; set; }
        public bool IsRunning { get; set; }
        public bool IsAutoStart { get; set; }
        public bool CanStop { get; set; }
        public string Description { get; set; } = "";
    }
}
