// Constraints e índices para o GraphRAG do Kothar
// Execute após criar o container Neo4j

// =============================================================
// Constraints — Unicidade de nós
// =============================================================

// Arquivo de código
CREATE CONSTRAINT file_path_unique IF NOT EXISTS
FOR (f:File) REQUIRE f.path IS UNIQUE;

// Rota de API
CREATE CONSTRAINT route_path_unique IF NOT EXISTS
FOR (r:Route) REQUIRE r.path IS UNIQUE;

// Tabela de banco
CREATE CONSTRAINT table_name_unique IF NOT EXISTS
FOR (t:Table) REQUIRE t.name IS UNIQUE;

// Componente UI
CREATE CONSTRAINT component_name_unique IF NOT EXISTS
FOR (c:Component) REQUIRE c.name IS UNIQUE;

// Skill
CREATE CONSTRAINT skill_id_unique IF NOT EXISTS
FOR (s:Skill) REQUIRE s.id IS UNIQUE;

// Session
CREATE CONSTRAINT session_id_unique IF NOT EXISTS
FOR (sess:Session) REQUIRE sess.id IS UNIQUE;

// =============================================================
// Índices — Performance de busca
// =============================================================

CREATE INDEX file_type_index IF NOT EXISTS
FOR (f:File) ON (f.type);

CREATE INDEX file_modified_index IF NOT EXISTS
FOR (f:File) ON (f.last_modified);

CREATE INDEX route_method_index IF NOT EXISTS
FOR (r:Route) ON (r.method);

// =============================================================
// Tipos de Relacionamento Padrão:
//
// (File)-[:IMPORTS]->(File)
// (File)-[:IMPLEMENTS]->(Route)
// (File)-[:READS]->(Table)
// (File)-[:WRITES]->(Table)
// (Component)-[:CALLS]->(Route)
// (Component)-[:USES]->(Component)
// (Session)-[:MODIFIED]->(File)
// (Skill)-[:APPLIES_TO]->(File)
// =============================================================
