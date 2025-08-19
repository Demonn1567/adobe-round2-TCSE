import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.jsx';
import Library from './components/library/library.jsx';
import Workspace from './pages/Workspace.jsx';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { ThemeProvider } from './ThemeContext.jsx';
import VoiceSelect from './components/voiceControl/voiceControl.jsx';


const routes = createBrowserRouter([
  {
    path : "/",
    element: <App/>,
    children: [
      { path : "library", element : <Library/> },
      { path : "workspace", element: <Workspace/> },
      { path : "test", element: <VoiceSelect/>},
    ]
  }
]);

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider>
      <RouterProvider router={routes}/>
    </ThemeProvider>
  </StrictMode>
);
