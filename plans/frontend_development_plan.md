# Plano de Desenvolvimento Frontend
## Sistema de Ranking de Torneio Online

---

**Agentes Responsáveis**: Frontend Developer + UX/UI Designer + Tech Lead + Product Manager  
**Stack**: React 18+ + TypeScript + Material-UI + Vite  
**Versão**: 1.0  
**Data**: Agosto 2025  

---

## 🎯 Visão Geral do Frontend

O frontend será uma aplicação React moderna com TypeScript, utilizando Material-UI para componentes, Vite como build tool e integração completa com as APIs backend. O sistema deve ser responsivo, acessível (WCAG 2.1 AA) e suportar tanto o painel administrativo quanto a visualização pública do ranking.

### Objetivos Principais
- Interface responsiva para desktop, tablet e mobile
- Painel administrativo completo para gerenciar torneio
- Visualização pública do ranking em tempo real
- Performance < 3 segundos conforme RNF001
- Acessibilidade WCAG 2.1 AA conforme RNF005
- Integração com identidade visual do torneio

---

## 📋 Fases de Desenvolvimento

### Fase 1: Setup e Arquitetura Base (Sprint 1-2)

#### 1.1 Configuração do Projeto
- [ ] **🏗️ Tech Lead**: Setup do Projeto React + TypeScript
  - Criar projeto com Vite + TypeScript template
  - Configurar ESLint + Prettier para qualidade de código
  - Setup de environment variables para diferentes ambientes
  
- [ ] **🎨 Frontend Developer**: Configuração do Build Tool (Vite)
  - Configurar Vite para desenvolvimento e produção
  - Setup de hot reload e fast refresh
  - Configurar build otimizado com code splitting

#### 1.2 Estrutura Base do Projeto
```
frontend/
├── public/
│   ├── index.html
│   └── assets/              # Imagens, ícones estáticos
├── src/
│   ├── components/          # Componentes reutilizáveis
│   │   ├── common/          # Componentes genéricos
│   │   ├── forms/           # Componentes de formulário
│   │   └── layout/          # Layout components
│   ├── pages/               # Páginas da aplicação
│   │   ├── admin/           # Páginas administrativas
│   │   └── public/          # Páginas públicas
│   ├── services/            # Integração com APIs
│   ├── store/               # Estado global (Zustand)
│   ├── types/               # TypeScript interfaces
│   ├── utils/               # Funções utilitárias
│   ├── hooks/               # Custom React hooks
│   └── styles/              # Tema e estilos globais
├── package.json
└── vite.config.ts
```

#### 1.3 Instalação de Dependencies
- [ ] **🎨 Frontend Developer**: Core Dependencies
  ```json
  {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.0.0",
    "@mui/material": "^5.14.0",
    "@mui/icons-material": "^5.14.0",
    "@emotion/react": "^11.11.0",
    "@emotion/styled": "^11.11.0"
  }
  ```

- [ ] **🎨 Frontend Developer**: Routing e State Management
  ```json
  {
    "react-router-dom": "^6.15.0",
    "zustand": "^4.4.0",
    "axios": "^1.5.0"
  }
  ```

- [ ] **🎨 Frontend Developer**: Forms e Validation
  ```json
  {
    "react-hook-form": "^7.45.0",
    "zod": "^3.22.0",
    "@hookform/resolvers": "^3.3.0"
  }
  ```

- [ ] **🧪 QA Engineer + 🎨 Frontend Developer**: Development e Testing
  ```json
  {
    "@vitejs/plugin-react": "^4.0.0",
    "eslint": "^8.47.0",
    "prettier": "^3.0.0",
    "@testing-library/react": "^13.4.0",
    "@testing-library/jest-dom": "^6.1.0",
    "vitest": "^0.34.0"
  }
  ```

#### 1.4 Configurações Base
- [ ] **🏗️ Tech Lead**: TypeScript Configuration
  - tsconfig.json com configurações strict
  - Path mapping para imports absolutos
  - Type checking rigoroso habilitado

- [ ] **🏗️ Tech Lead + 🎨 Frontend Developer**: ESLint + Prettier Setup
  - Regras de linting para React + TypeScript
  - Formatação automática consistente
  - Pre-commit hooks para qualidade

---

### Fase 2: Design System e Tema (Sprint 2-3)

#### 2.1 Configuração do Material-UI Theme
- [ ] **🎯 UX/UI Designer + 🎨 Frontend Developer**: Tema Customizado
  ```typescript
  // theme/index.ts
  const theme = createTheme({
    palette: {
      primary: {
        main: '#1976d2', // Azul principal
        light: '#42a5f5',
        dark: '#1565c0',
      },
      secondary: {
        main: '#dc004e', // Vermelho secundário
      },
      background: {
        default: '#f5f5f5',
        paper: '#ffffff',
      },
    },
    typography: {
      fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
      h1: {
        fontSize: '2.5rem',
        fontWeight: 600,
      },
      // ... outras configurações
    },
  });
  ```

#### 2.2 Sistema de Design Components
- [ ] **🎯 UX/UI Designer + 🎨 Frontend Developer**: Layout Components
  - Header com navegação e logo do torneio
  - Sidebar para painel administrativo  
  - Footer com informações básicas
  - Container responsivo principal

- [ ] **🎨 Frontend Developer**: Common Components
  - Loading spinner e skeletons
  - Error boundary e error states
  - Success/Error toast notifications
  - Confirmation dialogs
  - Empty states informativos

#### 2.3 Identidade Visual do Torneio
- [ ] **🎯 UX/UI Designer**: Integração de Branding
  - Logo oficial em todas as páginas (DES001)
  - Paleta de cores consistente (DES002)
  - Tipografia legível e profissional (DES003)
  - Layout moderno e clean (DES004)

---

### Fase 3: Roteamento e Estrutura de Navegação (Sprint 3)

#### 3.1 Configuração do React Router
- [ ] **🎨 Frontend Developer**: Setup de Rotas
  ```typescript
  // App.tsx
  const router = createBrowserRouter([
    {
      path: "/",
      element: <PublicLayout />,
      children: [
        { index: true, element: <PublicRanking /> },
        { path: "player/:id", element: <PlayerDetails /> },
      ],
    },
    {
      path: "/admin",
      element: <AdminLayout />,
      children: [
        { index: true, element: <Dashboard /> },
        { path: "players", element: <PlayersManagement /> },
        { path: "scores", element: <ScoresManagement /> },
        { path: "settings", element: <TournamentSettings /> },
      ],
    },
  ]);
  ```

#### 3.2 Layout Components
- [ ] **🎯 UX/UI Designer + 🎨 Frontend Developer**: PublicLayout
  - Header com logo e navegação pública
  - Container responsivo para conteúdo
  - Footer com informações do torneio

- [ ] **🎯 UX/UI Designer + 🎨 Frontend Developer**: AdminLayout  
  - Header com navegação administrativa
  - Sidebar com menu de administração
  - Breadcrumb para orientação (DES006)
  - Logout e perfil do usuário

#### 3.3 Proteção de Rotas
- [ ] **🎨 Frontend Developer**: ProtectedRoute Component
  - Verificação de autenticação JWT
  - Redirecionamento para login se não autenticado
  - Loading state durante verificação

---

### Fase 4: Autenticação e Estado Global (Sprint 3-4)

#### 4.1 Setup do Zustand (State Management)
- [ ] **🎨 Frontend Developer**: Auth Store
  ```typescript
  // store/authStore.ts
  interface AuthState {
    user: Admin | null;
    token: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (email: string, password: string) => Promise<void>;
    logout: () => void;
    refreshToken: () => Promise<void>;
  }
  ```

- [ ] **🎨 Frontend Developer**: App Store (Global State)
  ```typescript
  // store/appStore.ts  
  interface AppState {
    tournament: Tournament | null;
    isLoading: boolean;
    error: string | null;
    setTournament: (tournament: Tournament) => void;
    clearError: () => void;
  }
  ```

#### 4.2 Serviços de API
- [ ] **🎨 Frontend Developer**: API Client Setup
  ```typescript
  // services/apiClient.ts
  const apiClient = axios.create({
    baseURL: process.env.VITE_API_URL || 'http://localhost:8000/api/v1',
    timeout: 10000,
  });

  // Interceptors para auth e error handling
  apiClient.interceptors.request.use((config) => {
    const token = authStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });
  ```

- [ ] **🎨 Frontend Developer**: Auth Service
  ```typescript
  // services/authService.ts
  export const authService = {
    login: (credentials: LoginRequest) => 
      apiClient.post<LoginResponse>('/auth/login', credentials),
    
    refreshToken: () => 
      apiClient.post<RefreshResponse>('/auth/refresh'),
    
    logout: () => 
      apiClient.post('/auth/logout'),
  };
  ```

#### 4.3 Páginas de Autenticação
- [ ] **🎯 UX/UI Designer + 🎨 Frontend Developer**: Login Page
  - Formulário com email/senha e validação
  - Remember me checkbox
  - Loading state durante autenticação
  - Error handling com mensagens claras

---

### Fase 5: Painel Administrativo (Sprint 4-7)

#### 5.1 Dashboard Administrativo
- [ ] **📋 Product Manager + 🎯 UX/UI Designer + 🎨 Frontend Developer**: Dashboard Overview
  ```typescript
  // pages/admin/Dashboard.tsx
  - Cards com estatísticas principais:
    * Total de jogadores ativos
    * Total de pontuações registradas  
    * Última atualização do ranking
    * Jogador líder atual
  - Gráficos de atividade recente
  - Ações rápidas (adicionar jogador/pontuação)
  ```

#### 5.2 Gerenciamento de Jogadores
- [ ] **🎯 UX/UI Designer + 🎨 Frontend Developer**: Lista de Jogadores
  - DataTable com paginação e busca
  - Filtros: ativo/inativo, busca por nome
  - Colunas: avatar, nome, nickname, email, status, ações
  - Ações inline: editar, visualizar, desativar

- [ ] **🎨 Frontend Developer**: Formulário de Jogador
  ```typescript
  // components/forms/PlayerForm.tsx
  interface PlayerFormData {
    name: string;
    nickname: string;
    email?: string;
    avatar?: File;
    isActive: boolean;
  }
  
  // Validação com Zod + React Hook Form
  const playerSchema = z.object({
    name: z.string().min(2, "Nome deve ter pelo menos 2 caracteres"),
    nickname: z.string().min(2, "Nickname deve ter pelo menos 2 caracteres"),
    email: z.string().email().optional(),
    isActive: z.boolean(),
  });
  ```

- [ ] **🎯 UX/UI Designer + 🎨 Frontend Developer**: Importação CSV
  - Upload de arquivo com drag & drop
  - Preview dos dados antes da importação
  - Validação e feedback de erros
  - Progress indicator durante importação

#### 5.3 Gerenciamento de Pontuações
- [ ] **🎯 UX/UI Designer + 🎨 Frontend Developer**: Lista de Pontuações
  - DataTable com filtros por jogador, data, admin
  - Colunas: jogador, pontos, data, admin, observações, ações
  - Ordenação por data/pontos
  - Paginação para performance

- [ ] **🎨 Frontend Developer**: Formulário de Pontuação
  ```typescript
  // components/forms/ScoreForm.tsx
  interface ScoreFormData {
    playerId: number;
    points: number;
    notes?: string;
  }

  // Autocomplete para seleção de jogador
  // Validação de pontos (número positivo)
  // Campo opcional para observações
  ```

- [ ] **🎯 UX/UI Designer + 🎨 Frontend Developer**: Confirmação de Ações Críticas
  - Dialog de confirmação para deletar pontuações
  - Undo action para operações recentes
  - Feedback visual de sucesso/erro

#### 5.4 Configurações do Torneio
- [ ] **🎯 UX/UI Designer + 🎨 Frontend Developer**: Formulário de Configurações
  - Nome e descrição do torneio
  - Datas de início e fim
  - Upload de logo oficial
  - Critérios de ordenação do ranking
  - Preview das alterações

---

### Fase 6: Visualização Pública (Sprint 6-7)

#### 6.1 Ranking Público Principal
- [ ] **🎯 UX/UI Designer + 🎨 Frontend Developer**: Tabela de Ranking
  ```typescript
  // pages/public/PublicRanking.tsx
  interface RankingEntry {
    position: number;
    player: {
      id: number;
      name: string;
      nickname: string;
      avatar?: string;
    };
    totalPoints: number;
    lastUpdate: string;
  }

  // Componentes:
  - Header com nome e logo do torneio
  - Tabela responsiva com ranking
  - Indicador de última atualização
  - Paginação se necessário (>50 jogadores)
  ```

- [ ] **🎯 UX/UI Designer + 🎨 Frontend Developer**: Funcionalidades de Busca
  - Campo de busca proeminente no topo
  - Busca em tempo real por nome/nickname
  - Highlight nos resultados encontrados
  - Estado vazio quando não há resultados

#### 6.2 Detalhes do Jogador
- [ ] **🎯 UX/UI Designer + 🎨 Frontend Developer**: Página de Detalhes
  - Informações públicas do jogador
  - Posição atual no ranking
  - Histórico de pontuações (gráfico)
  - Estatísticas pessoais

#### 6.3 Estatísticas Públicas  
- [ ] **📋 Product Manager + 🎯 UX/UI Designer + 🎨 Frontend Developer**: Página de Estatísticas
  - Total de participantes
  - Pontuação média do torneio
  - Distribuição de pontuações (gráfico)
  - Top 3 jogadores em destaque

---

### Fase 7: Componentes Avançados e UX (Sprint 7-8)

#### 7.1 Componentes de Feedback
- [ ] **🎯 UX/UI Designer + 🎨 Frontend Developer**: Toast Notifications
  ```typescript
  // components/common/Toast.tsx
  - Success: "Jogador criado com sucesso!"
  - Error: "Erro ao salvar dados. Tente novamente."
  - Warning: "Alguns campos precisam ser revisados"
  - Info: "Ranking atualizado automaticamente"
  ```

- [ ] **🎯 UX/UI Designer + 🎨 Frontend Developer**: Loading States
  - Skeleton loading para tabelas
  - Spinner para ações rápidas
  - Progress bar para uploads
  - Shimmer effect para cards

#### 7.2 Estados de Erro
- [ ] **🎨 Frontend Developer**: Error Boundary
  - Captura de erros React não tratados
  - Fallback UI amigável
  - Opção para reportar erro
  - Botão para retry/reload

- [ ] **🎯 UX/UI Designer + 🎨 Frontend Developer**: Network Error Handling
  - Offline indicator
  - Retry automático com backoff
  - Fallback para dados em cache
  - Mensagens de erro contextuais

#### 7.3 Acessibilidade (WCAG 2.1 AA)
- [ ] **🎯 UX/UI Designer + 🎨 Frontend Developer**: Implementações A11y
  - Contraste adequado em todos os elementos
  - Labels apropriados em formulários
  - Keyboard navigation completa
  - Screen reader support
  - Focus management em modals
  - ARIA labels onde necessário

---

### Fase 8: Performance e Otimizações (Sprint 8-9)

#### 8.1 Code Splitting e Lazy Loading
- [ ] **🏗️ Tech Lead + 🎨 Frontend Developer**: Route-based Code Splitting
  ```typescript
  // Lazy loading de páginas
  const Dashboard = lazy(() => import('./pages/admin/Dashboard'));
  const PublicRanking = lazy(() => import('./pages/public/PublicRanking'));
  
  // Suspense wrapper com loading
  <Suspense fallback={<LoadingSkeleton />}>
    <Routes>
      <Route path="/admin" element={<Dashboard />} />
    </Routes>
  </Suspense>
  ```

- [ ] **🎨 Frontend Developer**: Component Lazy Loading
  - Lazy load de componentes pesados
  - Dynamic imports para bibliotecas grandes
  - Intersection Observer para componentes fora da viewport

#### 8.2 Otimizações de Bundle
- [ ] **🏗️ Tech Lead + 🚀 DevOps Engineer**: Vite Build Optimizations
  - Bundle analysis e tree shaking
  - Asset optimization (imagens, fonts)
  - Compression gzip/brotli
  - CDN-ready build output

#### 8.3 Performance Web Vitals
- [ ] **🏗️ Tech Lead + 🧪 QA Engineer**: Core Web Vitals
  - LCP (Largest Contentful Paint) < 2.5s
  - FID (First Input Delay) < 100ms  
  - CLS (Cumulative Layout Shift) < 0.1
  - Lighthouse score > 90

---

### Fase 9: Testes e Qualidade (Sprint 9-10)

#### 9.1 Setup de Testes
- [ ] **🧪 QA Engineer + 🎨 Frontend Developer**: Vitest + Testing Library
  ```typescript
  // vitest.config.ts
  export default defineConfig({
    test: {
      environment: 'jsdom',
      setupFiles: ['./src/test/setup.ts'],
      coverage: {
        reporter: ['text', 'html', 'lcov'],
        threshold: {
          global: {
            branches: 80,
            functions: 80,
            lines: 80,
            statements: 80,
          },
        },
      },
    },
  });
  ```

#### 9.2 Testes Unitários
- [ ] **🧪 QA Engineer + 🎨 Frontend Developer**: Componentes
  ```typescript
  // __tests__/PlayerForm.test.tsx
  describe('PlayerForm', () => {
    it('validates required fields', async () => {
      render(<PlayerForm />);
      
      const submitButton = screen.getByRole('button', { name: /salvar/i });
      fireEvent.click(submitButton);
      
      expect(await screen.findByText(/nome é obrigatório/i)).toBeInTheDocument();
    });
  });
  ```

- [ ] **🧪 QA Engineer + 🎨 Frontend Developer**: Hooks Customizados
  - Testes de custom hooks com renderHook
  - Mock de APIs e side effects
  - Testes de estado e lifecycle

#### 9.3 Testes de Integração
- [ ] **🧪 QA Engineer**: User Flows
  - Login → Dashboard → Criar Jogador
  - Busca público → Detalhes do jogador
  - Admin → Adicionar pontuação → Ver ranking atualizado

#### 9.4 E2E com Cypress (Coordenado com QA)
- [ ] **🧪 QA Engineer**: Testes Críticos
  - Fluxo completo administrativo
  - Visualização pública responsiva
  - Performance em diferentes devices

---

### Fase 10: Responsividade e PWA (Sprint 10)

#### 10.1 Responsive Design
- [ ] **🎯 UX/UI Designer + 🎨 Frontend Developer**: Breakpoints Material-UI
  ```typescript
  // styles/theme.ts
  const theme = createTheme({
    breakpoints: {
      values: {
        xs: 0,      // Mobile
        sm: 600,    // Tablet
        md: 900,    // Desktop pequeno
        lg: 1200,   // Desktop
        xl: 1536,   // Desktop grande
      },
    },
  });
  ```

- [ ] **🎯 UX/UI Designer + 🎨 Frontend Developer**: Components Responsivos
  - DataTables que viram cards em mobile
  - Sidebar que vira drawer em mobile
  - Navigation adaptativa por tamanho de tela

#### 10.2 PWA Features (Opcional)
- [ ] **🚀 DevOps Engineer + 🎨 Frontend Developer**: Service Worker
  - Cache de assets estáticos
  - Offline fallback pages
  - Background sync para actions

---

## 📊 Critérios de Aceitação por Fase

### Fase 1 ✅ Setup
- [ ] Projeto React + TypeScript rodando com Vite
- [ ] ESLint + Prettier configurados
- [ ] Estrutura de pastas implementada
- [ ] Dependencies instaladas e funcionais

### Fase 2 ✅ Design System
- [ ] Tema Material-UI customizado
- [ ] Logo do torneio integrado em todas as páginas
- [ ] Componentes base implementados
- [ ] Paleta de cores aplicada

### Fase 3 ✅ Navegação
- [ ] React Router configurado
- [ ] Layouts público e admin funcionais
- [ ] Breadcrumb navegacional implementado
- [ ] Rotas protegidas funcionando

### Fase 4 ✅ Auth & Estado
- [ ] Login JWT funcional
- [ ] Zustand stores configurados
- [ ] API client com interceptors
- [ ] Persistência de sessão

### Fase 5 ✅ Painel Admin
- [ ] Dashboard com estatísticas
- [ ] CRUD completo de jogadores
- [ ] CRUD completo de pontuações
- [ ] Importação CSV implementada
- [ ] Configurações de torneio

### Fase 6 ✅ Público
- [ ] Ranking público responsivo
- [ ] Busca de jogadores funcional
- [ ] Detalhes de jogador
- [ ] Estatísticas públicas

### Fases 7-10 ✅ Qualidade
- [ ] Testes > 80% cobertura
- [ ] Performance < 3s (RNF001)
- [ ] Acessibilidade WCAG 2.1 AA
- [ ] Responsividade completa

---

## 🛠️ Stack Técnica Detalhada

### Core Frontend
```json
{
  "react": "^18.2.0",
  "typescript": "^5.0.0",
  "@mui/material": "^5.14.0",
  "@mui/icons-material": "^5.14.0",
  "vite": "^4.4.0"
}
```

### State Management & HTTP
```json
{
  "zustand": "^4.4.0",
  "axios": "^1.5.0",
  "react-router-dom": "^6.15.0"
}
```

### Forms & Validation
```json
{
  "react-hook-form": "^7.45.0",
  "zod": "^3.22.0",
  "@hookform/resolvers": "^3.3.0"
}
```

### Development & Testing
```json
{
  "vitest": "^0.34.0",
  "@testing-library/react": "^13.4.0",
  "eslint": "^8.47.0",
  "prettier": "^3.0.0"
}
```

---

## 📋 Checklist de Entrega Final

### Interface Administrativa
- [ ] Login seguro com JWT
- [ ] Dashboard com métricas do torneio
- [ ] CRUD completo de jogadores com upload de avatar
- [ ] CRUD completo de pontuações com validações
- [ ] Importação CSV com preview e validação
- [ ] Configurações de torneio com upload de logo

### Interface Pública
- [ ] Ranking em tempo real com paginação
- [ ] Busca rápida por jogadores
- [ ] Detalhes de jogador com histórico
- [ ] Estatísticas do torneio
- [ ] Indicadores de última atualização

### Qualidade & Performance
- [ ] Responsivo em todos os dispositivos
- [ ] Acessibilidade WCAG 2.1 AA completa
- [ ] Performance < 3 segundos
- [ ] Testes automatizados > 80% cobertura
- [ ] Code review aprovado

### UX & Design
- [ ] Identidade visual do torneio integrada
- [ ] Loading states em todas as operações
- [ ] Error handling amigável
- [ ] Feedback visual para ações do usuário
- [ ] Navegação intuitiva e breadcrumbs

---

## 🎯 Próximos Passos

1. **Review com UX/UI Designer**: Validar designs e protótipos
2. **Review com Tech Lead**: Aprovar arquitetura frontend e padrões
3. **Kickoff com Frontend Developer**: Iniciar implementação seguindo este plano  
4. **Sync com Backend Developer**: Alinhar contratos de API e integração
5. **Coordenação com QA Engineer**: Preparar estratégia de testes desde o início

---

*Este plano foi elaborado pelos agentes Frontend Developer, UX/UI Designer, Tech Lead e Product Manager, baseado na documentação completa do projeto Sistema de Ranking de Torneio Online.*