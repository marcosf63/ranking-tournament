#!/usr/bin/env python3
"""
Script para criar dados de exemplo no sistema de ranking
"""
import sys
import os
from datetime import datetime, timedelta
from sqlmodel import Session

# Adicionar o diretório pai ao path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import sync_engine
from models.admin import Admin
from models.player import Player
from models.tournament import Tournament
from models.score import Score
from core.security import get_password_hash


def create_sample_data():
    """Criar dados de exemplo"""
    
    with Session(sync_engine) as session:
        print("Creating sample data...")
        
        # Verificar se já existem dados
        existing_tournaments = session.query(Tournament).count()
        if existing_tournaments > 0:
            print("Sample data already exists, skipping...")
            return
        
        # Criar torneios
        tournaments = [
            Tournament(
                name="Championship 2024",
                description="Torneio principal de 2024 com grandes prêmios",
                start_date=datetime.utcnow() - timedelta(days=30),
                end_date=datetime.utcnow() + timedelta(days=30),
                sort_criteria="points_desc"
            ),
            Tournament(
                name="Speed Tournament",
                description="Torneio de velocidade - pontuação reversa",
                start_date=datetime.utcnow() - timedelta(days=15),
                end_date=datetime.utcnow() + timedelta(days=15),
                sort_criteria="points_asc"
            ),
            Tournament(
                name="Classic Masters",
                description="Torneio clássico para mestres",
                start_date=datetime.utcnow() - timedelta(days=60),
                end_date=datetime.utcnow() - timedelta(days=10),
                sort_criteria="points_desc"
            )
        ]
        
        for tournament in tournaments:
            session.add(tournament)
        
        session.commit()
        
        # Criar jogadores
        players = [
            Player(name="João Silva", nickname="joao_master", email="joao@example.com"),
            Player(name="Maria Santos", nickname="maria_pro", email="maria@example.com"),
            Player(name="Pedro Lima", nickname="pedro_gamer", email="pedro@example.com"),
            Player(name="Ana Costa", nickname="ana_speed", email="ana@example.com"),
            Player(name="Carlos Oliveira", nickname="carlos_legend", email="carlos@example.com"),
            Player(name="Lucia Ferreira", nickname="lucia_star", email="lucia@example.com"),
            Player(name="Roberto Alves", nickname="roberto_ace", email="roberto@example.com"),
            Player(name="Patricia Sousa", nickname="patricia_elite", email="patricia@example.com"),
            Player(name="Fernando Dias", nickname="fernando_champ", email="fernando@example.com"),
            Player(name="Claudia Rocha", nickname="claudia_winner", email="claudia@example.com")
        ]
        
        for player in players:
            session.add(player)
        
        session.commit()
        
        # Buscar admin existente
        admin = session.query(Admin).first()
        if not admin:
            # Criar admin se não existir
            admin = Admin(
                name="System Admin",
                email="system@ranking.com",
                password_hash=get_password_hash("admin123"),
                permission_level="admin"
            )
            session.add(admin)
            session.commit()
        
        # Criar scores para Championship 2024
        championship = session.query(Tournament).filter(Tournament.name == "Championship 2024").first()
        scores_championship = [
            (1, 1250.5, "Excelente performance"),
            (2, 1180.0, "Muito bem jogado"),
            (3, 1150.5, "Boa estratégia"),
            (4, 1120.0, "Performance sólida"),
            (5, 1095.5, "Bom jogo"),
            (6, 1070.0, "Performance regular"),
            (7, 1045.5, "Precisa melhorar"),
            (8, 1020.0, "Jogo fraco"),
            (9, 995.5, "Muitos erros"),
            (10, 970.0, "Performance ruim")
        ]
        
        for i, (player_idx, points, notes) in enumerate(scores_championship):
            score = Score(
                player_id=player_idx,
                tournament_id=championship.id,
                points=points,
                notes=notes,
                admin_id=admin.id
            )
            session.add(score)
        
        # Criar scores para Speed Tournament (pontuação menor é melhor)
        speed = session.query(Tournament).filter(Tournament.name == "Speed Tournament").first()
        scores_speed = [
            (3, 45.2, "Tempo incrível"),
            (1, 47.8, "Muito rápido"),
            (5, 48.5, "Excelente tempo"),
            (7, 52.1, "Bom tempo"),
            (2, 53.7, "Tempo regular"),
            (9, 55.9, "Pode melhorar"),
            (4, 58.3, "Tempo lento"),
            (6, 61.5, "Muito lento")
        ]
        
        for player_idx, points, notes in scores_speed:
            score = Score(
                player_id=player_idx,
                tournament_id=speed.id,
                points=points,
                notes=notes,
                admin_id=admin.id
            )
            session.add(score)
        
        # Criar scores para Classic Masters
        classic = session.query(Tournament).filter(Tournament.name == "Classic Masters").first()
        scores_classic = [
            (2, 890.0, "Campeã absoluta"),
            (8, 875.5, "Segunda colocada"),
            (1, 860.0, "Terceiro lugar"),
            (10, 845.5, "Quarto lugar"),
            (6, 830.0, "Quinto lugar"),
            (4, 815.5, "Sexto lugar")
        ]
        
        for player_idx, points, notes in scores_classic:
            score = Score(
                player_id=player_idx,
                tournament_id=classic.id,
                points=points,
                notes=notes,
                admin_id=admin.id
            )
            session.add(score)
        
        session.commit()
        
        print("Sample data created successfully!")
        print(f"- Created {len(tournaments)} tournaments")
        print(f"- Created {len(players)} players")
        print(f"- Created scores for all tournaments")


if __name__ == "__main__":
    create_sample_data()