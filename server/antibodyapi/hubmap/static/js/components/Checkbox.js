import React, {useState} from 'react';
import { useCookies } from 'react-cookie';

function Checkbox(props) {

  const label = props.label;
  const elt = props.element;
  const checked = props.checked.elt;
  const setChecked = props.setChecked;
  const setCookie = props.setCookie;

  const id_col = elt + '_col';
  const id_header = id_col + "_head";

  //const [cookies, setCookie] = useCookies([]);
  //const [checked, setChecked] = useState(cookies[elt]==='true');

  console.info('Checkbox elt: ', elt, ' id_col: ', id_col, ' id_header: ', id_header, ' label: ', label);
  console.info('Checkbox display: ', display);

  const handleChange = () => {
    console.info(elt, "Checkbox handler: checked on entry:", props.checked);
    setChecked({...props.checked, ...{elt: checked==='false'?'true':'false'}});
    console.info('Checkbox handler: chected after reversing: ', props.checked);
    setCookie(elt, checked==='false'?'true':'false', { path: "/", sameSite: 'strict' });
    display[elt] = checked==="false"?'table-cell':'none';
    const all_col=document.getElementsByClassName(id_col);
    console.info('Checkbox handler: all_col: ', all_col)
    console.info('Checkbox handler: display before: ', display)
    for (var i=0;i<all_col.length;i++) {
       all_col[i].style.display=display[elt];
    }
    console.info('Checkbox handler: display after: ', display)
    // Uncaught TypeError: document.getElementById(...) is null
    // will only happen if no data has been loaded
    const table_header_elt=document.getElementById(id_header);
    if (table_header_elt !== null) {
      table_header_elt.style.display=display[elt];
    }
  };

  return (
    <div>
      <input type="checkbox"
             onChange={handleChange}
             checked={checked==='false'?true:false}
      />
      {label}
    </div>
  );
};

function AdditionalColumns() {

  const checkbox_props = [
    {element:"clone_id", label:"Clone ID"},
    {element:"cell_line", label:"Cell Line"},
    {element:"cell_line_ontology_id", label:"Cell Line Ontology ID"},
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
    {element:"omap_id", label:"OMAP ID"},
    {element:"created_by_user_email", label:"Submitter Email"}
  ];

  const [cookies, setCookie] = useCookies([]);
  const state_values = Object.assign({}, ...checkbox_props.map((x) => ({[x.element]: cookies[x.element]})));
  const [checked, setChecked] = useState(state_values);
  console.info('AdditionalColumns cookies: ', cookies);
  console.info('AdditionalColumns state_values: ', state_values);

  return (
     <div>
        <div className="header"><h3>Additional Columns</h3></div>
        <div className="content div-border">
            {checkbox_props.map(prop =>
             <Checkbox
               label={prop.label}
               element={prop.element}
               checked={checked}
               setChecked={setChecked}
               setCookie={setCookie}
               />
             )}
        </div>
    </div>
  );
};

export {AdditionalColumns};
