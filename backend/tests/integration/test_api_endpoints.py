"""
Testes de integração para endpoints da API
"""
import pytest
from fastapi import status


class TestAuthEndpoints:
    """Testes para endpoints de autenticação"""
    
    def test_login_success(self, client, test_admin):
        """Testar login bem-sucedido"""
        login_data = {
            "email": test_admin.email,
            "password": "testpass"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "admin" in data
        assert "tokens" in data
        assert data["admin"]["email"] == test_admin.email
        assert data["tokens"]["token_type"] == "bearer"
        assert len(data["tokens"]["access_token"]) > 0
    
    def test_login_invalid_credentials(self, client, test_admin):
        """Testar login com credenciais inválidas"""
        login_data = {
            "email": test_admin.email,
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client):
        """Testar login com usuário inexistente"""
        login_data = {
            "email": "nonexistent@email.com",
            "password": "password"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_refresh_token(self, client, test_admin):
        """Testar renovação de token"""
        # Fazer login primeiro
        login_data = {
            "email": test_admin.email,
            "password": "testpass"
        }
        login_response = client.post("/api/v1/auth/login", json=login_data)
        refresh_token = login_response.json()["tokens"]["refresh_token"]
        
        # Renovar token
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_logout(self, client, auth_headers):
        """Testar logout"""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        assert "Logout successful" in response.json()["message"]


class TestPlayerEndpoints:
    """Testes para endpoints de jogadores"""
    
    def test_list_players_authenticated(self, client, auth_headers, test_player):
        """Testar listagem de jogadores autenticado"""
        response = client.get("/api/v1/admin/players/", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "players" in data
        assert "total" in data
        assert data["total"] >= 1
        assert len(data["players"]) >= 1
    
    def test_list_players_unauthenticated(self, client, test_player):
        """Testar listagem de jogadores sem autenticação"""
        response = client.get("/api/v1/admin/players/")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_player(self, client, auth_headers):
        """Testar criação de jogador"""
        player_data = {
            "name": "New Player",
            "nickname": "new_player",
            "email": "new@player.com"
        }
        
        response = client.post("/api/v1/admin/players/", 
                             json=player_data, 
                             headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["name"] == player_data["name"]
        assert data["nickname"] == player_data["nickname"]
        assert data["email"] == player_data["email"]
        assert "id" in data
    
    def test_get_player_by_id(self, client, auth_headers, test_player):
        """Testar obtenção de jogador por ID"""
        response = client.get(f"/api/v1/admin/players/{test_player.id}", 
                            headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["id"] == test_player.id
        assert data["name"] == test_player.name
        assert data["nickname"] == test_player.nickname
    
    def test_update_player(self, client, auth_headers, test_player):
        """Testar atualização de jogador"""
        update_data = {
            "name": "Updated Player Name"
        }
        
        response = client.put(f"/api/v1/admin/players/{test_player.id}",
                            json=update_data,
                            headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["id"] == test_player.id
    
    def test_delete_player(self, client, auth_headers, test_player):
        """Testar desativação de jogador"""
        response = client.delete(f"/api/v1/admin/players/{test_player.id}",
                               headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        assert "deactivated successfully" in response.json()["message"]


class TestTournamentEndpoints:
    """Testes para endpoints de torneios"""
    
    def test_list_tournaments(self, client, auth_headers, test_tournament):
        """Testar listagem de torneios"""
        response = client.get("/api/v1/admin/tournaments/", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "tournaments" in data
        assert "total" in data
        assert data["total"] >= 1
    
    def test_create_tournament(self, client, auth_headers):
        """Testar criação de torneio"""
        tournament_data = {
            "name": "New Tournament",
            "description": "A new test tournament",
            "start_date": "2025-01-01T00:00:00",
            "end_date": "2025-12-31T23:59:59"
        }
        
        response = client.post("/api/v1/admin/tournaments/",
                             json=tournament_data,
                             headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["name"] == tournament_data["name"]
        assert data["description"] == tournament_data["description"]
        assert "id" in data
    
    def test_get_tournament_by_id(self, client, auth_headers, test_tournament):
        """Testar obtenção de torneio por ID"""
        response = client.get(f"/api/v1/admin/tournaments/{test_tournament.id}",
                            headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["id"] == test_tournament.id
        assert data["name"] == test_tournament.name


class TestScoreEndpoints:
    """Testes para endpoints de pontuações"""
    
    def test_list_scores(self, client, auth_headers, test_score):
        """Testar listagem de pontuações"""
        response = client.get("/api/v1/admin/scores/", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "scores" in data
        assert "total" in data
        assert data["total"] >= 1
    
    def test_create_score(self, client, auth_headers, test_player, test_tournament):
        """Testar criação de pontuação"""
        score_data = {
            "player_id": test_player.id,
            "tournament_id": test_tournament.id,
            "points": 150.5,
            "notes": "Test score creation"
        }
        
        response = client.post("/api/v1/admin/scores/",
                             json=score_data,
                             headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["player_id"] == score_data["player_id"]
        assert data["tournament_id"] == score_data["tournament_id"]
        assert data["points"] == score_data["points"]
        assert data["notes"] == score_data["notes"]
    
    def test_get_score_by_id(self, client, auth_headers, test_score):
        """Testar obtenção de pontuação por ID"""
        response = client.get(f"/api/v1/admin/scores/{test_score.id}",
                            headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["id"] == test_score.id
        assert data["points"] == test_score.points


class TestPublicEndpoints:
    """Testes para endpoints públicos"""
    
    def test_general_ranking(self, client, sample_data):
        """Testar ranking geral público"""
        response = client.get("/api/v1/public/ranking/")
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "entries" in data
        assert "total" in data
        assert "ranking_type" in data
        assert data["ranking_type"] == "general"
    
    def test_tournament_ranking(self, client, sample_data):
        """Testar ranking de torneio específico"""
        tournament = sample_data['tournaments'][0]
        
        response = client.get(f"/api/v1/public/ranking/tournament/{tournament.id}")
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "tournament_id" in data
        assert "entries" in data
        assert data["tournament_id"] == tournament.id
    
    def test_general_stats(self, client, sample_data):
        """Testar estatísticas gerais"""
        response = client.get("/api/v1/public/ranking/stats")
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "total_players" in data
        assert "total_tournaments" in data
        assert "total_scores" in data
        assert data["total_players"] >= 3
        assert data["total_tournaments"] >= 2
    
    def test_search_players(self, client, sample_data):
        """Testar busca de jogadores"""
        response = client.get("/api/v1/public/search/players?query=Player")
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        if data:
            player = data[0]
            assert "id" in player
            assert "name" in player
            assert "nickname" in player
    
    def test_search_tournaments(self, client, sample_data):
        """Testar busca de torneios"""
        response = client.get("/api/v1/public/search/tournaments?query=Tournament")
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_search_suggestions(self, client, sample_data):
        """Testar sugestões de busca"""
        response = client.get("/api/v1/public/search/suggestions?query=P")
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "query" in data
        assert "suggestions" in data
        assert data["query"] == "P"


class TestPagination:
    """Testes para paginação"""
    
    def test_players_pagination(self, client, auth_headers, multiple_players):
        """Testar paginação de jogadores"""
        # Página 1 com tamanho 2
        response = client.get("/api/v1/admin/players/?page=1&size=2", 
                            headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 2
        assert len(data["players"]) <= 2
        assert data["total"] >= 5
        assert data["pages"] >= 3
    
    def test_ranking_pagination(self, client, sample_data):
        """Testar paginação do ranking"""
        response = client.get("/api/v1/public/ranking/?page=1&size=2")
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 2
        assert len(data["entries"]) <= 2


class TestErrorHandling:
    """Testes para tratamento de erros"""
    
    def test_get_nonexistent_player(self, client, auth_headers):
        """Testar busca de jogador inexistente"""
        response = client.get("/api/v1/admin/players/99999", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_create_duplicate_player_email(self, client, auth_headers, test_player):
        """Testar criação de jogador com email duplicado"""
        player_data = {
            "name": "Another Player",
            "nickname": "another_player", 
            "email": test_player.email  # Email duplicado
        }
        
        response = client.post("/api/v1/admin/players/",
                             json=player_data,
                             headers=auth_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_invalid_tournament_dates(self, client, auth_headers):
        """Testar criação de torneio com datas inválidas"""
        tournament_data = {
            "name": "Invalid Tournament",
            "description": "Tournament with invalid dates",
            "start_date": "2025-12-31T23:59:59",
            "end_date": "2025-01-01T00:00:00"  # Data final antes da inicial
        }
        
        response = client.post("/api/v1/admin/tournaments/",
                             json=tournament_data,
                             headers=auth_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST