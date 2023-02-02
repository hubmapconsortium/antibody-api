import React, {useState} from 'react';
import { useCookies } from 'react-cookie';

function Checkbox(props) {

  const [cookies, setCookie] = useCookies([]);
  const elt = props.element;
  const [checked, setChecked] = useState(cookies[elt]==='true');
  const id_col = elt + '_col'
  const id_header = id_col + "_head";
  const label = props.label;
  //console.info('elt: ', elt, ' id_col: ', id_col, ' id_header: ', id_header, ' label: ', label);
  //console.info('display: ', display);
  //console.info('cookie_checked: on entry', cookies[elt]);

  const handleChange = () => {
    //console.info(elt, "checked on entry:", checked);
    setChecked(!checked);
    setCookie(elt, checked?'false':'true', { path: "/" });
    //console.info('cookie_checked after setCookie: ', cookies[elt]);
    if (checked) {
      display[elt]="none";
      var all_col=document.getElementsByClassName(id_col);
      for (var i=0;i<all_col.length;i++) {
         all_col[i].style.display=display[elt];
      }
      var table_header_elt=document.getElementById(id_header);
      table_header_elt.style.display=display[elt];
    } else {
      display[elt]="table-cell";
      var all_col=document.getElementsByClassName(id_col);
      for(var i=0;i<all_col.length;i++) {
        all_col[i].style.display=display[elt];
      }
      var table_header_elt=document.getElementById(id_header);
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
