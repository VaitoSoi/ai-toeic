import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import { createBrowserRouter, RouterProvider } from 'react-router';
import Topics from './pages/Topics';
import Topic from './pages/Topic';
import { Toaster } from './components/ui/sonner';

const router = createBrowserRouter([
    {
        path: "/",
        element: <Topics />,
    },
    {
        path: "/topic/*",
        element: <Topic />
    }
]);


createRoot(document.getElementById('root')!)
    .render(
        <StrictMode>
            <RouterProvider router={router} />
            <Toaster />
        </StrictMode>,
    );
