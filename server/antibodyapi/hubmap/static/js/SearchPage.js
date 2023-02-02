import Search from "./components/Search";
import React from "react";
import ReactDOM from "react-dom";
import { CookiesProvider } from "react-cookie";

const SearchPage = () => {
    return <Search />;
};

ReactDOM.render(<CookiesProvider><SearchPage/></CookiesProvider>,
    document.getElementById("render-react-here")
);
