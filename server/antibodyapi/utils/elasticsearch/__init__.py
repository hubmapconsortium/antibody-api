import elasticsearch

def index_antibody(antibody):
    es_conn = elasticsearch.Elasticsearch()
    doc = {
        'antibody_uuid': antibody['antibody_uuid'],
        'protocols_io_doi': antibody['protocols_io_doi'],
        'uniprot_accession_number': antibody['uniprot_accession_number'],
        'target_name': antibody['target_name'],
        'rrid': antibody['rrid'],
        'antibody_name': antibody['antibody_name'],
        'host_organism': antibody['host_organism'],
        'clonality': antibody['clonality'],
        'vendor': antibody['vendor'],
        'catalog_number': antibody['catalog_number'],
        'lot_number': antibody['lot_number'],
        'recombinant': antibody['recombinant'],
        'organ_or_tissue': antibody['organ_or_tissue'],
        'hubmap_platform': antibody['hubmap_platform'],
        'submitter_orciid': antibody['submitter_orciid']
    }
    es_conn.index(index='hm_antibodies', document=doc) # pylint: disable=unexpected-keyword-arg, no-value-for-parameter
