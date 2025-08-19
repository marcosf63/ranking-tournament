"""
Serviço de backup automático do banco de dados
"""
import os
import gzip
import shutil
import subprocess
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path
import logging

from ..core.config import settings
from .notification_service import notification_service

logger = logging.getLogger(__name__)


class BackupService:
    """Serviço para backup automático do banco de dados"""
    
    def __init__(self):
        self.backup_dir = Path("./backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # Configurações de backup
        self.max_backups = 30  # Manter 30 backups
        self.compress_backups = True
        
        # Configurações do PostgreSQL
        self.db_config = self._parse_database_url()
    
    def _parse_database_url(self) -> Dict[str, str]:
        """Extrair configurações do banco da URL"""
        # Format: postgresql+asyncpg://user:password@host:port/database
        url = settings.database_url.replace("+asyncpg", "").replace("postgresql://", "")
        
        if "@" in url:
            auth, host_db = url.split("@", 1)
            user_pass = auth.split(":", 1)
            user = user_pass[0]
            password = user_pass[1] if len(user_pass) > 1 else ""
        else:
            user = "postgres"
            password = ""
            host_db = url
        
        if "/" in host_db:
            host_port, database = host_db.split("/", 1)
        else:
            host_port = host_db
            database = "ranking"
        
        if ":" in host_port:
            host, port = host_port.split(":", 1)
        else:
            host = host_port
            port = "5432"
        
        return {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database
        }
    
    def create_backup(self, backup_name: Optional[str] = None) -> Dict[str, any]:
        """
        Criar backup do banco de dados
        
        Args:
            backup_name: Nome personalizado do backup
            
        Returns:
            Dict com informações do backup criado
        """
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            if backup_name:
                filename = f"{backup_name}_{timestamp}.sql"
            else:
                filename = f"ranking_backup_{timestamp}.sql"
            
            backup_path = self.backup_dir / filename
            
            # Comando pg_dump
            cmd = [
                "pg_dump",
                f"--host={self.db_config['host']}",
                f"--port={self.db_config['port']}",
                f"--username={self.db_config['user']}",
                f"--dbname={self.db_config['database']}",
                "--verbose",
                "--clean",
                "--no-owner",
                "--no-acl",
                f"--file={backup_path}"
            ]
            
            # Configurar senha via variável de ambiente
            env = os.environ.copy()
            if self.db_config['password']:
                env['PGPASSWORD'] = self.db_config['password']
            
            # Executar pg_dump
            logger.info(f"Starting backup: {filename}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                error_msg = f"pg_dump failed: {result.stderr}"
                logger.error(error_msg)
                notification_service.notify_system_error(
                    "Backup Failed",
                    error_msg,
                    {"command": " ".join(cmd)}
                )
                raise Exception(error_msg)
            
            # Obter tamanho do arquivo
            file_size = backup_path.stat().st_size
            
            # Comprimir se habilitado
            if self.compress_backups:
                compressed_path = backup_path.with_suffix(".sql.gz")
                with open(backup_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Remover arquivo original
                backup_path.unlink()
                backup_path = compressed_path
                compressed_size = backup_path.stat().st_size
            else:
                compressed_size = file_size
            
            backup_info = {
                "filename": backup_path.name,
                "path": str(backup_path),
                "size": file_size,
                "compressed_size": compressed_size,
                "compressed": self.compress_backups,
                "created_at": datetime.utcnow().isoformat(),
                "success": True
            }
            
            logger.info(f"Backup created successfully: {backup_path.name} ({compressed_size} bytes)")
            
            # Limpar backups antigos
            self._cleanup_old_backups()
            
            return backup_info
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            notification_service.notify_system_error(
                "Backup Error",
                str(e),
                {"operation": "create_backup"}
            )
            raise
    
    def restore_backup(self, backup_filename: str, confirm: bool = False) -> Dict[str, any]:
        """
        Restaurar backup do banco de dados
        
        ATENÇÃO: Esta operação irá SUBSTITUIR todos os dados atuais!
        
        Args:
            backup_filename: Nome do arquivo de backup
            confirm: Confirmação de que quer realmente restaurar
            
        Returns:
            Dict com resultado da operação
        """
        if not confirm:
            raise ValueError("Restore operation requires explicit confirmation (confirm=True)")
        
        try:
            backup_path = self.backup_dir / backup_filename
            
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_filename}")
            
            # Se o arquivo está comprimido, descomprimir temporariamente
            if backup_path.suffix == ".gz":
                temp_path = backup_path.with_suffix("")
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(temp_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                sql_file = temp_path
                cleanup_temp = True
            else:
                sql_file = backup_path
                cleanup_temp = False
            
            # Comando psql para restaurar
            cmd = [
                "psql",
                f"--host={self.db_config['host']}",
                f"--port={self.db_config['port']}",
                f"--username={self.db_config['user']}",
                f"--dbname={self.db_config['database']}",
                "--quiet",
                f"--file={sql_file}"
            ]
            
            # Configurar senha
            env = os.environ.copy()
            if self.db_config['password']:
                env['PGPASSWORD'] = self.db_config['password']
            
            # Executar restore
            logger.warning(f"Starting database restore from: {backup_filename}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            # Limpar arquivo temporário se necessário
            if cleanup_temp:
                temp_path.unlink()
            
            if result.returncode != 0:
                error_msg = f"psql restore failed: {result.stderr}"
                logger.error(error_msg)
                notification_service.notify_system_error(
                    "Restore Failed",
                    error_msg,
                    {"backup_file": backup_filename}
                )
                raise Exception(error_msg)
            
            restore_info = {
                "backup_file": backup_filename,
                "restored_at": datetime.utcnow().isoformat(),
                "success": True
            }
            
            logger.warning(f"Database restored successfully from: {backup_filename}")
            notification_service.notify_system_error(
                "Database Restored",
                f"Database was restored from backup: {backup_filename}",
                restore_info
            )
            
            return restore_info
            
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            notification_service.notify_system_error(
                "Restore Error",
                str(e),
                {"backup_file": backup_filename}
            )
            raise
    
    def list_backups(self) -> List[Dict[str, any]]:
        """Listar todos os backups disponíveis"""
        backups = []
        
        for backup_file in sorted(self.backup_dir.glob("*.sql*"), reverse=True):
            file_stats = backup_file.stat()
            
            backup_info = {
                "filename": backup_file.name,
                "path": str(backup_file),
                "size": file_stats.st_size,
                "compressed": backup_file.suffix == ".gz",
                "created_at": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                "age_days": (datetime.now() - datetime.fromtimestamp(file_stats.st_mtime)).days
            }
            
            backups.append(backup_info)
        
        return backups
    
    def delete_backup(self, backup_filename: str) -> bool:
        """Deletar um backup específico"""
        try:
            backup_path = self.backup_dir / backup_filename
            
            if not backup_path.exists():
                logger.warning(f"Backup file not found: {backup_filename}")
                return False
            
            backup_path.unlink()
            logger.info(f"Backup deleted: {backup_filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting backup {backup_filename}: {e}")
            return False
    
    def _cleanup_old_backups(self):
        """Limpar backups antigos mantendo apenas os mais recentes"""
        backups = self.list_backups()
        
        if len(backups) > self.max_backups:
            # Ordenar por data de criação (mais recente primeiro)
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
            # Deletar backups excedentes
            for backup in backups[self.max_backups:]:
                self.delete_backup(backup['filename'])
                logger.info(f"Cleaned up old backup: {backup['filename']}")
    
    def schedule_automatic_backup(self) -> Dict[str, any]:
        """Criar backup automático agendado"""
        try:
            backup_info = self.create_backup("auto")
            
            logger.info("Automatic backup completed successfully")
            
            # Notificar apenas em caso de erro
            return backup_info
            
        except Exception as e:
            logger.error(f"Automatic backup failed: {e}")
            notification_service.notify_system_error(
                "Automatic Backup Failed",
                str(e),
                {"scheduled": True}
            )
            raise
    
    def get_backup_statistics(self) -> Dict[str, any]:
        """Obter estatísticas dos backups"""
        backups = self.list_backups()
        
        if not backups:
            return {
                "total_backups": 0,
                "total_size": 0,
                "oldest_backup": None,
                "newest_backup": None,
                "average_size": 0
            }
        
        total_size = sum(backup['size'] for backup in backups)
        
        return {
            "total_backups": len(backups),
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "oldest_backup": backups[-1]['created_at'],
            "newest_backup": backups[0]['created_at'],
            "average_size": round(total_size / len(backups)),
            "compressed_backups": len([b for b in backups if b['compressed']])
        }


# Instância global do serviço
backup_service = BackupService()