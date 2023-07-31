import React, {useState} from 'react';
import { useCookies } from 'react-cookie';

function Checkbox(props) {

  const label = props.label;
  const elt = props.element;
  const id_col = elt + '_col';
  const id_header = id_col + "_head";

  const [cookies, setCookie] = useCookies([]);
  const [checked, setChecked] = useState(cookies[elt]==='true');

  console.info('Checkbox elt: ', elt, ' id_col: ', id_col, ' id_header: ', id_header, ' label: ', label);
  console.info('Checkbox display: ', display);
  console.info('Checkbox cookie_checked: on entry', cookies[elt]);

  const handleChange = () => {
    console.info(elt, "checked on entry:", checked);
    setChecked(!checked);
    setCookie(elt, checked?'false':'true', { path: "/", sameSite: 'strict' });
    console.info('Checkbox cookie_checked after setCookie: ', cookies[elt]);
    display[elt]=checked?"none":"table-cell";
    const all_col=document.getElementsByClassName(id_col);
    for (var i=0;i<all_col.length;i++) {
       all_col[i].style.display=display[elt];
    }
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
             checked={checked}
      />
      {label}
    </div>
  );
};

function ButtonSetAll() {

  const [cookies, setCookie] = useCookies([]);

  console.info('ButtonSetAll: display on entry: ', display);
  console.info('ButtonSetAll: cookies: on entry', cookies);

  const handleClick = () => {
    const display_item = true;
    const never_modify =
        ['target_symbol','uniprot_accession_number','clonality','method','tissue_preservation','avr_pdf_filename']
    for (let elt in display) {
      if (!never_modify.includes(elt)) {
        console.info('ButtonSetAll: modifying display_item: ', display_item, ' elt: ', elt);
        var [checked, setChecked] = useState(cookies[elt]===display_item?'true':'false');
        setChecked(display_item);
        setCookie(elt, display_item?'true':'false', {path: "/", sameSite: 'strict'})
        display[elt] = display_item?"table-cell":"none";
        var id_col = elt + '_col';
        const all_col=document.getElementsByClassName(id_col);
        for (var i=0;i<all_col.length;i++) {
           all_col[i].style.display=display[elt];
        }
        var id_header = id_col + "_head";
        var table_header_elt=document.getElementById(id_header);
        if (table_header_elt !== null) {
          table_header_elt.style.display=display[elt];
        }
      }
    }
  };

  return (
    <div>
      <button onClick={handleClick} />
        Set All
      </button>
    </div>
  );
};

export {Checkbox, ButtonSetAll};
