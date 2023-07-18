
CREATE TABLE IF NOT EXISTS "public"."vendors" (
    "id" serial,
    "vendor_name" text NOT NULL,
    PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS vendors_unique_index ON vendors(UPPER(vendor_name));

DO $$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'clonality_types') THEN
        CREATE TYPE "clonality_types" AS ENUM ('monoclonal', 'polyclonal', 'oligoclonal');
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS "public"."antibodies" (
    "id" serial,

    "antibody_uuid" uuid NOT NULL,
    "avr_pdf_filename" text,
    "avr_pdf_uuid" uuid,
    "protocol_doi" text NOT NULL,
    "uniprot_accession_number" text NOT NULL,
    "target_symbol" text NOT NULL,
    "rrid" text NOT NULL,
    "cell_line" text NOT NULL,
    "cell_line_ontology_id" text NOT NULL,
    "host" text NOT NULL,
    "clonality" clonality_types NOT NULL,
    "vendor_id" integer REFERENCES vendors(id),
    "catalog_number" text NOT NULL,
    "lot_number" text NOT NULL,
    "recombinant" text NOT NULL,
    "organ" text NOT NULL,
    "method" text NOT NULL,
    "author_orcids" text NOT NULL,
    "hgnc_id" text NOT NULL,
    "isotype" text NOT NULL,
    "concentration_value" text,
    "dilution" text,
    "conjugate" text,
    "tissue_preservation" text NOT NULL,
    "cycle_number" text NOT NULL,
    "fluorescent_reporter" text NOT NULL,
    "manuscript_doi" text NOT NULL,
    "vendor_affiliation" text,
    "organ_uberon" text NOT NULL,
    "antigen_retrieval" text NOT NULL,
    "omap_id" text,

    "group_uuid" uuid NOT NULL,
    "created_timestamp" integer NOT NULL,
    "created_by_user_displayname" text NOT NULL,
    "created_by_user_email" text NOT NULL,
    "created_by_user_sub" text NOT NULL,
    PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS antibody_uuid_index ON antibodies(antibody_uuid);
