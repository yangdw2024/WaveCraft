import os
import sys
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler


class Logger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def _get_log_dir(self):
        if getattr(sys, "frozen", False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        log_dir = os.path.join(base_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        return log_dir

    def initialize(self, log_level=logging.INFO):
        if self._initialized:
            return

        self.logger = logging.getLogger("WaveCraft")
        self.logger.setLevel(log_level)
        self.logger.propagate = False

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        log_dir = self._get_log_dir()
        date_str = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(log_dir, f"wavecraft_{date_str}.log")

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=30,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        self._initialized = True
        self.logger.info("=" * 60)
        self.logger.info(f"WaveCraft 启动 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"运行模式: {'打包版本' if getattr(sys, 'frozen', False) else '开发版本'}")
        self.logger.info(f"Python版本: {sys.version}")
        self.logger.info(f"工作目录: {os.getcwd()}")
        self.logger.info("=" * 60)

    def get_logger(self):
        if not self._initialized:
            self.initialize()
        return self.logger

    def info(self, message):
        self.get_logger().info(message)

    def warning(self, message):
        self.get_logger().warning(message)

    def error(self, message):
        self.get_logger().error(message)

    def debug(self, message):
        self.get_logger().debug(message)

    def critical(self, message):
        self.get_logger().critical(message)

    def exception(self, message):
        self.get_logger().exception(message)


class IssueRecorder:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def initialize(self):
        if self._initialized:
            return
        self._issues = []
        self._initialized = True

    def record_issue(self, category, description, severity="medium", details=None):
        self.initialize()
        issue = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "category": category,
            "description": description,
            "severity": severity,
            "details": details or {},
        }
        self._issues.append(issue)
        logger = Logger().get_logger()
        logger.warning(f"[问题记录] {category}: {description} (严重度: {severity})")
        if details:
            logger.debug(f"问题详情: {details}")

    def get_all_issues(self):
        self.initialize()
        return self._issues.copy()

    def get_issues_by_severity(self, severity):
        self.initialize()
        return [i for i in self._issues if i["severity"] == severity]

    def get_issue_count(self):
        self.initialize()
        return len(self._issues)

    def clear_issues(self):
        self.initialize()
        self._issues.clear()

    def export_issues(self, filepath):
        self.initialize()
        import json
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self._issues, f, ensure_ascii=False, indent=2)
        return len(self._issues)
