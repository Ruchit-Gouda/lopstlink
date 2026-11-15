import { useEffect, useRef, useState } from "react";
import {
  Eye,
  EyeOff,
  Loader2,
  LockKeyhole,
  ShieldCheck,
  X,
} from "lucide-react";
import { login, signup } from "../api";

const EMPTY_FORM = { full_name: "", email: "", password: "" };

export default function AuthDialog({ mode = "login", onClose, onAuthenticated }) {
  const [tab, setTab] = useState(mode);
  const [form, setForm] = useState(EMPTY_FORM);
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const firstFieldRef = useRef(null);

  useEffect(() => {
    const timer = window.setTimeout(() => firstFieldRef.current?.focus(), 60);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    function handleKey(event) {
      if (event.key === "Escape" && !busy) onClose();
    }

    window.addEventListener("keydown", handleKey);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKey);
    };
  }, [busy, onClose]);

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((previous) => ({ ...previous, [name]: value }));
  }

  function switchTab(next) {
    setTab(next);
    setError("");
    setShowPassword(false);
    window.setTimeout(() => firstFieldRef.current?.focus(), 40);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    const email = form.email.trim().toLowerCase();
    const password = form.password;

    if (!/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(email)) {
      setError("Enter a valid email address.");
      return;
    }

    if (tab === "signup" && form.full_name.trim().length < 2) {
      setError("Enter your full name.");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    try {
      setBusy(true);
      const user =
        tab === "signup"
          ? await signup({
              full_name: form.full_name.trim(),
              email,
              password,
            })
          : await login({ email, password });

      onAuthenticated(user, tab);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="modal"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !busy) onClose();
      }}
    >
      <div
        className="modal__panel modal__panel--auth"
        role="dialog"
        aria-modal="true"
        aria-labelledby="auth-dialog-title"
      >
        <button
          type="button"
          className="modal__close"
          onClick={onClose}
          disabled={busy}
          aria-label="Close login dialog"
        >
          <X size={17} aria-hidden="true" />
        </button>

        <span className="auth__badge" aria-hidden="true">
          <LockKeyhole size={20} />
        </span>

        <h3 id="auth-dialog-title">
          {tab === "login" ? "Welcome back" : "Create your account"}
        </h3>
        <p className="auth__subtitle">
          {tab === "login"
            ? "Log in to publish reports, earn credits and see unlocked contacts."
            : "Publish reports, earn Link credits and get contacted on a 70%+ match."}
        </p>

        <div className="auth__tabs" role="tablist" aria-label="Account action">
          <button
            type="button"
            role="tab"
            aria-selected={tab === "login"}
            className={`auth__tab${tab === "login" ? " is-active" : ""}`}
            onClick={() => switchTab("login")}
          >
            Log in
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={tab === "signup"}
            className={`auth__tab${tab === "signup" ? " is-active" : ""}`}
            onClick={() => switchTab("signup")}
          >
            Sign up
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {tab === "signup" && (
            <div className="field">
              <label htmlFor="auth-name">Full name</label>
              <input
                ref={firstFieldRef}
                id="auth-name"
                name="full_name"
                value={form.full_name}
                onChange={handleChange}
                placeholder="Your name"
                maxLength={80}
                autoComplete="name"
                required
              />
            </div>
          )}

          <div className="field">
            <label htmlFor="auth-email">Email</label>
            <input
              ref={tab === "login" ? firstFieldRef : undefined}
              id="auth-email"
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              placeholder="you@college.edu"
              maxLength={254}
              autoComplete="email"
              required
            />
          </div>

          <div className="field">
            <label htmlFor="auth-password">Password</label>
            <div className="password-field">
              <input
                id="auth-password"
                type={showPassword ? "text" : "password"}
                name="password"
                value={form.password}
                onChange={handleChange}
                placeholder={
                  tab === "signup" ? "At least 8 characters" : "Your password"
                }
                minLength={8}
                autoComplete={
                  tab === "signup" ? "new-password" : "current-password"
                }
                required
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword((previous) => !previous)}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? (
                  <EyeOff size={16} aria-hidden="true" />
                ) : (
                  <Eye size={16} aria-hidden="true" />
                )}
              </button>
            </div>
          </div>

          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}

          <button
            type="submit"
            className="btn btn--primary btn--full"
            disabled={busy}
          >
            {busy && <Loader2 size={16} className="spin" aria-hidden="true" />}
            {busy
              ? tab === "login"
                ? "Logging in…"
                : "Creating account…"
              : tab === "login"
                ? "Log in"
                : "Create account"}
          </button>
        </form>

        <p className="auth__note">
          <ShieldCheck size={15} aria-hidden="true" />
          <span>
            Your email is never shown on a report. It is released only to a
            member whose item matches yours at 70% or higher.
          </span>
        </p>
      </div>
    </div>
  );
}
