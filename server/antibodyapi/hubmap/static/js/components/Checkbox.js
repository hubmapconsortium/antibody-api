import React, {useState} from 'react';

function Checkbox(props) {

  const [checked, setChecked] = useState(false);
  const id_col = props.id_col;
  const text_col = props.text_col;
  const table_header=id_col+"_head"

  const handleChange = () => {
    console.info("checkbox handleChange");
    setChecked(!checked);
    if (checked) {
      console.info("hide "+id_col);
      var all_col=document.getElementsByClassName(id_col);
      for (var i=0;i<all_col.length;i++) {
         all_col[i].style.display="none";
      }
      var table_header_elt=document.getElementById(table_header);
      table_header_elt.style.display="none";
    } else {
      console.info("show columns "+id_col);
      var all_col=document.getElementsByClassName(id_col);
      for(var i=0;i<all_col.length;i++) {
        all_col[i].style.display="table-cell";
      }
      var table_header_elt=document.getElementById(table_header);
      table_header_elt.style.display="table-cell";
    }
  };

  return (
    <div>
      <input type="checkbox" onChange={handleChange} /> {text_col}
    </div>
  );
};

export {Checkbox};
