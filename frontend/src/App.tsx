import { createBrowserRouter, RouterProvider } from "react-router";
import { AuthProvider } from "@/components/AuthProvider";
import { AppLayout } from "@/components/layout/AppLayout";
import { GuestOnly, RequireAuth } from "@/components/layout/guards";
import { ForgotPasswordPage } from "@/pages/ForgotPasswordPage";
import { HealthPage } from "@/pages/HealthPage";
import { HomePage } from "@/pages/HomePage";
import { LoginPage } from "@/pages/LoginPage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { ProfilePage } from "@/pages/ProfilePage";
import { QuizEditorPage } from "@/pages/QuizEditorPage";
import { QuizPreviewPage } from "@/pages/QuizPreviewPage";
import { QuizzesPage } from "@/pages/QuizzesPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { ResetPasswordPage } from "@/pages/ResetPasswordPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { VerifyEmailPage } from "@/pages/VerifyEmailPage";

// wszystkie adresy aplikacji
const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: "/", element: <HomePage /> },
      {
        path: "/login",
        element: (
          <GuestOnly>
            <LoginPage />
          </GuestOnly>
        ),
      },
      {
        path: "/register",
        element: (
          <GuestOnly>
            <RegisterPage />
          </GuestOnly>
        ),
      },
      { path: "/verify-email", element: <VerifyEmailPage /> },
      { path: "/forgot-password", element: <ForgotPasswordPage /> },
      { path: "/reset-password", element: <ResetPasswordPage /> },
      {
        path: "/profile",
        element: (
          <RequireAuth>
            <ProfilePage />
          </RequireAuth>
        ),
      },
      {
        path: "/settings",
        element: (
          <RequireAuth>
            <SettingsPage />
          </RequireAuth>
        ),
      },
      {
        path: "/quizzes",
        element: (
          <RequireAuth>
            <QuizzesPage />
          </RequireAuth>
        ),
      },
      {
        path: "/quizzes/:id/edit",
        element: (
          <RequireAuth>
            <QuizEditorPage />
          </RequireAuth>
        ),
      },
      { path: "/quizzes/:id/preview", element: <QuizPreviewPage /> },
      { path: "/share/:token", element: <QuizPreviewPage /> },
      { path: "/status", element: <HealthPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);

export function App() {
  return (
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  );
}
