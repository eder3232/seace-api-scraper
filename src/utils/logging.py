"""
Utilidades para logging profesional en los scrapers.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_dir: str = "logs"
) -> None:
    """
    Configura el sistema de logging profesional.
    
    Args:
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Nombre del archivo de log (opcional)
        log_dir: Directorio donde guardar los logs
    """
    # Crear directorio de logs si no existe
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Configurar formato de logging
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Convertir string de nivel a constante de logging
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configurar handlers
    handlers = [
        logging.StreamHandler(sys.stdout)  # Consola
    ]
    
    # Agregar handler de archivo si se especifica
    if log_file:
        log_file_path = log_path / log_file
        handlers.append(logging.FileHandler(log_file_path, encoding='utf-8'))
    
    # Configurar logging básico
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        datefmt=date_format,
        handlers=handlers,
        force=True  # Sobrescribir configuración anterior si existe
    )


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger con el nombre especificado.
    
    Args:
        name: Nombre del logger (típicamente __name__)
    
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)
