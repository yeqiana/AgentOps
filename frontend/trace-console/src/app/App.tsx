import { Outlet } from "react-router-dom";
import { UI_TEXT } from "../constants/uiText";

export function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="app-eyebrow">{UI_TEXT.app.stage}</p>
          <h1>{UI_TEXT.app.title}</h1>
        </div>
      </header>
      <main className="app-content">
        <Outlet />
      </main>
    </div>
  );
}
