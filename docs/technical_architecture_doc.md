# Documento de Arquitetura Técnica
## Sistema de Ranking de Torneio Online

---

**Versão**: 1.0  
**Data**: Agosto 2025  
**Projeto**: Sistema de Ranking de Torneio Online  

---

## 1. Visão Geral da Arquitetura

### 1.1 Objetivo
Este documento define a arquitetura técnica, tecnologias, padrões e estruturas utilizadas no desenvolvimento do Sistema de Ranking de Torneio Online, conforme especificado no PRD versão 1.0.

### 1.2 Escopo
O sistema será desenvolvido como uma aplicação web moderna com arquitetura cliente-servidor, separando claramente as responsabilidades entre frontend, backend e persistência de dados.

### 1.3 Princípios Arquiteturais
- **Separação de responsabilidades**: Frontend e Backend independentes
- **RESTful API**: Comunicação padronizada via HTTP/JSON
- **Segurança por design**: Autenticação e autorização em todas as camadas
- **Escalabilidade horizontal**: Preparado para crescimento futuro
- **Observabilidade**: Logs estruturados e monitoramento

## 2. Stack Tecnológica

### 2.1 Backend
- **Linguagem**: Python 3.11+
- **Framework**: FastAPI 0.104+
- **ORM**: SQLModel 0.0.14+ (baseado em SQLAlchemy 2.0 + Pydantic v2)
- **Migrações**: Alembic para migrações de banco de dados
- **CLI**: Typer para interface de linha de comando
- **Autenticação**: JWT (JSON Web Tokens) com python-jose
- **Documentação**: OpenAPI/Swagger (automática via FastAPI)

### 2.2 Frontend
- **Framework**: React 18+ com TypeScript
- **Build Tool**: Vite 5+
- **Roteamento**: React Router DOM v6
- **Estado Global**: Zustand ou Redux Toolkit
- **UI Components**: Material-UI (MUI) v5 ou Tailwind CSS + Headless UI
- **HTTP Client**: Axios
- **Formulários**: React Hook Form + Zod para validação

### 2.3 Banco de Dados
- **SGBD**: PostgreSQL 15+
- **Connection Pool**: SQLAlchemy com asyncpg
- **Backup**: pg_dump automatizado
- **Indexação**: Índices otimizados para consultas de ranking

### 2.4 Infraestrutura e Deploy
- **Containerização**: Docker + Docker Compose
- **Reverse Proxy**: Nginx
- **SSL**: Let's Encrypt (Certbot)
- **Monitoramento**: Prometheus + Grafana (opcional)
- **Logs**: Estruturados em JSON com Python logging

### 2.5 Desenvolvimento
- **Controle de Versão**: Git
- **Code Quality**: 
  - Backend: Black (formatação), Flake8 (linting), mypy (type checking)
  - Frontend: ESLint + Prettier
- **Testes**: 
  - Backend: pytest + pytest-asyncio
  - Frontend: Jest + React Testing Library
- **Pre-commit**: Hooks para qualidade de código

## 3. Arquitetura do Sistema

### 3.1 Visão Geral
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│  (PostgreSQL)   │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         │              ┌─────────────────┐
         └──────────────►│   Nginx         │
                        │   Port: 80/443  │
                        └─────────────────┘
```

### 3.2 Padrões Arquiteturais
- **Repository Pattern**: Para abstração de acesso a dados
- **Dependency Injection**: FastAPI nativo para injeção de dependências
- **Service Layer**: Lógica de negócio separada dos endpoints
- **DTO Pattern**: SQLModel classes para transferência de dados
- **Error Handling**: Middleware centralizado para tratamento de erros

## 4. Modelo de Dados

### 4.1 Entidades Principais

#### Tournaments (Torneios)
- ID único, nome, descrição
- Datas de início e fim
- Logo oficial e critérios de ordenação
- Timestamps de criação e atualização

#### Players (Jogadores)
- ID único, nome completo e nickname
- Email e avatar (opcionais)
- Status ativo/inativo
- Timestamps de criação e atualização

#### Scores (Pontuações)
- ID único, referência ao jogador e torneio
- Valor da pontuação e observações
- Referência ao administrador responsável
- Timestamps de criação e atualização

#### Admins (Administradores)
- ID único, nome e email
- Hash da senha e nível de permissão
- Status ativo/inativo e último login
- Timestamps de criação e atualização

#### Audit Logs (Logs de Auditoria)
- ID único, nome da tabela e ID do registro
- Ação realizada (CREATE, UPDATE, DELETE)
- Valores antigos e novos (JSONB)
- Referência ao administrador e timestamp

### 4.2 Relacionamentos
- **Player ↔ Score**: Um jogador pode ter múltiplas pontuações (1:N)
- **Tournament ↔ Score**: Um torneio pode ter múltiplas pontuações (1:N)
- **Admin ↔ Score**: Um admin pode registrar múltiplas pontuações (1:N)
- **Admin ↔ Audit Log**: Um admin pode ter múltiplas ações auditadas (1:N)

### 4.3 Índices de Performance
- Índice composto em (player_id, tournament_id) para scores
- Índice ordenado em (tournament_id, points DESC) para ranking
- Índice único em nickname para busca rápida de jogadores
- Índice composto em (table_name, record_id) para audit logs

## 5. API Design

### 5.1 Estrutura de URLs

#### Autenticação
- `POST /api/v1/auth/login` - Login de administrador
- `POST /api/v1/auth/refresh` - Renovação de token
- `POST /api/v1/auth/logout` - Logout

#### Gerenciamento de Jogadores (Admin)
- `GET /api/v1/admin/players` - Listar jogadores
- `POST /api/v1/admin/players` - Criar jogador
- `GET /api/v1/admin/players/{id}` - Detalhes do jogador
- `PUT /api/v1/admin/players/{id}` - Atualizar jogador
- `DELETE /api/v1/admin/players/{id}` - Remover jogador
- `POST /api/v1/admin/players/import` - Importar via CSV

#### Gerenciamento de Pontuações (Admin)
- `GET /api/v1/admin/scores` - Listar pontuações
- `POST /api/v1/admin/scores` - Adicionar pontuação
- `PUT /api/v1/admin/scores/{id}` - Atualizar pontuação
- `DELETE /api/v1/admin/scores/{id}` - Remover pontuação

#### Gerenciamento de Administradores (Admin)
- `GET /api/v1/admin/users` - Listar administradores
- `POST /api/v1/admin/users` - Criar novo administrador
- `GET /api/v1/admin/users/{id}` - Detalhes do administrador
- `PUT /api/v1/admin/users/{id}` - Atualizar administrador
- `PUT /api/v1/admin/users/{id}/password` - Alterar senha
- `DELETE /api/v1/admin/users/{id}` - Desativar administrador

#### Configuração do Torneio (Admin)
- `GET /api/v1/admin/tournament` - Obter configurações
- `PUT /api/v1/admin/tournament` - Atualizar configurações

#### API Pública
- `GET /api/v1/public/ranking` - Obter ranking
- `GET /api/v1/public/players/{id}` - Informações públicas do jogador
- `GET /api/v1/public/stats` - Estatísticas do torneio

### 5.2 Padrões de Response

#### Resposta de Sucesso
- Status code apropriado (200, 201, 204)
- Dados solicitados no campo `data`
- Metadados de paginação quando aplicável
- Mensagem descritiva quando necessário

#### Resposta de Erro
- Status code de erro apropriado (400, 401, 403, 404, 500)
- Código de erro estruturado
- Mensagem de erro legível para humanos
- Detalhes adicionais quando aplicável

### 5.4 Endpoints Específicos de Administradores

#### Criação de Administrador
- **Endpoint**: `POST /api/v1/admin/users`
- **Permissão**: Apenas administradores com nível "admin"
- **Payload**: nome, email, senha, nível de permissão
- **Validações**: email único, senha forte, nível válido

#### Alteração de Senha
- **Endpoint**: `PUT /api/v1/admin/users/{id}/password`
- **Permissão**: Admin próprio ou admin superior
- **Payload**: senha atual, nova senha, confirmação
- **Validações**: senha atual correta, nova senha forte

#### Listagem de Administradores
- **Endpoint**: `GET /api/v1/admin/users`
- **Permissão**: Apenas administradores
- **Filtros**: status (ativo/inativo), nível de permissão
- **Paginação**: suporte a offset/limit

#### Atualização de Perfil
- **Endpoint**: `PUT /api/v1/admin/users/{id}`
- **Permissão**: Admin próprio ou admin superior
- **Campos**: nome, email, nível de permissão, status
- **Restrições**: não pode alterar próprio nível de permissão
- Paginação baseada em offset/limit
- Filtros por query parameters
- Ordenação configurável
- Busca por texto em campos relevantes

## 7. Autenticação e Autorização

### 7.1 Estratégia de Autenticação
- **JWT (JSON Web Tokens)** para sessões stateless
- **Refresh tokens** para renovação automática
- **Bcrypt** para hash de senhas
- **Bearer token** no header Authorization

### 7.2 Níveis de Permissão
- **Admin**: Acesso completo ao sistema
- **Moderator**: Acesso limitado (sem gerenciar outros admins)
- **Public**: Acesso apenas às APIs públicas (sem autenticação)

### 7.3 Middleware de Segurança
- Validação de token em todas as rotas protegidas
- Verificação de nível de permissão por endpoint
- Rate limiting para prevenção de ataques
- CORS configurado para domínios específicos

### 7.4 Gerenciamento de Usuários Administrativos

#### Políticas de Senha
- **Complexidade mínima**: 8 caracteres, maiúscula, minúscula, número
- **Histórico de senhas**: não permitir reutilização das últimas 5 senhas
- **Expiração**: senhas expiram a cada 90 dias (configurável)
- **Tentativas de login**: bloqueio após 5 tentativas falhadas

#### Hierarquia de Permissões
- **Super Admin**: acesso total, pode criar outros admins
- **Admin**: gerencia torneios, jogadores e pontuações
- **Moderator**: apenas visualiza e adiciona pontuações
- **Read-only**: apenas consulta dados (futuro)

#### Auditoria de Usuários
- **Log de logins**: timestamp, IP, user agent
- **Histórico de alterações**: quem alterou o quê e quando
- **Sessões ativas**: controle de sessões simultâneas
- **Alertas de segurança**: login de nova localização/dispositivo

## 8. Frontend Architecture

### 8.1 Estrutura de Componentes
- **Layout Components**: Header, Sidebar, Footer
- **Page Components**: Dashboard, Players, Scores, Ranking
- **Form Components**: PlayerForm, ScoreForm, LoginForm
- **Common Components**: DataTable, Modal, Loading, ErrorBoundary

### 8.2 Estado Global
- **Zustand** para gerenciamento de estado simples e performático
- **Stores separados** por domínio (players, scores, auth)
- **Estado local** com React hooks para componentes específicos
- **Cache inteligente** para dados de API

### 8.3 Roteamento
- **React Router v6** para navegação SPA
- **Rotas protegidas** com verificação de autenticação
- **Lazy loading** para otimização de bundle
- **Breadcrumb** automático baseado na rota

### 8.4 Comunicação com API
- **Axios** como cliente HTTP principal
- **Interceptors** para tratamento automático de auth e erros
- **TypeScript** para type safety completo
- **React Query** opcional para cache avançado

### 8.5 Gestão de Usuários no Frontend

#### Páginas de Administração de Usuários
- **Lista de Usuários**: tabela com filtros e paginação
- **Criar Usuário**: formulário com validação em tempo real
- **Editar Perfil**: form para atualização de dados pessoais
- **Alterar Senha**: form específico com validações de segurança

#### Componentes Específicos
- **UserForm**: formulário reutilizável para criar/editar
- **PasswordForm**: componente especializado para alteração de senha
- **UserTable**: tabela com ações inline (editar, desativar)
- **PermissionBadge**: componente visual para níveis de permissão

#### Validações de Frontend
- **Email único**: verificação em tempo real via API
- **Força da senha**: indicador visual de complexidade
- **Confirmação de senha**: validação de matching
- **Campos obrigatórios**: validação antes do submit

## 9. Configuração e Deploy

### 8.1 Containerização
- **Docker** para empacotamento de aplicações
- **Docker Compose** para orquestração local
- **Multi-stage builds** para otimização de imagens
- **Health checks** para monitoramento de containers

### 8.2 Variáveis de Ambiente
- **Backend**: DATABASE_URL, SECRET_KEY, CORS_ORIGINS
- **Frontend**: REACT_APP_API_URL, REACT_APP_ENV
- **Database**: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
- **Nginx**: SSL_CERT_PATH, DOMAIN_NAME

### 8.3 Estratégias de Deploy
- **Development**: Docker Compose local
- **Staging**: Docker Swarm ou Kubernetes
- **Production**: Cloud providers (AWS, GCP, Azure)
- **CI/CD**: GitHub Actions ou GitLab CI

## 9. Testes

### 9.1 Backend Testing
- **Unit Tests**: Pytest para lógica de negócio
- **Integration Tests**: Testes de API com TestClient
- **Database Tests**: Fixtures com SQLite in-memory
- **Coverage**: Mínimo 80% de cobertura de código

### 9.2 Frontend Testing
- **Unit Tests**: Jest + React Testing Library
- **Component Tests**: Testes de renderização e interação
- **E2E Tests**: Cypress para fluxos críticos
- **Visual Tests**: Storybook para componentes isolados

### 9.3 Estratégia de QA
- **Testes automatizados** em pipeline CI/CD
- **Code review** obrigatório antes de merge
- **Ambiente de staging** para testes manuais
- **Monitoramento de errors** em produção

## 10. Monitoramento e Logs

### 10.1 Logging Strategy
- **Structured logging** em formato JSON
- **Log levels** apropriados (DEBUG, INFO, WARNING, ERROR)
- **Correlation IDs** para rastreamento de requests
- **Audit trail** para todas as operações críticas

### 10.2 Métricas de Performance
- **Response time** de APIs
- **Database query performance**
- **Frontend bundle size** e loading times
- **Error rates** e uptime

### 10.3 Health Checks
- **Liveness probes** para verificar se aplicação está rodando
- **Readiness probes** para verificar se está pronta para receber tráfego
- **Database connectivity** checks
- **External dependencies** monitoring

## 11. Segurança

### 11.1 Configurações de Segurança
- **HTTPS obrigatório** em produção
- **CORS** configurado para domínios específicos
- **Rate limiting** para prevenção de ataques
- **Input validation** em todas as entradas
- **SQL injection** prevenção via ORM

### 11.2 Proteção de Dados
- **Password hashing** com bcrypt
- **Sensitive data masking** em logs
- **Database encryption** at rest
- **Backup encryption** para dados sensíveis

### 11.3 Compliance
- **LGPD compliance** para dados pessoais
- **Audit logs** para rastreabilidade
- **Data retention policies**
- **User consent** management

## 12. Performance e Otimizações

### 12.1 Database Optimization
- **Índices otimizados** para queries de ranking
- **Connection pooling** para eficiência
- **Query optimization** com EXPLAIN ANALYZE
- **Database caching** com Redis (futuro)

### 12.2 Frontend Performance
- **Code splitting** por rotas
- **Lazy loading** de componentes
- **Image optimization** e CDN
- **Bundle analysis** e tree shaking

### 12.3 Caching Strategy
- **Browser caching** para assets estáticos
- **API response caching** quando apropriado
- **Database query caching** com Redis
- **CDN** para distribuição global

## 13. Backup e Recovery

### 13.1 Estratégia de Backup
- **Automated daily backups** do PostgreSQL
- **Point-in-time recovery** capability
- **Cross-region backup** replication
- **Backup testing** mensal

### 13.2 Disaster Recovery
- **RTO (Recovery Time Objective)**: 4 horas
- **RPO (Recovery Point Objective)**: 24 horas
- **Documented recovery procedures**
- **Regular disaster recovery drills**

## 14. Escalabilidade

### 14.1 Escalabilidade Horizontal
- **Stateless application** design
- **Load balancer** para distribuição de tráfego
- **Database read replicas** para scaling de leitura
- **Microservices** preparação para futuro

### 14.2 Monitoramento de Crescimento
- **Performance metrics** tracking
- **Capacity planning** baseado em métricas
- **Auto-scaling** rules para cloud deployment
- **Cost optimization** strategies

## 15. Principais Vantagens do SQLModel

### 15.1 Benefícios sobre SQLAlchemy puro
- **Menos Código Duplicado**: Define modelos, schemas de request/response e validação em um só lugar
- **Type Safety**: TypeScript-like experience no Python com mypy support
- **Auto-complete Melhor**: IDEs conseguem inferir tipos automaticamente  
- **Pydantic v2 Integration**: Validação automática e serialização otimizada
- **Compatibilidade**: 100% compatível com SQLAlchemy 2.0 por baixo dos panos
- **FastAPI Native**: Criado pelo mesmo autor do FastAPI para máxima integração

### 15.2 Comparação Prática

**SQLAlchemy Tradicional:**
- Precisaria de 3 arquivos separados: models, schemas, crud
- Total: ~150 linhas de código para funcionalidade básica

**SQLModel:**
- Tudo integrado com ~80 linhas
- Menos manutenção, menos bugs, mais produtividade

### 15.3 Requirements.txt Recomendado

#### Core Dependencies
- fastapi==0.104.1
- sqlmodel==0.0.14
- alembic==1.12.1
- python-jose[cryptography]==3.3.0
- passlib[bcrypt]==1.7.4
- python-multipart==0.0.6

#### Database
- psycopg2-binary==2.9.9
- asyncpg==0.29.0

#### Development
- pytest==7.4.3
- pytest-asyncio==0.21.1
- black==23.11.0
- flake8==6.1.0
- mypy==1.7.1

---

## Conclusão

Este documento define a arquitetura técnica completa para o Sistema de Ranking de Torneio Online, utilizando **FastAPI + SQLModel** no backend e **React + TypeScript** no frontend. A escolha do SQLModel oferece uma experiência de desenvolvimento superior, combinando a robustez do SQLAlchemy 2.0 com a simplicidade e type safety do Pydantic v2.

A arquitetura proposta garante escalabilidade, segurança e manutenibilidade, atendendo todos os requisitos especificados no PRD com uma stack tecnológica moderna e otimizada.

### Pontos-chave da arquitetura:
- **SQLModel** para redução significativa de código duplicado
- **Type Safety** completo entre frontend e backend
- **Escalabilidade horizontal** preparada para crescimento
- **Segurança robusta** com JWT e validação em múltiplas camadas
- **Testes automatizados** para garantir qualidade
- **Deploy containerizado** para facilitar operações

A implementação seguirá as melhores práticas de desenvolvimento, com testes automatizados, documentação abrangente e estratégias de deploy robustas.

---

**Próximos Passos**:
1. Setup do ambiente de desenvolvimento com SQLModel
2. Configuração do banco de dados PostgreSQL
3. Implementação do MVP (Fase 1) com modelos SQLModel
4. Testes automatizados backend/frontend
5. Deploy em ambiente de produção com Docker