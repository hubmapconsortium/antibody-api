import React from 'react';
import { useCookies } from 'react-cookie';

function Checkbox(props) {
  const label = props.label;
  const elt = props.element;
  const handleChange = props.handleChange;
  const isChecked = props.isChecked;
  console.info('Checkbox props: ', props);

  return (
    <div>
      <input type="checkbox"
             onChange={handleChange(elt)}
             checked={isChecked(elt)}
      />
      {label}
    </div>
  );
};

export {Checkbox};
