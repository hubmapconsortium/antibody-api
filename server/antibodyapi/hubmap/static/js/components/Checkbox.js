import React, {useState} from 'react';

function Checkbox(props) {

  const [checked, setChecked] = useState(false);
  const id_col = props.id_col;
  const text_col = props.text_col;
  const table_header=id_col+"_head";

  const handleChange = () => {
    console.info(id_col, "checked on entry:", checked)
    setChecked(!checked);
    if (checked) {
      display[id_col]="none";
      var all_col=document.getElementsByClassName(id_col);
      for (var i=0;i<all_col.length;i++) {
         all_col[i].style.display=display[id_col];
      }
      var table_header_elt=document.getElementById(table_header);
      table_header_elt.style.display=display[id_col];
    } else {
      display[id_col]="table-cell";
      var all_col=document.getElementsByClassName(id_col);
      for(var i=0;i<all_col.length;i++) {
        all_col[i].style.display=display[id_col];
      }
      var table_header_elt=document.getElementById(table_header);
      table_header_elt.style.display=display[id_col];
    }
  };

  return (
    <div>
      <input type="checkbox" onChange={handleChange} /> {text_col}
    </div>
  );
};

export {Checkbox};
