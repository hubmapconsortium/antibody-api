import React, {useState} from 'react';
import { useCookies } from 'react-cookie';

function Checkbox(props) {

  const elt = props.element;
  const label = props.label;
  const id_col = elt + '_col';
  const id_header = id_col + "_head";

  const [cookies, setCookie] = useCookies([]);
  const [checked, setChecked] = useState(cookies[elt]==='true');

  console.info('elt: ', elt, ' id_col: ', id_col, ' id_header: ', id_header, ' label: ', label);
  console.info('display: ', display);
  console.info('cookie_checked: on entry', cookies[elt]);

  const handleChange = () => {
    console.info(elt, "checked on entry:", checked);
    setChecked(!checked);
    setCookie(elt, checked?'false':'true', { path: "/", sameSite: 'strict' });
    console.info('cookie_checked after setCookie: ', cookies[elt]);
    if (checked) {
      display[elt]="none";
      const all_col=document.getElementsByClassName(id_col);
      for (var i=0;i<all_col.length;i++) {
         all_col[i].style.display=display[elt];
      }
      const table_header_elt=document.getElementById(id_header);
      table_header_elt.style.display=display[elt];
    } else {
      display[elt]="table-cell";
      const all_col=document.getElementsByClassName(id_col);
      for(var i=0;i<all_col.length;i++) {
        all_col[i].style.display=display[elt];
      }
      const table_header_elt=document.getElementById(id_header);
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

export {Checkbox};
