# install_tickgenerator.ps1
# Шаг 1. Установка модуля TickGenerator
# Фаза: реализация
# Вектор: удержан

Write-Host "🚀 TickGenerator: начало установки" -ForegroundColor Green
Write-Host "Фаза накопления завершена. Приступаем к сборке." -ForegroundColor Cyan

# 1. Проверка прав администратора
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "❌ Ошибка: Запустите PowerShell от имени администратора" -ForegroundColor Red
    exit 1
}

# 2. Создание структуры директорий
$modulePath = "C:\Program Files\SpectraVortex\Modules\TickGenerator"
$configPath = "C:\ProgramData\SpectraVortex\Config"
$logPath = "C:\ProgramData\SpectraVortex\Logs"

Write-Host "📁 Создаю структуру директорий..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $modulePath -Force | Out-Null
New-Item -ItemType Directory -Path $configPath -Force | Out-Null
New-Item -ItemType Directory -Path $logPath -Force | Out-Null

# 3. Генерация файла модуля TickGenerator
$moduleFile = @"
// TickGenerator.cs
// Ядро тактовой синхронизации Ризомы
// Версия 1.0.0

using System;
using System.IO;
using System.Timers;

namespace SpectraVortex.Modules.TickGenerator
{
    /// <summary>
    /// Генератор эталонного такта.
    /// Сердце системы. Не зависит от состояний других модулей.
    /// </summary>
    public class TickGenerator : IDisposable
    {
        private readonly Timer _timer;
        private readonly string _logPath;
        private long _tickCount;
        private readonly object _lock = new object();
        
        /// <summary>
        /// Событие нового такта
        /// </summary>
        public event EventHandler<TickEventArgs> Tick;
        
        /// <summary>
        /// Текущий номер такта
        /// </summary>
        public long CurrentTick { get; private set; }
        
        /// <summary>
        /// Частота тактов (Гц)
        /// </summary>
        public double Frequency { get; private set; }
        
        public TickGenerator(double frequency = 60.0)
        {
            Frequency = frequency;
            _logPath = @"C:\ProgramData\SpectraVortex\Logs\tick.log";
            _timer = new Timer(1000.0 / frequency);
            _timer.Elapsed += OnTick;
            _timer.AutoReset = true;
            
            // Гарантия, что файл лога существует
            File.AppendAllText(_logPath, $"[{DateTime.UtcNow:O}] TickGenerator инициализирован. Частота: {frequency} Гц\n");
        }
        
        /// <summary>
        /// Запустить генератор тактов
        /// </summary>
        public void Start()
        {
            lock (_lock)
            {
                _timer.Start();
                File.AppendAllText(_logPath, $"[{DateTime.UtcNow:O}] TickGenerator запущен\n");
            }
        }
        
        /// <summary>
        /// Остановить генератор тактов
        /// </summary>
        public void Stop()
        {
            lock (_lock)
            {
                _timer.Stop();
                File.AppendAllText(_logPath, $"[{DateTime.UtcNow:O}] TickGenerator остановлен\n");
            }
        }
        
        private void OnTick(object sender, ElapsedEventArgs e)
        {
            lock (_lock)
            {
                CurrentTick++;
                
                // Каждые 1000 тактов пишем в лог (для отладки)
                if (CurrentTick % 1000 == 0)
                {
                    File.AppendAllText(_logPath, $"[{DateTime.UtcNow:O}] Такт #{CurrentTick}\n");
                }
                
                // Вызываем событие для подписчиков
                Tick?.Invoke(this, new TickEventArgs(CurrentTick, DateTime.UtcNow));
            }
        }
        
        public void Dispose()
        {
            _timer?.Dispose();
            File.AppendAllText(_logPath, $"[{DateTime.UtcNow:O}] TickGenerator завершил работу\n");
        }
    }
    
    /// <summary>
    /// Аргументы события такта
    /// </summary>
    public class TickEventArgs : EventArgs
    {
        public long TickNumber { get; }
        public DateTime Timestamp { get; }
        
        public TickEventArgs(long tickNumber, DateTime timestamp)
        {
            TickNumber = tickNumber;
            Timestamp = timestamp;
        }
    }
}
"@

# 4. Сохранение файла модуля
$moduleFile | Out-File -FilePath "$modulePath\TickGenerator.cs" -Encoding UTF8
Write-Host "✅ Модуль TickGenerator.cs создан" -ForegroundColor Green

# 5. Создание тестового скрипта для проверки
$testScript = @"
# test_tickgenerator.ps1
# Тестовый скрипт для проверки работы TickGenerator

Add-Type -Path "C:\Program Files\SpectraVortex\Modules\TickGenerator\TickGenerator.cs" -ReferencedAssemblies "System.dll"

Write-Host "🧪 Тестирование TickGenerator" -ForegroundColor Cyan

# Создаём экземпляр генератора с частотой 10 Гц (для наглядности)
$generator = New-Object SpectraVortex.Modules.TickGenerator.TickGenerator(10.0)

# Подписываемся на событие такта
$action = {
    Write-Host "⚡ Такт #`$(`$args[1].TickNumber) в `$(`$args[1].Timestamp)" -ForegroundColor Yellow
}
Register-ObjectEvent -InputObject $generator -EventName Tick -Action $action | Out-Null

# Запускаем
$generator.Start()
Write-Host "✅ Генератор запущен. Наблюдаем 5 секунд..." -ForegroundColor Green

# Ждём 5 секунд
Start-Sleep -Seconds 5

# Останавливаем
$generator.Stop()
$generator.Dispose()

# Показываем лог
Write-Host "`n📋 Последние строки лога:" -ForegroundColor Cyan
Get-Content "C:\ProgramData\SpectraVortex\Logs\tick.log" -Tail 10

Write-Host "`n✅ Тест завершён" -ForegroundColor Green
"@

$testScript | Out-File -FilePath "$modulePath\test_tickgenerator.ps1" -Encoding UTF8
Write-Host "✅ Тестовый скрипт создан" -ForegroundColor Green

# 6. Создание конфигурации
$configFile = @"
{
    "Module": "TickGenerator",
    "Version": "1.0.0",
    "Frequency": 60.0,
    "AutoStart": true,
    "LogLevel": "Info"
}
"@

$configFile | Out-File -FilePath "$configPath\tickgenerator.json" -Encoding UTF8
Write-Host "✅ Конфигурация создана" -ForegroundColor Green

# 7. Регистрация модуля в системе
$registryPath = "HKLM:\SOFTWARE\SpectraVortex\Modules"
New-Item -Path $registryPath -Force | Out-Null
New-ItemProperty -Path $registryPath -Name "TickGenerator" -Value $modulePath -PropertyType String -Force | Out-Null

Write-Host "✅ Модуль зарегистрирован в реестре" -ForegroundColor Green

# 8. Финальное сообщение
Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║  🎯 TickGenerator успешно установлен                         ║
║  📍 Путь: $modulePath                                        ║
║  ⚡ Частота по умолчанию: 60 Гц                              ║
║  🔧 Конфиг: $configPath\tickgenerator.json                   ║
║  📊 Логи: $logPath\tick.log                                  ║
╠══════════════════════════════════════════════════════════════╣
║  ▶️ Для теста запустите:                                      ║
║     powershell -File "$modulePath\test_tickgenerator.ps1"    ║
╚══════════════════════════════════════════════════════════════╝

Фаза: реализация. Вектор: удержан. Такт: запущен.
"@ -ForegroundColor Magenta