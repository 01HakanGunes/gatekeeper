- Dont use React.FC instead "The recommended modern approach is to define your component's props using a type or interface and then apply it directly to the function's parameters".

- Do not use direct React imports. (import React)

- Do not use forwardRef instead use "Starting in React 19, you can now access ref as a prop for function components:

function MyInput({placeholder, ref}) {
return <input placeholder={placeholder} ref={ref} />
}

//...
<MyInput ref={ref} />"

-
