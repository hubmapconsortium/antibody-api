import React from 'react';

class AntibodyHitsTable extends React.Component {

  render(){
    const { hits } = this.props;

    console.info('display: ', display);
    console.info('assets_url: ', assets_url);
    var antibodies = '';
    for (var i = 0; i < hits.length; i++) {
      var hit = hits[i];
      antibodies += `<tr key=${hit._id}>`;
      antibodies += `<td class="antibody_name_col">${hit._source.antibody_name}</td>`;
      antibodies += `<td class="host_organism_col">${hit._source.host_organism}</td>`;
      antibodies += `<td class="uniprot_accession_number_col"><a href="https://www.uniprot.org/uniprot/${hit._source.uniprot_accession_number}#section_general" target="_blank">${hit._source.uniprot_accession_number}</a></td>`;
      antibodies += `<td class="target_name_col">${hit._source.target_name}</td>`;
      antibodies += `<td class="avr_filename_col">`;
      if (hit._source.avr_filename != undefined) {
        var assets_url = document.getElementById('assets_url').innerHTML;
        antibodies += `<a href="${assets_url}/${hit._source.avr_uuid}/${hit._source.avr_filename}" target="_blank">${hit._source.avr_filename}</a>`;
      }
      antibodies += `</td>`;
      antibodies += '<td class="rrid_col" style="display:'+display.rrid+`"><a href="https://scicrunch.org/resources/Any/search?q=${hit._source.rrid}" target="_blank">${hit._source.rrid}</a></td>`;
      antibodies += '<td class="clonality_col" style="display:'+display.clonality+`;">${hit._source.clonality}</td>`;
      antibodies += '<td class="catalog_number_col" style="display:'+display.catalog_number+`;">${hit._source.catalog_number}</td>`;
      antibodies += '<td class="lot_number_col" style="display:'+display.lot_number+`;">${hit._source.lot_number}</td>`;
      antibodies += '<td class="vendor_col" style="display:'+display.vendor+`;">${hit._source.vendor}</td>`;
      antibodies += '<td class="recombinant_col" style="display:'+display.recombinant+`;">${hit._source.recombinant}</td>`;
      antibodies += '<td class="organ_or_tissue_col" style="display:'+display.organ_or_tissue+`;">${hit._source.organ_or_tissue}</td>`;
      antibodies += '<td class="hubmap_platform_col" style="display:'+display.hubmap_platform+`;">${hit._source.hubmap_platform}</td>`;
      antibodies += '<td class="submitter_orcid_col" style="display:'+display.submitter_orcid+`;"><a href="https://orcid.org/${hit._source.submitter_orcid}" target="_blank">${hit._source.submitter_orcid}</a></td>`;
      antibodies += '<td class="created_by_user_email_col" style="display:'+display.created_by_user_email+`;"><a href="mailto:${hit._source.created_by_user_email}" target="_blank">${hit._source.created_by_user_email}</a></td>`;
      antibodies += `</tr>`;
    }
    return (
      <div style={{width: '100%', boxSizing: 'border-box', padding: 8}}>
        <table id="antibody-results-table" className="sk-table sk-table-striped" style={{width: '100%', boxSizing: 'border-box'}}>
          <thead>
            <tr>
              <th id="antibody_name_col_head">Name</th>
              <th id="host_organism_col_head">Host Organism</th>
              <th id="uniprot_accession_col_head">UniProt#</th>
              <th id="target_name_col_head">Target Name</th>
              <th id="avr_filename_col_head">PDF</th>
              <th id="rrid_col_head" style={{"display": display.rrid}}>RRID</th>
              <th id="clonality_col_head" style={{"display": display.clonality}}>Clonality</th>
              <th id="catalog_number_col_head" style={{"display": display.catalog_number}}>Catalog#</th>
              <th id="lot_number_col_head" style={{"display": display.lot_number}}>Lot#</th>
              <th id="vendor_col_head" style={{"display": display.vendor}}>Vendor</th>
              <th id="recombinant_col_head" style={{"display": display.recombinant}}>Recombinant</th>
              <th id="organ_or_tissue_col_head" style={{"display": display.organ_or_tissue}}>Organ/Tissue</th>
              <th id="hubmap_platform_col_head" style={{"display": display.hubmap_platform}}>HuBMAP Platform</th>
              <th id="submitter_orcid_col_head" style={{"display": display.submitter_orcid}}>Submitter ORCID</th>
              <th id="created_by_user_email_col_head" style={{"display": display.created_by_user_email}}>Email</th>
            </tr>
          </thead>
          <tbody dangerouslySetInnerHTML={{__html: antibodies}}/>
        </table>
      </div>
    )
  }
}

export default AntibodyHitsTable;
