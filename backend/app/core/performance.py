"""
Otimizações de performance e índices do banco de dados
"""
from sqlalchemy import text, Index
from sqlmodel import Session
import logging
from typing import List, Dict, Any

from .database import sync_engine

logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """Classe para otimizações de performance"""
    
    def __init__(self):
        self.indexes_created = False
    
    def create_database_indexes(self):
        """Criar índices otimizados para o banco de dados"""
        if self.indexes_created:
            return
        
        indexes = [
            # Índices para tabela players
            "CREATE INDEX IF NOT EXISTS idx_players_active ON players(is_active) WHERE is_active = true;",
            "CREATE INDEX IF NOT EXISTS idx_players_email ON players(email);",
            "CREATE INDEX IF NOT EXISTS idx_players_nickname ON players(nickname);",
            "CREATE INDEX IF NOT EXISTS idx_players_name_search ON players USING gin(to_tsvector('english', name));",
            
            # Índices para tabela tournaments
            "CREATE INDEX IF NOT EXISTS idx_tournaments_dates ON tournaments(start_date, end_date);",
            "CREATE INDEX IF NOT EXISTS idx_tournaments_active ON tournaments(end_date) WHERE end_date >= NOW();",
            "CREATE INDEX IF NOT EXISTS idx_tournaments_name_search ON tournaments USING gin(to_tsvector('english', name));",
            
            # Índices para tabela scores
            "CREATE INDEX IF NOT EXISTS idx_scores_player_tournament ON scores(player_id, tournament_id);",
            "CREATE INDEX IF NOT EXISTS idx_scores_tournament_points ON scores(tournament_id, points DESC);",
            "CREATE INDEX IF NOT EXISTS idx_scores_player_points ON scores(player_id, points DESC);",
            "CREATE INDEX IF NOT EXISTS idx_scores_created_at ON scores(created_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_scores_admin ON scores(admin_id);",
            
            # Índices para tabela admins
            "CREATE INDEX IF NOT EXISTS idx_admins_email ON admins(email);",
            "CREATE INDEX IF NOT EXISTS idx_admins_active ON admins(is_active) WHERE is_active = true;",
            "CREATE INDEX IF NOT EXISTS idx_admins_permission ON admins(permission_level);",
            
            # Índices para tabela audit_log
            "CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_log(resource_type, resource_id);",
            "CREATE INDEX IF NOT EXISTS idx_audit_admin ON audit_log(admin_id);",
            "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp DESC);",
            "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);",
            
            # Índices compostos para queries complexas
            "CREATE INDEX IF NOT EXISTS idx_scores_player_tournament_points ON scores(player_id, tournament_id, points DESC);",
            "CREATE INDEX IF NOT EXISTS idx_scores_tournament_player_points ON scores(tournament_id, player_id, points DESC);",
            
            # Índices para ranking geral (otimização crítica)
            "CREATE INDEX IF NOT EXISTS idx_ranking_calculation ON scores(player_id, points) WHERE EXISTS (SELECT 1 FROM players p WHERE p.id = scores.player_id AND p.is_active = true);",
        ]
        
        try:
            with Session(sync_engine) as session:
                for index_sql in indexes:
                    try:
                        session.execute(text(index_sql))
                        logger.debug(f"Index created: {index_sql.split()[-1] if 'idx_' in index_sql else 'unnamed'}")
                    except Exception as e:
                        logger.warning(f"Index creation failed: {e}")
                
                session.commit()
                logger.info("Database indexes created successfully")
                self.indexes_created = True
                
        except Exception as e:
            logger.error(f"Error creating database indexes: {e}")
    
    def create_materialized_views(self):
        """Criar views materializadas para queries complexas"""
        views = [
            # View para ranking geral
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_general_ranking AS
            SELECT 
                p.id as player_id,
                p.name as player_name,
                p.nickname as player_nickname,
                p.avatar_url,
                COUNT(s.id) as total_tournaments,
                SUM(s.points) as total_points,
                AVG(s.points) as average_points,
                MAX(s.points) as best_score,
                MIN(s.points) as worst_score,
                RANK() OVER (ORDER BY SUM(s.points) DESC) as position,
                NOW() as last_updated
            FROM players p
            JOIN scores s ON p.id = s.player_id
            WHERE p.is_active = true
            GROUP BY p.id, p.name, p.nickname, p.avatar_url
            ORDER BY total_points DESC;
            """,
            
            # Índice para a view materializada
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_general_ranking_player ON mv_general_ranking(player_id);",
            "CREATE INDEX IF NOT EXISTS idx_mv_general_ranking_position ON mv_general_ranking(position);",
            "CREATE INDEX IF NOT EXISTS idx_mv_general_ranking_points ON mv_general_ranking(total_points DESC);",
            
            # View para estatísticas do sistema
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_system_stats AS
            SELECT 
                COUNT(DISTINCT p.id) as total_players,
                COUNT(DISTINCT CASE WHEN p.is_active THEN p.id END) as active_players,
                COUNT(DISTINCT t.id) as total_tournaments,
                COUNT(DISTINCT CASE WHEN t.end_date >= NOW() THEN t.id END) as active_tournaments,
                COUNT(s.id) as total_scores,
                AVG(s.points) as average_score,
                MAX(s.points) as highest_score,
                MIN(s.points) as lowest_score,
                COUNT(CASE WHEN s.points > 0 THEN 1 END) as positive_scores,
                COUNT(CASE WHEN s.points < 0 THEN 1 END) as negative_scores,
                NOW() as last_updated
            FROM players p
            LEFT JOIN scores s ON p.id = s.player_id
            LEFT JOIN tournaments t ON s.tournament_id = t.id;
            """
        ]
        
        try:
            with Session(sync_engine) as session:
                for view_sql in views:
                    try:
                        session.execute(text(view_sql))
                        logger.debug("Materialized view created")
                    except Exception as e:
                        logger.warning(f"Materialized view creation failed: {e}")
                
                session.commit()
                logger.info("Materialized views created successfully")
                
        except Exception as e:
            logger.error(f"Error creating materialized views: {e}")
    
    def refresh_materialized_views(self):
        """Atualizar views materializadas"""
        views_to_refresh = [
            "mv_general_ranking",
            "mv_system_stats"
        ]
        
        try:
            with Session(sync_engine) as session:
                for view in views_to_refresh:
                    try:
                        session.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view};"))
                        logger.debug(f"Refreshed materialized view: {view}")
                    except Exception as e:
                        # Fallback para refresh sem CONCURRENTLY
                        try:
                            session.execute(text(f"REFRESH MATERIALIZED VIEW {view};"))
                            logger.debug(f"Refreshed materialized view (non-concurrent): {view}")
                        except Exception as e2:
                            logger.warning(f"Failed to refresh materialized view {view}: {e2}")
                
                session.commit()
                logger.info("Materialized views refreshed")
                
        except Exception as e:
            logger.error(f"Error refreshing materialized views: {e}")
    
    def analyze_query_performance(self) -> Dict[str, Any]:
        """Analisar performance das queries mais comuns"""
        common_queries = [
            # Query de ranking geral
            """
            EXPLAIN ANALYZE
            SELECT 
                p.id, p.name, p.nickname, p.avatar_url,
                COUNT(s.id) as total_tournaments,
                SUM(s.points) as total_points,
                AVG(s.points) as average_points,
                RANK() OVER (ORDER BY SUM(s.points) DESC) as position
            FROM players p
            JOIN scores s ON p.id = s.player_id
            WHERE p.is_active = true
            GROUP BY p.id, p.name, p.nickname, p.avatar_url
            ORDER BY total_points DESC
            LIMIT 10;
            """,
            
            # Query de ranking por torneio
            """
            EXPLAIN ANALYZE
            SELECT 
                p.id, p.name, s.points,
                RANK() OVER (ORDER BY s.points DESC) as position
            FROM players p
            JOIN scores s ON p.id = s.player_id
            WHERE s.tournament_id = 1 AND p.is_active = true
            ORDER BY s.points DESC
            LIMIT 10;
            """,
            
            # Query de busca de jogadores
            """
            EXPLAIN ANALYZE
            SELECT id, name, nickname, email
            FROM players
            WHERE is_active = true
            AND (name ILIKE '%test%' OR nickname ILIKE '%test%')
            LIMIT 10;
            """
        ]
        
        results = []
        
        try:
            with Session(sync_engine) as session:
                for i, query in enumerate(common_queries):
                    try:
                        result = session.execute(text(query)).fetchall()
                        
                        # Extrair informações de performance
                        execution_time = None
                        for row in result:
                            if 'Execution Time:' in str(row):
                                execution_time = str(row).split('Execution Time:')[1].strip()
                                break
                        
                        results.append({
                            'query_id': i + 1,
                            'execution_time': execution_time,
                            'plan_rows': len(result),
                            'status': 'completed'
                        })
                        
                    except Exception as e:
                        results.append({
                            'query_id': i + 1,
                            'error': str(e),
                            'status': 'failed'
                        })
                
        except Exception as e:
            logger.error(f"Error analyzing query performance: {e}")
        
        return {
            'analysis_timestamp': logger.info("Query performance analysis completed"),
            'queries_analyzed': len(common_queries),
            'results': results
        }
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do banco de dados"""
        stats_queries = {
            'table_sizes': """
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
            """,
            
            'index_usage': """
                SELECT 
                    indexrelname as index_name,
                    idx_tup_read,
                    idx_tup_fetch,
                    idx_scan
                FROM pg_stat_user_indexes
                ORDER BY idx_scan DESC;
            """,
            
            'slow_queries': """
                SELECT 
                    query,
                    calls,
                    total_time,
                    mean_time,
                    min_time,
                    max_time
                FROM pg_stat_statements 
                WHERE query LIKE '%SELECT%'
                ORDER BY mean_time DESC 
                LIMIT 10;
            """
        }
        
        results = {}
        
        try:
            with Session(sync_engine) as session:
                for stat_name, query in stats_queries.items():
                    try:
                        result = session.execute(text(query)).fetchall()
                        results[stat_name] = [dict(row._mapping) for row in result]
                    except Exception as e:
                        results[stat_name] = f"Error: {e}"
                        logger.warning(f"Stats query failed for {stat_name}: {e}")
                
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            results['error'] = str(e)
        
        return results
    
    def optimize_all(self):
        """Executar todas as otimizações disponíveis"""
        logger.info("Starting performance optimization...")
        
        # Criar índices
        self.create_database_indexes()
        
        # Criar views materializadas (se PostgreSQL)
        try:
            self.create_materialized_views()
            self.refresh_materialized_views()
        except Exception as e:
            logger.info("Materialized views not supported or failed to create")
        
        logger.info("Performance optimization completed")


# Instância global do otimizador
performance_optimizer = PerformanceOptimizer()


# Decorator para monitoramento de performance
def monitor_performance(func):
    """Decorator para monitorar performance de funções"""
    import time
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log se a função demorar mais que 1 segundo
            if execution_time > 1.0:
                logger.warning(
                    f"Slow function detected: {func.__name__} took {execution_time:.2f}s"
                )
            elif execution_time > 0.1:
                logger.info(
                    f"Function timing: {func.__name__} took {execution_time:.3f}s"
                )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Function error: {func.__name__} failed after {execution_time:.3f}s: {e}"
            )
            raise
    
    return wrapper


# Query builders otimizados
class OptimizedQueries:
    """Queries otimizadas para operações comuns"""
    
    @staticmethod
    def get_general_ranking_optimized(limit: int = 100, offset: int = 0) -> str:
        """Query otimizada para ranking geral"""
        return f"""
        WITH player_scores AS (
            SELECT 
                s.player_id,
                SUM(s.points) as total_points,
                COUNT(s.id) as total_tournaments,
                AVG(s.points) as average_points,
                MAX(s.points) as best_score,
                MIN(s.points) as worst_score
            FROM scores s
            INNER JOIN players p ON s.player_id = p.id
            WHERE p.is_active = true
            GROUP BY s.player_id
        ),
        ranked_players AS (
            SELECT 
                ps.*,
                p.name as player_name,
                p.nickname as player_nickname,
                p.avatar_url,
                RANK() OVER (ORDER BY ps.total_points DESC) as position
            FROM player_scores ps
            INNER JOIN players p ON ps.player_id = p.id
        )
        SELECT * FROM ranked_players
        ORDER BY position
        LIMIT {limit} OFFSET {offset};
        """
    
    @staticmethod
    def get_tournament_ranking_optimized(tournament_id: int, limit: int = 100, offset: int = 0) -> str:
        """Query otimizada para ranking de torneio"""
        return f"""
        WITH tournament_scores AS (
            SELECT 
                s.player_id,
                s.points,
                s.notes,
                s.created_at as score_date,
                p.name as player_name,
                p.nickname as player_nickname,
                p.avatar_url,
                t.sort_criteria
            FROM scores s
            INNER JOIN players p ON s.player_id = p.id
            INNER JOIN tournaments t ON s.tournament_id = t.id
            WHERE s.tournament_id = {tournament_id} 
            AND p.is_active = true
        )
        SELECT 
            *,
            CASE 
                WHEN sort_criteria = 'points_desc' THEN 
                    RANK() OVER (ORDER BY points DESC)
                ELSE 
                    RANK() OVER (ORDER BY points ASC)
            END as position
        FROM tournament_scores
        ORDER BY 
            CASE WHEN sort_criteria = 'points_desc' THEN points END DESC,
            CASE WHEN sort_criteria = 'points_asc' THEN points END ASC
        LIMIT {limit} OFFSET {offset};
        """
    
    @staticmethod
    def get_player_search_optimized(search_term: str, limit: int = 20) -> str:
        """Query otimizada para busca de jogadores"""
        return f"""
        SELECT DISTINCT
            p.id,
            p.name,
            p.nickname,
            p.avatar_url,
            COALESCE(ps.total_tournaments, 0) as total_tournaments,
            COALESCE(ps.total_points, 0) as total_points,
            COALESCE(ps.position, 0) as position
        FROM players p
        LEFT JOIN (
            SELECT 
                player_id,
                COUNT(*) as total_tournaments,
                SUM(points) as total_points,
                RANK() OVER (ORDER BY SUM(points) DESC) as position
            FROM scores
            GROUP BY player_id
        ) ps ON p.id = ps.player_id
        WHERE p.is_active = true
        AND (
            p.name ILIKE '%{search_term}%' 
            OR p.nickname ILIKE '%{search_term}%'
        )
        ORDER BY ps.total_points DESC NULLS LAST
        LIMIT {limit};
        """