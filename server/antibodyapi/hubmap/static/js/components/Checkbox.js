import React from 'react';
import { useCookies } from 'react-cookie';

function Checkbox(props) {
  const label = props.label;
  const elt = props.element;
  const handleChange = props.handleChange;
  const isChecked = props.isChecked;
  console.info('Checkbox props: ', props);

  handleToggle = (event) => {
    console.info('handleToggle; e=', event, '; !event.target.checked=', !event.target.checked);
    props.handleChange(elt, !event.target.checked);
  }

  return (
    <div>
      <input type="checkbox"
             id={`${elt}_checkbox_id`}
             onChange={handleToggle}
      />
      {label}
    </div>
  );
};

export {Checkbox};
