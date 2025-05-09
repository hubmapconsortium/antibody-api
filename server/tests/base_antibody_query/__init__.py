def base_antibody_query():
    return '''
SELECT 
    a.antibody_uuid,
    a.protocol_doi, a.uniprot_accession_number,
    a.target_name, a.rrid, a.host,
    a.clonality, v.vendor_name,
    a.catalog_number, a.lot_number, a.recombinant, a.organ,
    a.method, a.author_orcids, a.hgnc_id, a.isotype,
    a.concentration_value, a.dilution_factor, a.conjugate,
    a.tissue_preservation, a.cycle_number, a.fluorescent_reporter,
    a.manuscript_doi, a.vendor_affiliation, a.organ_uberon_id,
    a.antigen_retrieval, a.omap_id,
    a.group_uuid,
    a.created_by_user_displayname, a.created_by_user_email,
    a.created_by_user_sub
FROM antibodies a
JOIN vendors v ON a.vendor_id = v.id
'''

def base_antibody_query_without_antibody_uuid():
    return '''
SELECT 
    a.protocol_doi, a.uniprot_accession_number,
    a.target_name, a.rrid, a.host,
    a.clonality, v.vendor_name,
    a.catalog_number, a.lot_number, a.recombinant, a.organ,
    a.method, a.author_orcids, a.hgnc_id, a.isotype,
    a.concentration_value, a.dilution_factor, a.conjugate,
    a.tissue_preservation, a.cycle_number, a.fluorescent_reporter,
    a.manuscript_doi, a.vendor_affiliation, a.organ_uberon_id,
    a.antigen_retrieval, a.omap_id,
    a.group_uuid,
    a.created_by_user_displayname, a.created_by_user_email,
    a.created_by_user_sub
FROM antibodies a
JOIN vendors v ON a.vendor_id = v.id
'''
