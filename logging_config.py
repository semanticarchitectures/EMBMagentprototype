"""
Logging configuration for EMBM-J DS.

Provides structured logging to both console and rotating log files.
"""

import structlog
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime


# Create logs directory
LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)


def configure_logging(
    log_level: str = "INFO",
    log_to_file: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
):
    """
    Configure structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_to_file: Whether to log to files
        max_bytes: Max size of each log file before rotation
        backup_count: Number of backup files to keep
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
    )

    # Add file handlers if requested
    if log_to_file:
        # Main application log
        app_handler = RotatingFileHandler(
            LOGS_DIR / "embm_app.log",
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        app_handler.setLevel(numeric_level)
        app_handler.setFormatter(logging.Formatter("%(message)s"))

        # MCP server log
        mcp_handler = RotatingFileHandler(
            LOGS_DIR / "embm_mcp_server.log",
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        mcp_handler.setLevel(numeric_level)
        mcp_handler.setFormatter(logging.Formatter("%(message)s"))

        # Agent log
        agent_handler = RotatingFileHandler(
            LOGS_DIR / "embm_agents.log",
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        agent_handler.setLevel(numeric_level)
        agent_handler.setFormatter(logging.Formatter("%(message)s"))

        # Test log
        test_handler = RotatingFileHandler(
            LOGS_DIR / "embm_tests.log",
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        test_handler.setLevel(numeric_level)
        test_handler.setFormatter(logging.Formatter("%(message)s"))

        # Add handlers to root logger
        root_logger = logging.getLogger()

        # Remove existing file handlers to avoid duplicates
        for handler in root_logger.handlers[:]:
            if isinstance(handler, RotatingFileHandler):
                root_logger.removeHandler(handler)

        root_logger.addHandler(app_handler)

        # Configure specific loggers
        logging.getLogger("mcp_server").addHandler(mcp_handler)
        logging.getLogger("agents").addHandler(agent_handler)
        logging.getLogger("tests").addHandler(test_handler)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically module name)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def log_session_start(session_type: str):
    """Log the start of a new session (test run, workflow, etc.)."""
    logger = get_logger("session")
    logger.info(
        "session_started",
        session_type=session_type,
        timestamp=datetime.utcnow().isoformat(),
        log_dir=str(LOGS_DIR)
    )


def get_log_files():
    """Get list of all log files."""
    return list(LOGS_DIR.glob("*.log"))


if __name__ == "__main__":
    # Test logging configuration
    configure_logging(log_level="INFO", log_to_file=True)

    logger = get_logger("test")
    logger.info("logging_test", message="Logging configuration test")
    logger.debug("debug_test", message="This is a debug message")
    logger.warning("warning_test", message="This is a warning")
    logger.error("error_test", message="This is an error")

    print(f"\nLog files created in: {LOGS_DIR}")
    for log_file in get_log_files():
        print(f"  - {log_file.name}")
