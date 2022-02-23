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
      antibodies += `<td>${hit._source.antibody_name}</td>`;
      antibodies += `<td>${hit._source.host_organism}</td>`;
      antibodies += `<td><a href="https://www.uniprot.org/uniprot/${hit._source.uniprot_accession_number}#section_general" target="_blank">${hit._source.uniprot_accession_number}</a></td>`;
      antibodies += `<td>${hit._source.target_name}</td>`;
      antibodies += `<td>`;
      if (hit._source.avr_filename != undefined) {
        var assets_url = document.getElementById('assets_url').innerHTML;
        antibodies += `<a href="${assets_url}/${hit._source.avr_uuid}/${hit._source.avr_filename}" target="_blank">${hit._source.avr_filename}</a>`;
      }
      antibodies += `</td>`;
      antibodies += '<td class="rrid_col" style="display:'+display.rrid_col+`;"><a href="https://scicrunch.org/resources/Any/search?q=${hit._source.rrid}" target="_blank">${hit._source.rrid}</a></td>`;
      antibodies += '<td class="clonality_col" style="display:'+display.clonality_col+`;">${hit._source.clonality}</td>`;
      antibodies += '<td class="catalog_number_col" style="display:'+display.catalog_number_col+`;">${hit._source.catalog_number}</td>`;
      antibodies += '<td class="lot_number_col" style="display:'+display.lot_number_col+`;">${hit._source.lot_number}</td>`;
      antibodies += '<td class="vendor_col" style="display:'+display.vendor_col+`;">${hit._source.vendor}</td>`;
      antibodies += '<td class="recombinat_col" style="display:'+display.recombinat_col+`;">${hit._source.recombinant}</td>`;
      antibodies += '<td class="ot_col" style="display:'+display.ot_col+`;">${hit._source.organ_or_tissue}</td>`;
      antibodies += '<td class="hp_col" style="display:'+display.hp_col+`;">${hit._source.hubmap_platform}</td>`;
      antibodies += '<td class="so_col" style="display:'+display.so_col+`;"><a href="https://orcid.org/${hit._source.submitter_orciid}" target="_blank">${hit._source.submitter_orciid}</a></td>`;
      antibodies += '<td class="email_col" style="display:'+display.email_col+`;"><a href="mailto:${hit._source.created_by_user_email}" target="_blank">${hit._source.created_by_user_email}</a></td>`;
      antibodies += `</tr>`;
    }
    return (
      <div style={{width: '100%', boxSizing: 'border-box', padding: 8}}>
        <table id="antibody-results-table" className="sk-table sk-table-striped" style={{width: '100%', boxSizing: 'border-box'}}>
          <thead>
            <tr>
              <th>Name</th>
              <th>Host Organism</th>
              <th>Uniprot#</th>
              <th>Target Name</th>
              <th>PDF</th>
              <th id="rrid_col_head" style={{"display": display.rrid_col}}>RRID</th>
              <th id="clonality_col_head" style={{"display": display.clonality_col}}>Clonality</th>
              <th id="catalog_number_col_head" style={{"display": display.catalog_number_col}}>Catalog#</th>
              <th id="lot_number_col_head" style={{"display": display.lot_number_col}}>Lot#</th>
              <th id="vendor_col_head" style={{"display": display.vendor_col}}>Vendor</th>
              <th id="recombinat_col_head" style={{"display": display.recombinat_col}}>Recombinant</th>
              <th id="ot_col_head" style={{"display": display.ot_col}}>Organ/Tissue</th>
              <th id="hp_col_head" style={{"display": display.hp_col}}>Hubmap Platform</th>
              <th id="so_col_head" style={{"display": display.so_col}}>Submitter Orcid</th>
              <th id="email_col_head" style={{"display": display.email_col}}>Email</th>
            </tr>
          </thead>
          <tbody dangerouslySetInnerHTML={{__html: antibodies}}/>
        </table>
      </div>
    )
  }
}

export default AntibodyHitsTable;
