"""Database repository for CRUD operations."""

from typing import Optional
from uuid import UUID

import psycopg2
import psycopg2.extras

from sandwich.db.models import (
    ForagingLogEntry,
    Ingredient,
    Sandwich,
    SandwichIngredient,
    SandwichRelation,
    Source,
    StructuralType,
)

# Register UUID adapter for psycopg2
psycopg2.extras.register_uuid()


class Repository:
    """Database access layer for SANDWICH entities."""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._conn: Optional[psycopg2.extensions.connection] = None

    def connect(self):
        self._conn = psycopg2.connect(self.connection_string)
        self._conn.autocommit = False

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    @property
    def conn(self) -> psycopg2.extensions.connection:
        if self._conn is None or self._conn.closed:
            self.connect()
        return self._conn

    # --- Sources ---

    def insert_source(self, source: Source) -> UUID:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sources (source_id, url, domain, content, content_hash, fetched_at, content_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING source_id
                """,
                (
                    source.source_id,
                    source.url,
                    source.domain,
                    source.content,
                    source.content_hash,
                    source.fetched_at,
                    source.content_type,
                ),
            )
            result = cur.fetchone()[0]
            self.conn.commit()
            return result

    # --- Structural Types ---

    def insert_structural_type(self, st: StructuralType) -> int:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO structural_types (name, description, bread_relation, filling_role, parent_type_id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING type_id
                """,
                (
                    st.name,
                    st.description,
                    st.bread_relation,
                    st.filling_role,
                    st.parent_type_id,
                ),
            )
            result = cur.fetchone()[0]
            self.conn.commit()
            return result

    def get_all_structural_types(self) -> list[StructuralType]:
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM structural_types ORDER BY type_id")
            rows = cur.fetchall()
            return [StructuralType(**row) for row in rows]

    def get_structural_type_by_name(self, name: str) -> Optional[StructuralType]:
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM structural_types WHERE name = %s", (name,)
            )
            row = cur.fetchone()
            if row:
                return StructuralType(**row)
            return None

    # --- Sandwiches ---

    def insert_sandwich(self, s: Sandwich) -> UUID:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sandwiches (
                    sandwich_id, name, description, created_at,
                    validity_score, bread_compat_score, containment_score,
                    specificity_score, nontrivial_score, novelty_score,
                    bread_top, bread_bottom, filling,
                    source_id, structural_type_id,
                    assembly_rationale, validation_rationale, reuben_commentary
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s
                )
                RETURNING sandwich_id
                """,
                (
                    s.sandwich_id,
                    s.name,
                    s.description,
                    s.created_at,
                    s.validity_score,
                    s.bread_compat_score,
                    s.containment_score,
                    s.specificity_score,
                    s.nontrivial_score,
                    s.novelty_score,
                    s.bread_top,
                    s.bread_bottom,
                    s.filling,
                    s.source_id,
                    s.structural_type_id,
                    s.assembly_rationale,
                    s.validation_rationale,
                    s.reuben_commentary,
                ),
            )
            result = cur.fetchone()[0]
            self.conn.commit()
            return result

    def get_sandwich(self, sandwich_id: UUID) -> Optional[Sandwich]:
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM sandwiches WHERE sandwich_id = %s", (sandwich_id,)
            )
            row = cur.fetchone()
            if row:
                # Remove embedding columns for model construction
                for key in [
                    "bread_top_embedding",
                    "bread_bottom_embedding",
                    "filling_embedding",
                    "sandwich_embedding",
                ]:
                    row.pop(key, None)
                return Sandwich(**row)
            return None

    def get_all_sandwiches(self) -> list[Sandwich]:
        """Load all sandwiches (without embeddings) for corpus init."""
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM sandwiches ORDER BY created_at")
            rows = cur.fetchall()
            results = []
            for row in rows:
                for key in [
                    "bread_top_embedding",
                    "bread_bottom_embedding",
                    "filling_embedding",
                    "sandwich_embedding",
                ]:
                    row.pop(key, None)
                results.append(Sandwich(**row))
            return results

    def get_sandwich_embeddings(self, sandwich_id: UUID) -> Optional[list[float]]:
        """Get the full sandwich embedding vector."""
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT sandwich_embedding::text FROM sandwiches WHERE sandwich_id = %s",
                (sandwich_id,),
            )
            row = cur.fetchone()
            if row and row[0]:
                # pgvector returns text like "[0.01,0.02,...]"
                return [float(x) for x in row[0].strip("[]").split(",")]
            return None

    def update_sandwich_embeddings(
        self,
        sandwich_id: UUID,
        bread_top_emb: list[float],
        bread_bottom_emb: list[float],
        filling_emb: list[float],
        sandwich_emb: list[float],
    ) -> None:
        """Store embedding vectors for a sandwich."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                UPDATE sandwiches SET
                    bread_top_embedding = %s,
                    bread_bottom_embedding = %s,
                    filling_embedding = %s,
                    sandwich_embedding = %s
                WHERE sandwich_id = %s
                """,
                (
                    bread_top_emb,
                    bread_bottom_emb,
                    filling_emb,
                    sandwich_emb,
                    sandwich_id,
                ),
            )
            self.conn.commit()

    # --- Ingredients ---

    def insert_ingredient(self, ingredient: Ingredient) -> UUID:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ingredients (ingredient_id, text, ingredient_type, first_seen_sandwich, first_seen_at, usage_count)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING ingredient_id
                """,
                (
                    ingredient.ingredient_id,
                    ingredient.text,
                    ingredient.ingredient_type,
                    ingredient.first_seen_sandwich,
                    ingredient.first_seen_at,
                    ingredient.usage_count,
                ),
            )
            result = cur.fetchone()[0]
            self.conn.commit()
            return result

    # --- Sandwich Ingredients ---

    def link_sandwich_ingredient(self, si: SandwichIngredient):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sandwich_ingredients (sandwich_id, ingredient_id, role)
                VALUES (%s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (si.sandwich_id, si.ingredient_id, si.role),
            )
            self.conn.commit()

    # --- Relations ---

    def insert_relation(self, rel: SandwichRelation):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sandwich_relations (relation_id, sandwich_a, sandwich_b, relation_type, similarity_score, rationale)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (
                    rel.relation_id,
                    rel.sandwich_a,
                    rel.sandwich_b,
                    rel.relation_type,
                    rel.similarity_score,
                    rel.rationale,
                ),
            )
            self.conn.commit()

    # --- Foraging Log ---

    def insert_foraging_log(self, entry: ForagingLogEntry):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO foraging_log (log_id, timestamp, source_id, curiosity_prompt, outcome, outcome_rationale, sandwich_id, session_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    entry.log_id,
                    entry.timestamp,
                    entry.source_id,
                    entry.curiosity_prompt,
                    entry.outcome,
                    entry.outcome_rationale,
                    entry.sandwich_id,
                    entry.session_id,
                ),
            )
            self.conn.commit()
