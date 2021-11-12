import React from 'react';

class AntibodyHitsTable extends React.Component {

  render(){
    const { hits } = this.props

    var antibodies = '';
    for (var i = 0; i < hits.length; i++) {
      var hit = hits[i];
      antibodies += `<tr key=${hit._id}>`;
      antibodies += `<td>${hit._source.antibody_name}</td>`;
      antibodies += `<td>${hit._source.host_organism}</td>`;
      antibodies += `<td>${hit._source.target_name}</td>`;
      antibodies += `<td>${hit._source.vendor}</td>`;
      antibodies += `</tr>`;
    }
    return (
      <div style={{width: '100%', boxSizing: 'border-box', padding: 8}}>
        <table className="sk-table sk-table-striped" style={{width: '100%', boxSizing: 'border-box'}}>
          <thead>
            <tr>
              <th>Name</th>
              <th>Host Organism</th>
              <th>Target Name</th>
              <th>Vendor</th>
            </tr>
          </thead>
          <tbody dangerouslySetInnerHTML={{__html: antibodies}}/>
        </table>
      </div>
    )
  }
}

export default AntibodyHitsTable;
