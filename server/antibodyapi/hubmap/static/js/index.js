import SomeComponent from "./components/SomeComponent";
import React from "react";
import ReactDOM from "react-dom";
import { CookiesProvider } from "react-cookie";

const SomePage = () => {
    return <SomeComponent />;
};

ReactDOM.render(<CookiesProvider><SomePage /></CookiesProvider>,
    document.getElementById("render-react-here")
);

