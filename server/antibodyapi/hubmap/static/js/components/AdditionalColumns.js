import React, { useState } from 'react';
import { useCookies } from 'react-cookie';
import { Checkbox } from './Checkbox';

function AdditionalColumns() {

  const checkbox_props = [
    {element:"clone_id", label:"Clone ID"},
    {element:"cell_line", label:"Cell Line"},
  ];

  const state_values = Object.assign({}, ...checkbox_props.map((x) => ({[x.element]: false})));
  const [checked, setChecked] = useState(state_values);
  console.info('Set useState for state_values; checked:', checked);

  const handleChange = (elt) => {
    console.info(elt, "Checkbox handler: checked before:", checked, ' elt: ', elt);
    setChecked({...checked, ...{elt: !checked.elt}});
    console.info('Checkbox handler: checked after: ', checked, ' elt: ', elt);
    display[elt] = checked.elt?'table-cell':'none';
    const id_col = elt + '_col';
    const all_col=document.getElementsByClassName(id_col);
    for (var i=0;i<all_col.length;i++) {
       all_col[i].style.display=display[elt];
    }
    console.info('Checkbox handler: display after: ', display);
    // Uncaught TypeError: document.getElementById(...) is null
    // will only happen if no data has been loaded
    const id_header = id_col + "_head";
    const table_header_elt=document.getElementById(id_header);
    if (table_header_elt !== null) {
      table_header_elt.style.display=display[elt];
    }
  };

  const isChecked = (elt) => {
    console.info('isChecked: elt: ', elt, ' checked: ', checked, ' checked.elt: ', checked.elt);
    return checked.elt;
  };

  return (
     <div>
        <div className="header"><h3>Additional Columns</h3></div>
        <div className="content div-border">
            {checkbox_props.map(prop =>
             <Checkbox
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
