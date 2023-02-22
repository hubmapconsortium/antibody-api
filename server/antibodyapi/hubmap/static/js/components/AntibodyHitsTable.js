import React from 'react';

class AntibodyHitsTable extends React.Component {

  render(){
    const { hits } = this.props;

    //console.info('display: ', display);
    //console.info('assets_url: ', assets_url);
    var antibodies = '';
    var organ_uberon_url_encode = '';
    for (var i = 0; i < hits.length; i++) {
      var hit = hits[i];
      antibodies += `<tr key=${hit._id}>`;
      antibodies += `<td class="target_name_col"><a href="https://www.uniprot.org/uniprotkb?query=(protein_name:%22${hit._source.target_name}%22)%20AND%20(accession:${hit._source.uniprot_accession_number})" target="_blank">${hit._source.target_name}</a></td>`;
      antibodies += `<td class="uniprot_accession_number_col"><a href="https://www.uniprot.org/uniprot/${hit._source.uniprot_accession_number}#section_general" target="_blank">${hit._source.uniprot_accession_number}</a></td>`;
      antibodies += `<td class="clonality_col">${hit._source.clonality}</td>`;
      antibodies += `<td class="method_col">${hit._source.method}</td>`;
      antibodies += `<td class="tissue_preservation_col">${hit._source.tissue_preservation}</td>`;
      antibodies += `<td class="avr_pdf_filename_col">`;
      if (hit._source.avr_pdf_filename != undefined) {
        antibodies += `<a href="${assets_url}/${hit._source.avr_pdf_uuid}/${hit._source.avr_pdf_filename}" target="_blank">${hit._source.avr_pdf_filename}</a>`;
      }
      antibodies += `</td>`;

      antibodies += '<td class="host_col" style="display:'+display.lot_number+`;">${hit._source.host}</td>`;
      antibodies += '<td class="rrid_col" style="display:'+display.rrid+`;"><a href="https://scicrunch.org/resolver/RRID:${hit._source.rrid}" target="_blank">${hit._source.rrid}</a></td>`;
      antibodies += '<td class="catalog_number_col" style="display:'+display.catalog_number+`;">${hit._source.catalog_number}</td>`;
      antibodies += '<td class="lot_number_col" style="display:'+display.lot_number+`;">${hit._source.lot_number}</td>`;
      antibodies += '<td class="vendor_name_col" style="display:'+display.vendor_name+`;">${hit._source.vendor_name}</td>`;
      antibodies += '<td class="recombinant_col" style="display:'+display.recombinant+`;">${hit._source.recombinant}</td>`;
      antibodies += '<td class="organ_col" style="display:'+display.organ+`;">${hit._source.organ}</td>`;
      antibodies += '<td class="method_col" style="display:'+display.method+`;">${hit._source.method}</td>`;
      antibodies += '<td class="author_orcid_col" style="display:'+display.author_orcid+`;"><a href="https://orcid.org/${hit._source.author_orcid}" target="_blank">${hit._source.author_orcid}</a></td>`;
      antibodies += '<td class="hgnc_id_col" style="display:'+display.hgnc_id+`"><a href="https://www.genenames.org/tools/search/#!/?query=${hit._source.hgnc_id}" target="_blank">${hit._source.hgnc_id}</a></td>`;
      antibodies += '<td class="isotype_col" style="display:'+display.isotype+`;">${hit._source.isotype}</td>`;
      antibodies += '<td class="concentration_value_col" style="display:'+display.concentration_value+`;">${hit._source.concentration_value}</td>`;
      antibodies += '<td class="dilution_col" style="display:'+display.dilution+`;">${hit._source.dilution}</td>`;
      antibodies += '<td class="conjugate_col" style="display:'+display.conjugate+`;">${hit._source.conjugate}</td>`;
      antibodies += '<td class="cycle_number_col" style="display:'+display.cycle_number+`;">${hit._source.cycle_number}</td>`;
      antibodies += '<td class="fluorescent_reporter_col" style="display:'+display.fluorescent_reporter+`;">${hit._source.fluorescent_reporter}</td>`;
      antibodies += '<td class="manuscript_doi_col" style="display:'+display.manuscript_doi+`;"><a href="https://www.doi.org/${hit._source.manuscript_doi}" target="_blank">${hit._source.manuscript_doi}</a></td>`;
      antibodies += '<td class="protocols_doi_col" style="display:'+display.protocols_doi+`;"><a href="https://www.doi.org/${hit._source.protocols_doi}" target="_blank">${hit._source.protocols_doi}</a></td>`;
      antibodies += '<td class="vendor_affiliation_col" style="display:'+display.vendor_affiliation+`;">${hit._source.vendor_affiliation}</td>`;
      organ_uberon_url_encode = hit._source.organ_uberon.replace(':','%3A');
      antibodies += '<td class="organ_uberon_col" style="display:'+display.organ_uberon+`;"><a href="https://www.ebi.ac.uk/ols/search?q=${organ_uberon_url_encode}&groupField=iri&exact=on&start=0" target="_blank">${hit._source.organ_uberon}</a></td>`;
      antibodies += '<td class="antigen_retrieval_col" style="display:'+display.antigen_retrieval+`;">${hit._source.antigen_retrieval}</td>`;
      antibodies += '<td class="omap_id_col" style="display:'+display.omap_id+`;">${hit._source.omap_id}</td>`;
      antibodies += '<td class="created_by_user_email_col" style="display:'+display.created_by_user_email+`;"><a href="mailto:${hit._source.created_by_user_email}" target="_blank">${hit._source.created_by_user_email}</a></td>`;
      antibodies += `</tr>`;
    }
    return (
      <div style={{width: '100%', boxSizing: 'border-box', padding: 8}}>
        <table id="antibody-results-table" className="sk-table sk-table-striped" style={{width: '100%', boxSizing: 'border-box'}}>
          <thead>
            <tr>
              <th id="target_name_col_head">Target Name</th>
              <th id="uniprot_accession_col_head">UniProt#</th>
              <th id="clonality_col_head">Clonality</th>
              <th id="method_col_head">Method</th>
              <th id="tissue_preservation_col_head">Tissue Preservation</th>
              <th id="avr_pdf_filename_col_head">PDF</th>

              <th id="host_col_head" style={{"display": display.host}}>Host</th>
              <th id="rrid_col_head" style={{"display": display.rrid}}>RRID</th>
              <th id="catalog_number_col_head" style={{"display": display.catalog_number}}>Catalog#</th>
              <th id="lot_number_col_head" style={{"display": display.lot_number}}>Lot#</th>
              <th id="vendor_name_col_head" style={{"display": display.vendor_name}}>Vendor</th>
              <th id="recombinant_col_head" style={{"display": display.recombinant}}>Recombinant</th>
              <th id="organ_col_head" style={{"display": display.organ}}>Organ</th>
              <th id="author_orcid_col_head" style={{"display": display.author_orcid}}>Author ORCiD iD</th>
              <th id="hgnc_id_col_head" style={{"display": display.hgnc_id}}>HGNC ID</th>
              <th id="isotype_col_head" style={{"display": display.isotype}}>Isotype</th>
              <th id="concentration_value_col_head" style={{"display": display.concentration_value}}>Concentration</th>
              <th id="dilution_col_head" style={{"display": display.dilution}}>Dilution</th>
              <th id="conjugate_col_head" style={{"display": display.conjugate}}>Conjugate</th>
              <th id="cycle_number_col_head" style={{"display": display.cycle_number}}>Cycle#</th>
              <th id="fluorescent_reporter_col_head" style={{"display": display.fluorescent_reporter}}>Fluorescent Reporter</th>
              <th id="manuscript_doi_col_head" style={{"display": display.manuscript_doi}}>Manuscript DOI</th>
              <th id="protocols_doi_col_head" style={{"display": display.protocols_doi}}>Protocols DOI</th>
              <th id="vendor_affiliation_col_head" style={{"display": display.vendor_affiliation}}>Vendor Affiliation</th>
              <th id="organ_uberon_col_head" style={{"display": display.organ_uberon}}>Organ UBERON</th>
              <th id="antigen_retrieval_col_head" style={{"display": display.antigen_retrieval}}>Antigen Retrieval</th>
              <th id="omap_id_col_head" style={{"display": display.omap_id}}>OMAP ID</th>
              <th id="created_by_user_email_col_head" style={{"display": display.created_by_user_email}}>Submitter Email</th>
            </tr>
          </thead>
          <tbody dangerouslySetInnerHTML={{__html: antibodies}}/>
        </table>
      </div>
    )
  }
}

export default AntibodyHitsTable;
