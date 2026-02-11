using System;
using System.Collections.Generic;
using System.Linq;
using System.ServiceProcess;
using System.Text.Json;
using TTFD.Cleaner.Models;

namespace TTFD.Cleaner.Commands
{
    public class ServicesCommand
    {
        // Защищённые службы (нельзя отключать)
        private static readonly HashSet<string> ProtectedServices = new(StringComparer.OrdinalIgnoreCase)
        {
            // Критические системные службы
            "WinDefend",           // Windows Defender
            "SecurityHealthService", // Security Health
            "wscsvc",              // Security Center
            "EventLog",            // Event Log
            "RpcSs",               // RPC
            "DcomLaunch",          // DCOM Server Process Launcher
            "PlugPlay",            // Plug and Play
            "Power",               // Power
            "ProfSvc",             // User Profile Service
            "Schedule",            // Task Scheduler
            "SENS",                // System Event Notification Service
            "Themes",              // Themes
            "UserManager",         // User Manager
            "Winmgmt",             // Windows Management Instrumentation
            "WlanSvc",             // WLAN AutoConfig (если используется WiFi)
            "Dhcp",                // DHCP Client
            "Dnscache",            // DNS Client
            "LanmanWorkstation",   // Workstation
            "LanmanServer",        // Server
            "NlaSvc",              // Network Location Awareness
            "nsi",                 // Network Store Interface Service
            "BFE",                 // Base Filtering Engine
            "MpsSvc",              // Windows Firewall
            "WinHttpAutoProxySvc", // WinHTTP Web Proxy Auto-Discovery Service
            "Wcmsvc",              // Windows Connection Manager
            "AudioSrv",            // Windows Audio
            "AudioEndpointBuilder" // Windows Audio Endpoint Builder
        };

        // Категории служб
        public static class ServiceCategories
        {
            public const string Telemetry = "telemetry";
            public const string Diagnostics = "diagnostics";
            public const string Xbox = "xbox";
            public const string Bluetooth = "bluetooth";
            public const string Printer = "printer";
            public const string Maps = "maps";
            public const string Biometrics = "biometrics";
            public const string Fax = "fax";
            public const string RemoteDesktop = "remote-desktop";
            public const string WindowsUpdate = "windows-update";
        }

        // Определение категорий служб
        private static readonly Dictionary<string, List<string>> ServicesByCategory = new()
        {
            [ServiceCategories.Telemetry] = new()
            {
                "DiagTrack",              // Connected User Experiences and Telemetry
                "dmwappushservice"        // Device Management Wireless Application Protocol
            },
            [ServiceCategories.Diagnostics] = new()
            {
                "diagsvc",                // Diagnostic Execution Service
                "DPS",                    // Diagnostic Policy Service
                "diagnosticshub.standardcollector.service", // Microsoft Diagnostics Hub
                "WdiServiceHost",         // Diagnostic Service Host
                "WdiSystemHost"           // Diagnostic System Host
            },
            [ServiceCategories.Xbox] = new()
            {
                "XblAuthManager",         // Xbox Live Auth Manager
                "XblGameSave",            // Xbox Live Game Save
                "XboxGipSvc",             // Xbox Accessory Management Service
                "XboxNetApiSvc"           // Xbox Live Networking Service
            },
            [ServiceCategories.Bluetooth] = new()
            {
                "bthserv",                // Bluetooth Support Service
                "BthAvctpSvc"             // AVCTP service
            },
            [ServiceCategories.Printer] = new()
            {
                "Spooler",                // Print Spooler
                "PrintNotify"             // Printer Extensions and Notifications
            },
            [ServiceCategories.Maps] = new()
            {
                "MapsBroker",             // Downloaded Maps Manager
                "lfsvc"                   // Geolocation Service
            },
            [ServiceCategories.Biometrics] = new()
            {
                "WbioSrvc"                // Windows Biometric Service
            },
            [ServiceCategories.Fax] = new()
            {
                "Fax"                     // Fax
            },
            [ServiceCategories.RemoteDesktop] = new()
            {
                "TermService",            // Remote Desktop Services
                "SessionEnv",             // Remote Desktop Configuration
                "UmRdpService"            // Remote Desktop Services UserMode Port Redirector
            },
            [ServiceCategories.WindowsUpdate] = new()
            {
                "wuauserv",               // Windows Update
                "UsoSvc"                  // Update Orchestrator Service
            }
        };

        public static int Execute(string[] args)
        {
            if (args.Length < 2)
            {
                Console.WriteLine(JsonSerializer.Serialize(new { error = "Missing subcommand" }));
                return 1;
            }

            string subcommand = args[1];

            try
            {
                switch (subcommand)
                {
                    case "list":
                        ListServices(args.Length > 2 ? args[2] : null);
                        break;
                    case "set-status":
                        if (args.Length < 4)
                        {
                            Console.WriteLine(JsonSerializer.Serialize(new { error = "Usage: services set-status <service-name> <enable|disable>" }));
                            return 1;
                        }
                        SetServiceStatus(args[2], args[3]);
                        break;
                    case "categories":
                        ListCategories();
                        break;
                    default:
                        Console.WriteLine(JsonSerializer.Serialize(new { error = $"Unknown subcommand: {subcommand}" }));
                        return 1;
                }
                return 0;
            }
            catch (Exception ex)
            {
                Console.WriteLine(JsonSerializer.Serialize(new { error = ex.Message }));
                return 1;
            }
        }

        private static void ListServices(string? category)
        {
            var services = new List<ServiceInfo>();

            if (category != null && ServicesByCategory.ContainsKey(category))
            {
                // Список служб конкретной категории
                foreach (var serviceName in ServicesByCategory[category])
                {
                    try
                    {
                        using var service = new ServiceController(serviceName);
                        services.Add(CreateServiceInfo(service, category));
                    }
                    catch
                    {
                        // Служба не найдена - пропускаем
                    }
                }
            }
            else
            {
                // Список всех служб из всех категорий
                foreach (var kvp in ServicesByCategory)
                {
                    foreach (var serviceName in kvp.Value)
                    {
                        try
                        {
                            using var service = new ServiceController(serviceName);
                            services.Add(CreateServiceInfo(service, kvp.Key));
                        }
                        catch
                        {
                            // Служба не найдена - пропускаем
                        }
                    }
                }
            }

            Console.WriteLine(JsonSerializer.Serialize(new { services }));
        }

        private static ServiceInfo CreateServiceInfo(ServiceController service, string category)
        {
            bool isProtected = ProtectedServices.Contains(service.ServiceName);
            bool isRunning = service.Status == ServiceControllerStatus.Running;
            bool isAutoStart = service.StartType == ServiceStartMode.Automatic;

            return new ServiceInfo
            {
                Name = service.ServiceName,
                DisplayName = service.DisplayName,
                Status = service.Status.ToString(),
                StartType = service.StartType.ToString(),
                Category = category,
                IsProtected = isProtected,
                IsRunning = isRunning,
                IsAutoStart = isAutoStart,
                CanStop = !isProtected && service.CanStop,
                Description = GetServiceDescription(service.ServiceName)
            };
        }

        private static string GetServiceDescription(string serviceName)
        {
            // Описания служб
            var descriptions = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase)
            {
                ["DiagTrack"] = "Собирает данные телеметрии для Microsoft",
                ["dmwappushservice"] = "Служба push-уведомлений WAP",
                ["diagsvc"] = "Выполняет диагностику системы",
                ["DPS"] = "Обрабатывает политики диагностики",
                ["diagnosticshub.standardcollector.service"] = "Собирает диагностические данные",
                ["WdiServiceHost"] = "Хост службы диагностики",
                ["WdiSystemHost"] = "Системный хост диагностики",
                ["XblAuthManager"] = "Аутентификация Xbox Live",
                ["XblGameSave"] = "Сохранения игр Xbox Live",
                ["XboxGipSvc"] = "Управление аксессуарами Xbox",
                ["XboxNetApiSvc"] = "Сетевые функции Xbox Live",
                ["bthserv"] = "Поддержка Bluetooth устройств",
                ["BthAvctpSvc"] = "Служба AVCTP для Bluetooth",
                ["Spooler"] = "Управление очередью печати",
                ["PrintNotify"] = "Уведомления о печати",
                ["MapsBroker"] = "Управление загруженными картами",
                ["lfsvc"] = "Служба геолокации",
                ["WbioSrvc"] = "Биометрическая аутентификация",
                ["Fax"] = "Отправка и получение факсов",
                ["TermService"] = "Удалённый рабочий стол",
                ["SessionEnv"] = "Конфигурация удалённого рабочего стола",
                ["UmRdpService"] = "Перенаправление портов RDP",
                ["wuauserv"] = "Автоматическое обновление Windows",
                ["UsoSvc"] = "Оркестратор обновлений Windows"
            };

            return descriptions.TryGetValue(serviceName, out var desc) ? desc : "";
        }

        private static void SetServiceStatus(string serviceName, string action)
        {
            // Проверка защищённых служб
            if (ProtectedServices.Contains(serviceName))
            {
                Console.WriteLine(JsonSerializer.Serialize(new 
                { 
                    success = false, 
                    error = "Эта служба защищена и не может быть изменена" 
                }));
                return;
            }

            try
            {
                using var service = new ServiceController(serviceName);

                if (action.Equals("disable", StringComparison.OrdinalIgnoreCase))
                {
                    // Остановить службу если запущена
                    if (service.Status == ServiceControllerStatus.Running && service.CanStop)
                    {
                        service.Stop();
                        service.WaitForStatus(ServiceControllerStatus.Stopped, TimeSpan.FromSeconds(30));
                    }

                    // Изменить тип запуска на Manual
                    SetServiceStartMode(serviceName, ServiceStartMode.Manual);

                    Console.WriteLine(JsonSerializer.Serialize(new 
                    { 
                        success = true, 
                        message = $"Служба {service.DisplayName} отключена" 
                    }));
                }
                else if (action.Equals("enable", StringComparison.OrdinalIgnoreCase))
                {
                    // Изменить тип запуска на Automatic
                    SetServiceStartMode(serviceName, ServiceStartMode.Automatic);

                    // Запустить службу
                    if (service.Status == ServiceControllerStatus.Stopped)
                    {
                        service.Start();
                        service.WaitForStatus(ServiceControllerStatus.Running, TimeSpan.FromSeconds(30));
                    }

                    Console.WriteLine(JsonSerializer.Serialize(new 
                    { 
                        success = true, 
                        message = $"Служба {service.DisplayName} включена" 
                    }));
                }
                else
                {
                    Console.WriteLine(JsonSerializer.Serialize(new 
                    { 
                        success = false, 
                        error = "Неизвестное действие. Используйте 'enable' или 'disable'" 
                    }));
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine(JsonSerializer.Serialize(new 
                { 
                    success = false, 
                    error = ex.Message 
                }));
            }
        }

        private static void SetServiceStartMode(string serviceName, ServiceStartMode mode)
        {
            // Используем WMI для изменения типа запуска
            string modeString = mode switch
            {
                ServiceStartMode.Automatic => "Automatic",
                ServiceStartMode.Manual => "Manual",
                ServiceStartMode.Disabled => "Disabled",
                _ => "Manual"
            };

            var startInfo = new System.Diagnostics.ProcessStartInfo
            {
                FileName = "sc.exe",
                Arguments = $"config \"{serviceName}\" start= {modeString.ToLower()}",
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true
            };

            using var process = System.Diagnostics.Process.Start(startInfo);
            process?.WaitForExit();
        }

        private static void ListCategories()
        {
            var categories = new List<object>();

            foreach (var kvp in ServicesByCategory)
            {
                int serviceCount = kvp.Value.Count;
                categories.Add(new
                {
                    id = kvp.Key,
                    name = GetCategoryName(kvp.Key),
                    description = GetCategoryDescription(kvp.Key),
                    serviceCount,
                    riskLevel = GetCategoryRiskLevel(kvp.Key)
                });
            }

            Console.WriteLine(JsonSerializer.Serialize(new { categories }));
        }

        private static string GetCategoryName(string category)
        {
            return category switch
            {
                ServiceCategories.Telemetry => "Телеметрия",
                ServiceCategories.Diagnostics => "Диагностика",
                ServiceCategories.Xbox => "Xbox",
                ServiceCategories.Bluetooth => "Bluetooth",
                ServiceCategories.Printer => "Печать",
                ServiceCategories.Maps => "Карты",
                ServiceCategories.Biometrics => "Биометрия",
                ServiceCategories.Fax => "Факс",
                ServiceCategories.RemoteDesktop => "Удалённый рабочий стол",
                ServiceCategories.WindowsUpdate => "Обновления Windows",
                _ => category
            };
        }

        private static string GetCategoryDescription(string category)
        {
            return category switch
            {
                ServiceCategories.Telemetry => "Сбор данных о работе системы для Microsoft",
                ServiceCategories.Diagnostics => "Диагностика и устранение проблем Windows",
                ServiceCategories.Xbox => "Функции Xbox Live и игровые сервисы",
                ServiceCategories.Bluetooth => "Поддержка Bluetooth устройств",
                ServiceCategories.Printer => "Управление принтерами и печатью",
                ServiceCategories.Maps => "Загрузка и управление картами",
                ServiceCategories.Biometrics => "Биометрическая аутентификация (отпечатки, лицо)",
                ServiceCategories.Fax => "Отправка и получение факсов",
                ServiceCategories.RemoteDesktop => "Удалённое подключение к компьютеру",
                ServiceCategories.WindowsUpdate => "Автоматическое обновление Windows",
                _ => ""
            };
        }

        private static string GetCategoryRiskLevel(string category)
        {
            return category switch
            {
                ServiceCategories.Telemetry => "low",
                ServiceCategories.Diagnostics => "medium",
                ServiceCategories.Xbox => "low",
                ServiceCategories.Bluetooth => "low",
                ServiceCategories.Printer => "low",
                ServiceCategories.Maps => "low",
                ServiceCategories.Biometrics => "low",
                ServiceCategories.Fax => "low",
                ServiceCategories.RemoteDesktop => "medium",
                ServiceCategories.WindowsUpdate => "high",
                _ => "medium"
            };
        }
    }
}
