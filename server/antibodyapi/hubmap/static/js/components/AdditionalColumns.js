import React, { useState } from 'react';
import { useCookies } from 'react-cookie';
import { Checkbox } from './Checkbox';

function AdditionalColumns() {

  const checkbox_props = [
    {element:"clone_id", label:"Clone ID"},
    {element:"host", label:"Host"},
    {element:"rrid", label:"RRID"},
    {element:"catalog_number", label:"Catalog#"},
    {element:"lot_number", label:"Lot#"},
    {element:"vendor_name", label:"Vendor"},
    {element:"recombinant", label:"Recombinant"},
    {element:"organ", label:"Organ"},
    {element:"author_orcids", label:"Author ORCiDs"},
    {element:"hgnc_id", label:"HGNC ID"},
    {element:"isotype", label:"Isotype"},
    {element:"concentration_value", label:"Concentration"},
    {element:"dilution_factor", label:"Dilution Factor"},
    {element:"conjugate", label:"Conjugate"},
    {element:"cycle_number", label:"Cycle#"},
    {element:"fluorescent_reporter", label:"Fluorescent Reporter"},
    {element:"manuscript_doi", label:"Manuscript DOI"},
    {element:"protocol_doi", label:"Protocol DOI"},
    {element:"vendor_affiliation", label:"Vendor Affiliation"},
    {element:"organ_uberon_id", label:"Organ UBERON ID"},
    {element:"antigen_retrieval", label:"Antigen Retrieval"},
    {element:"created_by_user_email", label:"Submitter Email"},
    {element:"previous_version_id", label:"Previous Version"},
    {element:"next_version_id", label:"Next Version"},
  ];

  const state_values = Object.assign({}, ...checkbox_props.map((x) =>
    ({[x.element]: document.getElementById(x.element + '_col_head').style.display==='table-cell'?true:false})
    ));
  const [checked, setChecked] = useState(state_values);

  const handleChange = (elt, to_state) => {
    var newChecked = Object.assign({}, checked);
    newChecked[elt] = to_state;
    setChecked(newChecked);
    changeEltDisplayState(elt, to_state);
  };


  const changeEltDisplayState = (elt, to_state) => {
    display[elt] = to_state?'table-cell':'none';

    const id_col = elt + '_col';
    const all_col=document.getElementsByClassName(id_col);
    for (var i=0;i<all_col.length;i++) {
       all_col[i].style.display=display[elt];
    }

    // Uncaught TypeError: document.getElementById(...) is null
    // will only happen if no data has been loaded
    const id_header = id_col + "_head";
    const table_header_elt=document.getElementById(id_header);
    if (table_header_elt !== null) {
      table_header_elt.style.display=display[elt];
    }
  };

  const isChecked = (elt) => {
    return checked[elt];
  };

  const clearAll = () => {
    const state_values = Object.assign({}, ...checkbox_props.map((x) => ({[x.element]: false})));
    setChecked(state_values);
    checkbox_props.forEach(x => changeEltDisplayState(x.element, false));
  };

  const setAll = () => {
    const state_values = Object.assign({}, ...checkbox_props.map((x) => ({[x.element]: true})));
    setChecked(state_values);
    checkbox_props.forEach(x => changeEltDisplayState(x.element, true));
  };

  return (
     <div>
        <div className="header">
            <h3>Additional Columns</h3>
        </div>
        <div>
            <button onClick={setAll}>Set All</button>
            &nbsp;
            <button onClick={clearAll}>Clear All</button>
        </div>
        <div className="content div-border">
            {checkbox_props.map(prop =>
             <Checkbox
               key={prop.element}
               label={prop.label}
               element={prop.element}
               handleChange={handleChange}
               isChecked={isChecked}
               />
            )}
        </div>
    </div>
  );
};

export {AdditionalColumns};
