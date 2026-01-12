import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './Signup.jsx'
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import Login from './Login.jsx';
import Home from './Home.jsx';

const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
  },
  {
    path: "/login",
    element: <Login />,
  },
  {
    path: "/home",
    element: <Home />,
  },
])

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>
);
