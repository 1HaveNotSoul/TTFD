using System;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace TTFD.Cleaner.Cli.Utils;

public static class JsonHelper
{
    private static readonly JsonSerializerOptions Options = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        WriteIndented = false,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
    };

    public static void WriteSuccess<T>(T data)
    {
        var response = new { success = true, data };
        Console.WriteLine(JsonSerializer.Serialize(response, Options));
    }

    public static void WriteError(string message)
    {
        var response = new { success = false, error = message };
        Console.WriteLine(JsonSerializer.Serialize(response, Options));
    }
}
