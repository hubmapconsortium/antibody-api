import React from 'react';

function Checkbox(props) {
  const label = props.label;
  const elt = props.element;
  const handleChange = props.handleChange;
  const isChecked = props.isChecked;

  const handleToggle = (event) => {
    handleChange(elt, event.target.checked);
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
