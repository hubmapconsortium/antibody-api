
CREATE TABLE IF NOT EXISTS "public"."vendors" (
    "id" serial,
    "name" text NOT NULL,
    PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS vendors_unique_index ON vendors(UPPER(name));

DO $$
BEGIN
    IF NOT EXISTS(SELECT 1 FROM pg_type WHERE typname = 'clonality_types') THEN
        CREATE TYPE "clonality_types" AS ENUM ('monoclonal', 'polyclonal');
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS "public"."antibodies" (
    "id" serial,
    "antibody_uuid" uuid NOT NULL,
    "protocols_io_doi" text NOT NULL,
    "uniprot_accession_number" text NOT NULL,
    "target_name" text NOT NULL,
    "rrid" text NOT NULL,
    "antibody_name" text NOT NULL,
    "host_organism" text NOT NULL,
    "clonality" clonality_types NOT NULL,
    "vendor_id" integer REFERENCES vendors(id),
    "catalog_number" text NOT NULL,
    "lot_number" text NOT NULL,
    "recombinant" boolean NOT NULL,
    "organ_or_tissue" text NOT NULL,
    "hubmap_platform" text NOT NULL,
    "submitter_orciid" text NOT NULL,
    "created_timestamp" integer NOT NULL,
    "created_by_user_displayname" text NOT NULL,
    "created_by_user_email" text NOT NULL,
    "created_by_user_sub" text NOT NULL,
    "group_uuid" uuid NOT NULL,
    PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS antibodies_unique_index ON antibodies(UPPER(uniprot_accession_number), UPPER(rrid), UPPER(lot_number), UPPER(target_name), UPPER(hubmap_platform));
