import React from 'react';

function Checkbox(props) {
  const label = props.label;
  const elt = props.element;
  const handleChange = props.handleChange;
  const isChecked = props.isChecked;

  const handleToggle = (event) => {
    handleChange(elt, event.target.checked);
  }

  const isCheckedCheck = () => {
    isChecked(elt);
  }

  return (
    <div>
      <input type="checkbox"
             id={`${elt}_checkbox_id`}
             onChange={handleToggle}
             checked={isCheckedCheck}
      />
      {label}
    </div>
  );
};

export {Checkbox};
