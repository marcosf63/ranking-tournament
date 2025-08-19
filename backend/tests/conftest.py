
"""
Configuração dos testes com pytest
"""
import pytest
import pytest_asyncio
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app
from app.core.database import get_async_session
from app.core.security import get_password_hash, create_access_token
from app.models import Admin, Player, Tournament, Score

# Banco de dados de teste em memória com driver assíncrono
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
async_test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)


@pytest_asyncio.fixture(scope="function")
async def session() -> AsyncSession:
    """Fixture para sessão de banco de dados de teste assíncrona"""
    # Criar tabelas
    async with async_test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    # Sessão para o teste
    async with AsyncSession(async_test_engine) as session:
        yield session
    
    # Limpar após o teste
    async with async_test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture(scope="function")
def client(session: AsyncSession):
    """Fixture para cliente de teste do FastAPI com override de sessão assíncrona"""
    
    def get_session_override():
        return session
    
    app.dependency_overrides[get_async_session] = get_session_override
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_admin(session: AsyncSession) -> Admin:
    """Fixture para admin de teste"""
    admin = Admin(
        name="Test Admin",
        email="test@admin.com",
        password_hash=get_password_hash("testpass"),
        permission_level="admin",
        is_active=True
    )
    session.add(admin)
    await session.commit()
    await session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def test_player(session: AsyncSession) -> Player:
    """Fixture para jogador de teste"""
    player = Player(
        name="Test Player",
        nickname="test_player",
        email="test@player.com",
        is_active=True
    )
    session.add(player)
    await session.commit()
    await session.refresh(player)
    return player


@pytest_asyncio.fixture
async def test_tournament(session: AsyncSession) -> Tournament:
    """Fixture para torneio de teste"""
    tournament = Tournament(
        name="Test Tournament",
        description="Tournament for testing",
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 12, 31),
        sort_criteria="points_desc"
    )
    session.add(tournament)
    await session.commit()
    await session.refresh(tournament)
    return tournament


@pytest_asyncio.fixture
async def test_score(session: AsyncSession, test_player: Player, test_tournament: Tournament, test_admin: Admin) -> Score:
    """Fixture para pontuação de teste"""
    score = Score(
        player_id=test_player.id,
        tournament_id=test_tournament.id,
        points=100.0,
        notes="Test score",
        admin_id=test_admin.id
    )
    session.add(score)
    await session.commit()
    await session.refresh(score)
    return score


@pytest.fixture
def auth_headers(test_admin: Admin):
    """Fixture para headers de autenticação"""
    token = create_access_token(data={"sub": str(test_admin.id), "admin_id": test_admin.id})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def multiple_players(session: AsyncSession) -> list[Player]:
    """Fixture para múltiplos jogadores"""
    players = []
    for i in range(5):
        player = Player(
            name=f"Player {i+1}",
            nickname=f"player_{i+1}",
            email=f"player{i+1}@test.com",
            is_active=True
        )
        session.add(player)
        players.append(player)
    
    await session.commit()
    
    for player in players:
        await session.refresh(player)
    
    return players


@pytest_asyncio.fixture
async def sample_data(session: AsyncSession, test_admin: Admin):
    """Fixture para dados de exemplo completos"""
    players = []
    for i in range(3):
        player = Player(name=f"Player {i+1}", nickname=f"player_{i+1}")
        session.add(player)
        players.append(player)
    
    tournaments = []
    for i in range(2):
        tournament = Tournament(name=f"Tournament {i+1}", start_date=datetime.now(), end_date=datetime.now() + timedelta(days=1))
        session.add(tournament)
        tournaments.append(tournament)
    
    await session.commit()
    
    for p in players: await session.refresh(p)
    for t in tournaments: await session.refresh(t)
    
    scores = []
    points_matrix = [[100, 200], [150, 180], [120, 190]]
    
    for i, player in enumerate(players):
        for j, tournament in enumerate(tournaments):
            score = Score(player_id=player.id, tournament_id=tournament.id, points=points_matrix[i][j], admin_id=test_admin.id)
            session.add(score)
            scores.append(score)
    
    await session.commit()
    for s in scores: await session.refresh(s)
    
    return {
        'players': players,
        'tournaments': tournaments,
        'scores': scores,
        'admin': test_admin
    }
