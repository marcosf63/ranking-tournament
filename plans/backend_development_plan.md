# Plano de Desenvolvimento Backend
## Sistema de Ranking de Torneio Online

---

**Agentes Responsáveis**: Tech Lead + Backend Developer + Product Manager  
**Stack**: Python + FastAPI + SQLModel + PostgreSQL  
**Versão**: 1.0  
**Data**: Agosto 2025  

---

## 🎯 Visão Geral do Backend

O backend será desenvolvido seguindo a arquitetura definida no documento técnico, utilizando FastAPI como framework principal, SQLModel para ORM e PostgreSQL como banco de dados. O sistema deve suportar autenticação JWT, CRUD completo para entidades principais e APIs públicas para visualização do ranking.

### Objetivos Principais
- Implementar todas as APIs conforme especificação OpenAPI
- Garantir performance < 3 segundos conforme RNF001
- Suportar até 1000 jogadores simultâneos (RNF002)
- Implementar segurança robusta com JWT e validações
- Criar sistema de audit log para rastreabilidade

---

## 📋 Fases de Desenvolvimento

### Fase 1: Setup e Infraestrutura Base (Sprint 1-2)

#### 1.1 Configuração do Ambiente
- [ ] **🏗️ Tech Lead**: Setup do projeto Python com venv e pip
  - Criar estrutura de pastas padrão FastAPI
  - Configurar requirements.txt conforme doc técnica
  - Setup de desenvolvimento com hot reload
  
- [ ] **⚙️ Backend Developer**: Configuração do FastAPI
  - Configurar aplicação principal com middleware
  - Setup de CORS para frontend
  - Configurar documentação OpenAPI/Swagger automática
  
- [ ] **🚀 DevOps Engineer**: Configuração do Banco de Dados
  - Setup PostgreSQL com Docker Compose
  - Configurar connection string e pooling
  - Implementar health check de database

#### 1.2 Estrutura Base do Projeto
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── core/
│   │   ├── config.py          # Settings e env vars
│   │   ├── security.py        # JWT e auth
│   │   └── database.py        # SQLModel engine
│   ├── models/                # SQLModel classes
│   ├── schemas/               # Pydantic schemas
│   ├── api/                   # Endpoints
│   │   ├── v1/
│   │   │   ├── admin/         # Admin endpoints
│   │   │   └── public/        # Public endpoints
│   └── services/              # Business logic
├── tests/                     # Test suite
├── alembic/                   # Database migrations
└── requirements.txt
```

#### 1.3 Configurações Base
- [ ] **🚀 DevOps Engineer**: Variáveis de Ambiente
  - DATABASE_URL
  - SECRET_KEY para JWT
  - CORS_ORIGINS
  - LOG_LEVEL
  
- [ ] **⚙️ Backend Developer**: Logging Estruturado
  - Configurar logging em formato JSON
  - Implementar correlation IDs
  - Setup de diferentes níveis por ambiente

---

### Fase 2: Modelos de Dados e Migrações (Sprint 2-3)

#### 2.1 Implementação dos Modelos SQLModel

- [ ] **⚙️ Backend Developer**: Tournament Model (Torneio)
  ```python
  class Tournament(SQLModel, table=True):
      id: Optional[int] = Field(primary_key=True)
      name: str = Field(max_length=255)
      description: Optional[str] = None
      start_date: datetime
      end_date: datetime
      logo_url: Optional[str] = None
      sort_criteria: str = Field(default="points_desc")
      created_at: datetime = Field(default_factory=datetime.utcnow)
      updated_at: datetime = Field(default_factory=datetime.utcnow)
  ```

- [ ] **⚙️ Backend Developer**: Player Model (Jogador)
  ```python
  class Player(SQLModel, table=True):
      id: Optional[int] = Field(primary_key=True)
      name: str = Field(max_length=255)
      nickname: str = Field(max_length=100, unique=True)
      email: Optional[str] = Field(max_length=255)
      avatar_url: Optional[str] = None
      is_active: bool = Field(default=True)
      created_at: datetime = Field(default_factory=datetime.utcnow)
      updated_at: datetime = Field(default_factory=datetime.utcnow)
  ```

- [ ] **⚙️ Backend Developer**: Score Model (Pontuação)
  ```python
  class Score(SQLModel, table=True):
      id: Optional[int] = Field(primary_key=True)
      player_id: int = Field(foreign_key="player.id")
      tournament_id: int = Field(foreign_key="tournament.id")
      points: float
      notes: Optional[str] = None
      admin_id: int = Field(foreign_key="admin.id")
      created_at: datetime = Field(default_factory=datetime.utcnow)
      updated_at: datetime = Field(default_factory=datetime.utcnow)
  ```

- [ ] **⚙️ Backend Developer**: Admin Model (Administrador)
  ```python
  class Admin(SQLModel, table=True):
      id: Optional[int] = Field(primary_key=True)
      name: str = Field(max_length=255)
      email: str = Field(max_length=255, unique=True)
      password_hash: str
      permission_level: str = Field(default="moderator")  # admin, moderator
      is_active: bool = Field(default=True)
      last_login: Optional[datetime] = None
      created_at: datetime = Field(default_factory=datetime.utcnow)
      updated_at: datetime = Field(default_factory=datetime.utcnow)
  ```

- [ ] **⚙️ Backend Developer**: AuditLog Model (Log de Auditoria)
  ```python
  class AuditLog(SQLModel, table=True):
      id: Optional[int] = Field(primary_key=True)
      table_name: str = Field(max_length=50)
      record_id: int
      action: str = Field(max_length=10)  # CREATE, UPDATE, DELETE
      old_values: Optional[dict] = Field(sa_column=Column(JSON))
      new_values: Optional[dict] = Field(sa_column=Column(JSON))
      admin_id: int = Field(foreign_key="admin.id")
      timestamp: datetime = Field(default_factory=datetime.utcnow)
  ```

#### 2.2 Configuração do Alembic
- [ ] **⚙️ Backend Developer**: Setup de Migrações
  - Configurar Alembic para SQLModel
  - Criar migração inicial com todas as tabelas
  - Implementar índices de performance conforme doc técnica
  - Criar dados seed para admin inicial

#### 2.3 Índices de Performance
- [ ] **🏗️ Tech Lead + ⚙️ Backend Developer**: Índices Essenciais
  - Índice composto em (player_id, tournament_id) para scores
  - Índice ordenado em (tournament_id, points DESC) para ranking
  - Índice único em nickname para busca rápida
  - Índice composto em (table_name, record_id) para audit logs

---

### Fase 3: Autenticação e Segurança (Sprint 3-4)

#### 3.1 Sistema de Autenticação JWT
- [ ] **⚙️ Backend Developer**: Implementar JWT Handler
  ```python
  # core/security.py
  def create_access_token(data: dict, expires_delta: Optional[timedelta] = None)
  def verify_token(token: str) -> Optional[dict]
  def get_password_hash(password: str) -> str
  def verify_password(plain_password: str, hashed_password: str) -> bool
  ```

- [ ] **⚙️ Backend Developer**: Middleware de Autenticação
  - Dependency para verificação de token
  - Dependency para verificação de nível de permissão
  - Rate limiting para endpoints de auth

#### 3.2 Endpoints de Autenticação
- [ ] **⚙️ Backend Developer**: POST /api/v1/auth/login
  - Validar credenciais admin
  - Gerar access token e refresh token
  - Registrar último login
  
- [ ] **⚙️ Backend Developer**: POST /api/v1/auth/refresh
  - Validar refresh token
  - Gerar novo access token
  
- [ ] **⚙️ Backend Developer**: POST /api/v1/auth/logout
  - Invalidar tokens (blacklist)

#### 3.3 Validações de Segurança
- [ ] **⚙️ Backend Developer**: Input Validation
  - Pydantic schemas para todos os endpoints
  - Sanitização de inputs
  - Validação de tipos e formatos
  
- [ ] **🏗️ Tech Lead**: SQL Injection Protection
  - Uso exclusivo de SQLModel/SQLAlchemy ORM
  - Validação de parâmetros de query
  
- [ ] **🚀 DevOps Engineer**: Rate Limiting
  - Limite de requests por IP
  - Limite especial para endpoints de auth

---

### Fase 4: APIs Administrativas (Sprint 4-6)

#### 4.1 Gerenciamento de Jogadores
- [ ] **⚙️ Backend Developer**: GET /api/v1/admin/players
  - Listar jogadores com paginação
  - Filtros: ativo/inativo, busca por nome/nickname
  - Ordenação configurável
  
- [ ] **⚙️ Backend Developer**: POST /api/v1/admin/players
  - Criar novo jogador
  - Validações: nickname único, email válido
  - Upload de avatar (opcional)
  
- [ ] **⚙️ Backend Developer**: GET /api/v1/admin/players/{id}
  - Detalhes completos do jogador
  - Histórico de pontuações
  
- [ ] **⚙️ Backend Developer**: PUT /api/v1/admin/players/{id}
  - Atualizar dados do jogador
  - Validações de integridade
  
- [ ] **⚙️ Backend Developer**: DELETE /api/v1/admin/players/{id}
  - Soft delete (marcar como inativo)
  - Validar se não há pontuações ativas
  
- [ ] **⚙️ Backend Developer**: POST /api/v1/admin/players/import
  - Importação em lote via CSV
  - Validação de formato e dados
  - Preview antes da importação

#### 4.2 Gerenciamento de Pontuações
- [ ] **⚙️ Backend Developer**: GET /api/v1/admin/scores
  - Listar pontuações com filtros
  - Filtros: jogador, data, admin responsável
  - Ordenação por data/pontuação
  
- [ ] **⚙️ Backend Developer**: POST /api/v1/admin/scores
  - Adicionar nova pontuação
  - Recalcular ranking automaticamente
  - Registrar audit log
  
- [ ] **⚙️ Backend Developer**: PUT /api/v1/admin/scores/{id}
  - Atualizar pontuação existente
  - Recalcular ranking
  - Audit log da alteração
  
- [ ] **⚙️ Backend Developer**: DELETE /api/v1/admin/scores/{id}
  - Remover pontuação
  - Confirmação obrigatória
  - Recalcular ranking

#### 4.3 Gerenciamento de Administradores
- [ ] **⚙️ Backend Developer**: GET /api/v1/admin/users
  - Listar administradores (apenas para admin level)
  - Filtros por nível e status
  
- [ ] **⚙️ Backend Developer**: POST /api/v1/admin/users
  - Criar novo administrador
  - Validações de senha forte
  - Hash de senha com bcrypt
  
- [ ] **⚙️ Backend Developer**: PUT /api/v1/admin/users/{id}/password
  - Alterar senha (própria ou por admin superior)
  - Validar senha atual
  - Hash da nova senha

#### 4.4 Configuração do Torneio
- [ ] **⚙️ Backend Developer**: GET /api/v1/admin/tournament
  - Obter configurações atuais do torneio
  
- [ ] **⚙️ Backend Developer**: PUT /api/v1/admin/tournament
  - Atualizar configurações do torneio
  - Upload de logo oficial
  - Validar datas de início/fim

---

### Fase 5: APIs Públicas (Sprint 6-7)

#### 5.1 Ranking Público
- [ ] **⚙️ Backend Developer**: GET /api/v1/public/ranking
  - Ranking ordenado por critério configurado
  - Paginação para performance
  - Cache para otimização
  - Filtros por faixa de pontuação
  
- [ ] **⚙️ Backend Developer**: GET /api/v1/public/players/{id}
  - Informações públicas do jogador
  - Histórico de pontuações (público)
  - Posição atual no ranking

#### 5.2 Estatísticas Públicas
- [ ] **⚙️ Backend Developer**: GET /api/v1/public/stats
  - Total de participantes
  - Última atualização do ranking
  - Pontuação média
  - Estatísticas gerais do torneio

#### 5.3 Busca e Filtros
- [ ] **⚙️ Backend Developer**: GET /api/v1/public/search
  - Busca por nome/nickname de jogador
  - Busca fuzzy para tolerância a erros
  - Resultados ordenados por relevância

---

### Fase 6: Lógica de Negócio e Serviços (Sprint 7-8)

#### 6.1 Serviço de Ranking
- [ ] **⚙️ Backend Developer**: RankingService
  ```python
  class RankingService:
      async def calculate_ranking(tournament_id: int) -> List[RankingEntry]
      async def update_player_position(player_id: int, tournament_id: int)
      async def get_ranking_page(page: int, size: int) -> PaginatedRanking
  ```

#### 6.2 Serviço de Audit
- [ ] **⚙️ Backend Developer**: AuditService
  ```python
  class AuditService:
      async def log_action(table: str, record_id: int, action: str, old_data: dict, new_data: dict, admin_id: int)
      async def get_audit_trail(table: str, record_id: int) -> List[AuditLog]
  ```

#### 6.3 Serviço de Import/Export
- [ ] **⚙️ Backend Developer**: ImportService
  ```python
  class ImportService:
      async def validate_csv(file_content: str) -> ImportValidation
      async def preview_import(file_content: str) -> ImportPreview
      async def execute_import(file_content: str, admin_id: int) -> ImportResult
  ```

---

### Fase 7: Testes Automatizados (Sprint 8-9)

#### 7.1 Setup de Testes
- [ ] **🧪 QA Engineer**: Configuração pytest
  - Test database com SQLite in-memory
  - Fixtures para dados de teste
  - Mock de dependências externas
  
- [ ] **🧪 QA Engineer + ⚙️ Backend Developer**: Test Client FastAPI
  - Cliente de teste configurado
  - Headers de autenticação para testes admin

#### 7.2 Testes de Unidade
- [ ] **🧪 QA Engineer + ⚙️ Backend Developer**: Testes de Modelos
  - Validações SQLModel
  - Relacionamentos entre entidades
  - Constraints e índices
  
- [ ] **🧪 QA Engineer + ⚙️ Backend Developer**: Testes de Serviços
  - Lógica de ranking
  - Cálculos de pontuação
  - Audit logging
  - Import/export functionality

#### 7.3 Testes de Integração
- [ ] **🧪 QA Engineer**: Testes de API
  - Todos os endpoints administrativos
  - Todos os endpoints públicos
  - Cenários de erro e edge cases
  - Autenticação e autorização
  
- [ ] **🧪 QA Engineer + 🏗️ Tech Lead**: Testes de Performance
  - Endpoints de ranking com grande volume de dados
  - Queries de banco otimizadas
  - Memory usage e response times

#### 7.4 Cobertura de Testes
- [ ] **🧪 QA Engineer**: Meta de Cobertura: 85%+
  - Unit tests: 90%+
  - Integration tests: 80%+
  - Coverage report automatizado

---

### Fase 8: Performance e Otimização (Sprint 9-10)

#### 8.1 Otimizações de Database
- [ ] **🏗️ Tech Lead + ⚙️ Backend Developer**: Query Optimization
  - EXPLAIN ANALYZE para queries críticas
  - Otimização de queries de ranking
  - Connection pooling configurado
  
- [ ] **🏗️ Tech Lead**: Indexação Avançada
  - Índices compostos para queries complexas
  - Índices parciais quando aplicável
  - Monitoramento de uso de índices

#### 8.2 Cache e Performance
- [ ] **🚀 DevOps Engineer + ⚙️ Backend Developer**: Response Caching
  - Cache de ranking público (Redis futuro)
  - Headers de cache apropriados
  - Invalidação inteligente de cache
  
- [ ] **⚙️ Backend Developer**: Async Operations
  - Operações de I/O assíncronas
  - Bulk operations otimizadas
  - Background tasks para operações pesadas

#### 8.3 Monitoramento
- [ ] **🚀 DevOps Engineer**: Health Checks
  - Endpoint /health para liveness probe
  - Endpoint /ready para readiness probe
  - Database connectivity check
  
- [ ] **🚀 DevOps Engineer**: Métricas de Performance
  - Response time por endpoint
  - Database query performance
  - Memory usage tracking
  - Error rate monitoring

---

### Fase 9: Segurança Avançada e Compliance (Sprint 10)

#### 9.1 Hardening de Segurança
- [ ] **🚀 DevOps Engineer + 🏗️ Tech Lead**: Headers de Segurança
  - CORS configurado corretamente
  - Security headers (HSTS, CSP, etc.)
  - Input sanitization avançada
  
- [ ] **🚀 DevOps Engineer**: Auditoria de Segurança
  - Scan de vulnerabilidades
  - Dependency check para CVEs
  - Penetration testing básico

#### 9.2 Backup e Recovery
- [ ] **🚀 DevOps Engineer**: Estratégia de Backup
  - Backup automático do PostgreSQL
  - Point-in-time recovery capability
  - Testes de restore regulares
  
- [ ] **🚀 DevOps Engineer + 📝 Tech Writer**: Disaster Recovery
  - Procedimentos documentados
  - RTO/RPO definidos conforme doc técnica
  - Runbooks para cenários críticos

---

## 📊 Critérios de Aceitação por Fase

### Fase 1 ✅
- [ ] Aplicação FastAPI rodando com hot reload
- [ ] PostgreSQL conectado e funcional
- [ ] Swagger UI acessível em /docs
- [ ] Docker Compose configurado para desenvolvimento

### Fase 2 ✅
- [ ] Todos os modelos SQLModel implementados
- [ ] Migrações Alembic funcionando
- [ ] Índices de performance criados
- [ ] Admin seed data inserido

### Fase 3 ✅
- [ ] Login admin funcional com JWT
- [ ] Middleware de autenticação ativo
- [ ] Rate limiting implementado
- [ ] Testes de segurança passando

### Fase 4 ✅
- [ ] Todos os CRUDs administrativos funcionais
- [ ] Importação CSV implementada
- [ ] Audit log registrando todas as ações
- [ ] Validações de negócio implementadas

### Fase 5 ✅
- [ ] APIs públicas retornando dados corretos
- [ ] Ranking calculado automaticamente
- [ ] Busca funcionando corretamente
- [ ] Performance < 3 segundos conforme RNF001

### Fases 6-9 ✅
- [ ] Testes automatizados > 85% cobertura
- [ ] Performance otimizada
- [ ] Segurança hardened
- [ ] Documentação API completa

---

## 🛠️ Stack Técnica Detalhada

### Core Dependencies
```txt
fastapi==0.104.1
sqlmodel==0.0.14
alembic==1.12.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
psycopg2-binary==2.9.9
asyncpg==0.29.0
```

### Development Dependencies
```txt
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
black==23.11.0
flake8==6.1.0
mypy==1.7.1
pre-commit==3.5.0
```

---

## 📋 Checklist de Entrega Final

### Funcionalidades Core
- [ ] Sistema de autenticação JWT completo
- [ ] CRUD completo de jogadores, pontuações e admins
- [ ] Ranking público em tempo real
- [ ] Importação CSV com validação
- [ ] Audit log de todas as operações

### Qualidade e Performance
- [ ] Cobertura de testes > 85%
- [ ] Performance < 3s para todas as APIs
- [ ] Documentação OpenAPI completa
- [ ] Code review aprovado pelo Tech Lead

### Segurança
- [ ] Autenticação e autorização implementadas
- [ ] Rate limiting ativo
- [ ] Input validation em todos os endpoints
- [ ] Scan de segurança sem issues críticos

### Operações
- [ ] Health checks funcionais
- [ ] Logging estruturado implementado
- [ ] Métricas de performance disponíveis
- [ ] Backup strategy documentada

---

## 🎯 Próximos Passos

1. **Review com Product Manager**: Validar alinhamento com requisitos de negócio
2. **Review com Tech Lead**: Aprovar arquitetura e padrões técnicos  
3. **Kickoff com Backend Developer**: Iniciar implementação seguindo este plano
4. **Sync com QA Engineer**: Alinhar estratégia de testes desde o início
5. **Coordenação com DevOps**: Preparar ambientes conforme as fases

---

*Este plano foi elaborado pelos agentes Tech Lead, Backend Developer e Product Manager, baseado na documentação completa do projeto Sistema de Ranking de Torneio Online.*