import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { router } from "./app/router";
import { AuthProvider } from "./features/auth/AuthProvider";
import { applyDensityMode, getStoredDensityMode } from "./hooks/useDensityMode";
import { applyThemeMode, getStoredThemeMode } from "./hooks/useThemeMode";
import "./app/styles.css";

applyDensityMode(getStoredDensityMode());
applyThemeMode(getStoredThemeMode());

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  </React.StrictMode>
);
