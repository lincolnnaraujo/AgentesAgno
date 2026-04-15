# [FEAT] - Consulta de boleto por número para operador interno

## Contexto / Valor de Negócio
- Operadores internos atendem clientes por telefone que solicitam
  informações sobre seus boletos
- Hoje o processo é manual e moroso, impactando negativamente
  o tempo de atendimento
- A funcionalidade centraliza as informações do boleto em uma
  única tela, eliminando consultas manuais durante o atendimento
- Stakeholders: equipe de atendimento ao cliente, gestão operacional

## Descrição
**Estado atual:** o operador não possui interface dedicada para
consulta de boletos, realizando o processo de forma manual.

**Estado desejado:** o operador acessa um componente Vue embutido
no portal corporativo, informa o número do boleto e visualiza
instantaneamente: data de vencimento, status, data de pagamento
e valor.

**Fluxo ponta a ponta:**
```
[Operador] → [Vue Component (Portal Corporativo)]
           → GET /api/boletos/{numero}
           → [Spring Boot API]
           → [BoletoRepository (Port)]
           → [SQL Server - base existente]
```

## Decisões de Arquitetura

**Ports & Adapters identificados:**
- **Port (entrada):** `BoletoController` — expõe `GET /api/boletos/{numero}`
- **Port (saída):** `BoletoRepository` — interface que abstrai o acesso ao SQL Server
- **Adapter (saída):** `BoletoRepositoryImpl` — implementação JPA/JDBC para SQL Server
- **Domínio:** `BoletoService` — orquestra a consulta e aplica regras de negócio

**Bounded Context:** Consulta de Boletos (read-only)

**Estratégia de comunicação:** Síncrona — REST HTTP

**Tratamento de erros:**
- Boleto não encontrado → `HTTP 404` com mensagem `"Boleto não encontrado para o número informado"`
- Erro interno → `HTTP 500` com mensagem genérica (sem expor detalhes internos)
- Timeout configurado em **5 segundos** no RestTemplate/JdbcTemplate

**Observação sobre integração Vue:**
> ⚠️ A estratégia de embed no portal corporativo (Web Component / iframe / Module Federation)
> deve ser definida com o time de infraestrutura antes do desenvolvimento do frontend.

## Critérios de Aceitação (Gherkin)

### Cenário 1: Consulta com sucesso
- **Dado** que o operador está autenticado no portal corporativo
- **Quando** informa um número de boleto válido e existente na base
- **Então** o sistema retorna: data de vencimento, status, data de pagamento e valor do boleto
- **E** o tempo de resposta é inferior a 5 segundos

### Cenário 2: Boleto não encontrado
- **Dado** que o operador está autenticado no portal corporativo
- **Quando** informa um número de boleto que não existe na base
- **Então** o sistema exibe a mensagem: "Boleto não encontrado para o número informado"
- **E** o campo de busca permanece disponível para nova consulta

### Cenário 3: Campo de busca vazio ou inválido
- **Dado** que o operador está na tela de consulta
- **Quando** tenta submeter a consulta sem informar o número do boleto
- **Então** o sistema exibe validação no frontend antes de realizar a chamada à API
- **E** nenhuma requisição é enviada ao backend

### Cenário 4: Indisponibilidade da base de dados
- **Dado** que o banco de dados está indisponível
- **Quando** o operador realiza uma consulta
- **Então** o sistema retorna HTTP 500 com mensagem genérica ao frontend
- **E** o erro é registrado nos logs com stack trace completo

## Definition of Ready (DoR)
- [ ] História clara e compreensível por todo o time
- [ ] Critérios de aceitação definidos e testáveis
- [ ] Esquema da tabela de boletos no SQL Server compartilhado com o time de desenvolvimento
- [ ] Estratégia de integração do Vue no portal corporativo definida com time de infraestrutura ⚠️
- [ ] Volume de carga estimado (req/dia) levantado ⚠️
- [ ] Abordagem técnica (Hexagonal) revisada com Tech Lead
- [ ] Timeout de 5s validado com DBA (performance da query)
- [ ] Story points estimados pelo time
- [ ] Acesso ao ambiente de DEV com SQL Server disponível

## Definition of Done (DoD)

### Backend (Spring Boot)
- [ ] Endpoint `GET /api/boletos/{numero}` implementado
- [ ] Arquitetura Hexagonal aplicada (Controller → Service → Repository interface → Impl)
- [ ] Retorno correto dos campos: vencimento, status, data pagamento, valor
- [ ] HTTP 404 para boleto não encontrado com mensagem clara
- [ ] HTTP 500 para erros internos com log estruturado
- [ ] Timeout de 5s configurado na camada de dados
- [ ] Testes unitários com JUnit 5 + Mockito (cobertura mínima 80%)
- [ ] Build verde no GitHub Actions

### Frontend (Vue)
- [ ] Componente de busca por número do boleto implementado
- [ ] Exibição dos 4 campos: vencimento, status, data pagamento, valor
- [ ] Validação frontend: campo obrigatório antes de submeter
- [ ] Mensagem de erro clara quando boleto não encontrado
- [ ] Estado de loading durante a requisição
- [ ] Integração com portal corporativo validada

### Qualidade Geral
- [ ] Code review aprovado por pelo menos 1 par
- [ ] Sem issues críticas/altas no linter
- [ ] Logs implementados (entrada da requisição + erro)
- [ ] Deploy em ambiente de DEV realizado
- [ ] Testado e aprovado pelo time de QA
- [ ] Aceite do Product Owner obtido

## Cenários de Teste

### Testes Unitários (JUnit 5 + Mockito)
- [ ] `BoletoService` retorna DTO correto quando repositório encontra boleto
- [ ] `BoletoService` lança `BoletoNotFoundException` quando repositório retorna vazio
- [ ] `BoletoController` retorna HTTP 200 com body correto
- [ ] `BoletoController` retorna HTTP 404 com mensagem para `BoletoNotFoundException`
- [ ] `BoletoController` retorna HTTP 500 para exceção genérica

### Testes de Erro / Edge Cases
- [ ] Número de boleto com formato inválido
- [ ] Boleto existente mas com data de pagamento nula (boleto em aberto)
- [ ] Timeout simulado na camada de repositório

### Testes de Integração (repositório dedicado)
- [ ] Consulta real ao SQL Server via Testcontainers
- [ ] Validação do mapeamento ORM/JDBC dos campos

## Requisitos Não-Funcionais

| Aspecto         | Requisito                                          |
|-----------------|----------------------------------------------------|
| Performance     | Timeout ≤ 5s; meta real < 500ms por busca por PK  |
| Segurança       | Autenticação delegada ao portal corporativo        |
| Escalabilidade  | ⚠️ Pendente — volume de req/dia não levantado     |
| Disponibilidade | 24/7                                               |
| Observabilidade | Log estruturado por requisição + log de erros      |

## Dependências
- [ ] Acesso ao schema da tabela de boletos no SQL Server
- [ ] Definição da estratégia de embed Vue no portal corporativo ⚠️
- [ ] Alinhamento com DBA sobre índice na PK e performance esperada

## Notas Adicionais
- **Limitação conhecida:** sem volume de carga definido, a necessidade de cache (Redis)
  não foi avaliada. Se volume > 100k req/dia, revisar arquitetura com camada de cache
  antes de iniciar desenvolvimento.
- **Débito técnico:** avaliar cache após levantar métricas de volume em produção.
- **Melhoria futura:** busca por CPF/CNPJ do cliente (múltiplos boletos por consulta).

---

## ⚠️ Perguntas Pendentes para Refinamento

| # | Pendência | Impacto |
|---|---|---|
| 1 | Volume de carga (req/dia ou registros na base) | Define necessidade de cache Redis |
| 2 | Estratégia de integração Vue no portal (Web Component / iframe / Module Federation) | Bloqueia início do frontend |
| 3 | Métrica de sucesso mensurável (tempo de atendimento, volume de chamados) | Necessário para DoD do PO |
