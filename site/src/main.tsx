import { render } from "preact";

import { App } from "./app.tsx";
import "./styles.css";

const root = document.getElementById("app");
if (!root) throw new Error("no #app element");
render(<App />, root);
