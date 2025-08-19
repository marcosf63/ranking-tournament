"""
Testes unitários para autenticação
"""
import pytest
from datetime import datetime, timedelta

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_password_hash,
    verify_password
)


class TestPasswordHashing:
    """Testes para hash de senhas"""
    
    def test_password_hashing(self):
        """Testar criação e verificação de hash de senha"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        # Hash deve ser diferente da senha original
        assert hashed != password
        
        # Verificação deve ser verdadeira
        assert verify_password(password, hashed) is True
        
        # Senha errada deve retornar False
        assert verify_password("wrong_password", hashed) is False
    
    def test_different_passwords_different_hashes(self):
        """Testar que senhas diferentes geram hashes diferentes"""
        password1 = "password1"
        password2 = "password2"
        
        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)
        
        assert hash1 != hash2
    
    def test_same_password_different_hashes(self):
        """Testar que a mesma senha pode gerar hashes diferentes (salt)"""
        password = "same_password"
        
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Hashes podem ser diferentes devido ao salt, mas ambos devem verificar
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Testes para tokens JWT"""
    
    def test_create_access_token(self):
        """Testar criação de token de acesso"""
        data = {"sub": "1", "admin_id": 1}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert "." in token  # JWT tem pontos separando as partes
    
    def test_create_refresh_token(self):
        """Testar criação de token de refresh"""
        data = {"sub": "1", "admin_id": 1}
        token = create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        assert "." in token
    
    def test_verify_valid_access_token(self):
        """Testar verificação de token de acesso válido"""
        data = {"sub": "1", "admin_id": 1}
        token = create_access_token(data)
        
        payload = verify_token(token, "access")
        
        assert payload is not None
        assert payload["sub"] == "1"
        assert payload["admin_id"] == 1
        assert payload["type"] == "access"
    
    def test_verify_valid_refresh_token(self):
        """Testar verificação de token de refresh válido"""
        data = {"sub": "1", "admin_id": 1}
        token = create_refresh_token(data)
        
        payload = verify_token(token, "refresh")
        
        assert payload is not None
        assert payload["sub"] == "1"
        assert payload["admin_id"] == 1
        assert payload["type"] == "refresh"
    
    def test_verify_wrong_token_type(self):
        """Testar verificação de token com tipo errado"""
        data = {"sub": "1", "admin_id": 1}
        access_token = create_access_token(data)
        
        # Tentar verificar access token como refresh
        payload = verify_token(access_token, "refresh")
        
        assert payload is None
    
    def test_verify_invalid_token(self):
        """Testar verificação de token inválido"""
        invalid_token = "invalid.jwt.token"
        
        payload = verify_token(invalid_token, "access")
        
        assert payload is None
    
    def test_verify_expired_token(self):
        """Testar verificação de token expirado"""
        data = {"sub": "1", "admin_id": 1}
        
        # Criar token com expiração no passado
        expired_delta = timedelta(seconds=-1)
        token = create_access_token(data, expired_delta)
        
        # Token deve ser considerado inválido
        payload = verify_token(token, "access")
        
        assert payload is None
    
    def test_token_contains_expiration(self):
        """Testar que o token contém informações de expiração"""
        data = {"sub": "1", "admin_id": 1}
        token = create_access_token(data)
        
        payload = verify_token(token, "access")
        
        assert payload is not None
        assert "exp" in payload
        
        # Expiração deve ser no futuro
        exp_timestamp = payload["exp"]
        current_timestamp = datetime.utcnow().timestamp()
        assert exp_timestamp > current_timestamp
    
    def test_custom_expiration_time(self):
        """Testar token com tempo de expiração customizado"""
        data = {"sub": "1", "admin_id": 1}
        custom_delta = timedelta(hours=2)
        
        token = create_access_token(data, custom_delta)
        payload = verify_token(token, "access")
        
        assert payload is not None
        
        # Verificar que a expiração está aproximadamente em 2 horas
        exp_timestamp = payload["exp"]
        expected_exp = datetime.utcnow() + custom_delta
        
        # Margem de erro de 10 segundos
        assert abs(exp_timestamp - expected_exp.timestamp()) < 10


class TestTokenIntegration:
    """Testes de integração para tokens"""
    
    def test_full_token_cycle(self):
        """Testar ciclo completo de criação e verificação de token"""
        # Dados do admin
        admin_data = {
            "sub": "123",
            "admin_id": 123,
            "email": "test@admin.com"
        }
        
        # Criar tokens
        access_token = create_access_token(admin_data)
        refresh_token = create_refresh_token(admin_data)
        
        # Verificar access token
        access_payload = verify_token(access_token, "access")
        assert access_payload is not None
        assert access_payload["admin_id"] == 123
        assert access_payload["type"] == "access"
        
        # Verificar refresh token
        refresh_payload = verify_token(refresh_token, "refresh")
        assert refresh_payload is not None
        assert refresh_payload["admin_id"] == 123
        assert refresh_payload["type"] == "refresh"
        
        # Verificar que não são intercambiáveis
        assert verify_token(access_token, "refresh") is None
        assert verify_token(refresh_token, "access") is None