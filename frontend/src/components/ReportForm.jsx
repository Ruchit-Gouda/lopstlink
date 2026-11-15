import { useEffect, useRef, useState } from "react";
import {
  CalendarDays,
  Coins,
  Loader2,
  LogIn,
  PackageOpen,
  Search,
  ShieldCheck,
  Upload,
  X,
} from "lucide-react";
import { todayISO } from "../utils/format";

const CATEGORY_SUGGESTIONS = [
  "Phone",
  "Laptop",
  "Wallet",
  "Bag",
  "Documents",
  "Keys",
  "Bottle",
  "Clothing",
  "Accessories",
  "Books",
  "Other",
];

const LOST_POINTS = 10;
const FOUND_POINTS = 15;
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/;
const PHONE_RE = /^[0-9+()\-\s]{7,20}$/;

function emptyForm(reportType = "lost") {
  return {
    report_type: reportType,
    item_name: "",
    category: "",
    brand: "",
    color: "",
    location_text: "",
    event_date: todayISO(),
    description: "",
  };
}

export default function ReportForm({ user, onCreated, onRequireAuth }) {
  const [form, setForm] = useState(() => emptyForm());
  const [contact, setContact] = useState({
    contact_name: "",
    contact_email: "",
    contact_phone: "",
  });
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const fileRef = useRef(null);
  const syncedUserId = useRef(null);

  const reward = form.report_type === "found" ? FOUND_POINTS : LOST_POINTS;

  useEffect(() => {
    if (!user) {
      syncedUserId.current = null;
      return;
    }

    if (syncedUserId.current === user.id) return;
    syncedUserId.current = user.id;

    setContact({
      contact_name: user.full_name || "",
      contact_email: user.email || "",
      contact_phone: user.contact?.phone || "",
    });
  }, [user]);

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((previous) => ({ ...previous, [name]: value }));
  }

  function handleContactChange(event) {
    const { name, value } = event.target;
    setContact((previous) => ({ ...previous, [name]: value }));
  }

  function handleImage(event) {
    const file = event.target.files?.[0] || null;

    if (!file) {
      setImage(null);
      setPreview("");
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setError("Image must be smaller than 5 MB.");
      event.target.value = "";
      return;
    }

    setError("");
    setImage(file);
    setPreview((previous) => {
      if (previous) URL.revokeObjectURL(previous);
      return URL.createObjectURL(file);
    });
  }

  function clearImage() {
    setImage(null);
    setPreview("");
    if (fileRef.current) fileRef.current.value = "";
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    if (!user) {
      setError("Log in or create an account to publish your report.");
      onRequireAuth?.();
      return;
    }

    if (!image) {
      setError("Please choose a photo of the item.");
      return;
    }

    const contactName = contact.contact_name.trim();
    const contactEmail = contact.contact_email.trim().toLowerCase();
    const contactPhone = contact.contact_phone.trim();

    if (contactName.length < 2) {
      setError("Enter the name we should share with a match.");
      return;
    }

    if (!EMAIL_RE.test(contactEmail)) {
      setError("Enter a valid contact email address.");
      return;
    }

    if (contactPhone && !PHONE_RE.test(contactPhone)) {
      setError("Enter a valid phone number, or leave it blank.");
      return;
    }

    const formData = new FormData();
    Object.entries(form).forEach(([key, value]) => {
      formData.append(key, value);
    });
    formData.append("contact_name", contactName);
    formData.append("contact_email", contactEmail);
    formData.append("contact_phone", contactPhone);
    formData.append("image", image);

    try {
      setSubmitting(true);
      await onCreated(formData);
      setForm(emptyForm(form.report_type));
      clearImage();
    } catch (requestError) {
      if (requestError.status === 401) {
        onRequireAuth?.();
      }
      setError(requestError.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="form-card">
      <div className="panel-heading">
        <div>
          <h2>Report an item</h2>
          <p>Lost something or found something? Add the details below.</p>
        </div>
      </div>

      {!user && (
        <div className="form-callout">
          <LogIn size={18} aria-hidden="true" />
          <div className="form-callout__body">
            <strong>Log in to publish</strong>
            <p>Publishing earns credits and lets a 70%+ match contact you.</p>
          </div>
          <button
            type="button"
            className="btn btn--ghost btn--sm"
            onClick={onRequireAuth}
          >
            Log in
          </button>
        </div>
      )}

      <form className="report-form" onSubmit={handleSubmit}>
        <div className="type-toggle" role="group" aria-label="Report type">
          <button
            type="button"
            className={`type-toggle__btn${
              form.report_type === "lost" ? " is-active" : ""
            }`}
            aria-pressed={form.report_type === "lost"}
            onClick={() =>
              setForm((previous) => ({ ...previous, report_type: "lost" }))
            }
          >
            <Search size={16} aria-hidden="true" />
            I lost something
          </button>
          <button
            type="button"
            className={`type-toggle__btn${
              form.report_type === "found" ? " is-active" : ""
            }`}
            aria-pressed={form.report_type === "found"}
            onClick={() =>
              setForm((previous) => ({ ...previous, report_type: "found" }))
            }
          >
            <PackageOpen size={16} aria-hidden="true" />
            I found something
          </button>
        </div>

        <div className="field">
          <label htmlFor="item_name">Item name</label>
          <input
            id="item_name"
            name="item_name"
            value={form.item_name}
            onChange={handleChange}
            placeholder="Black wallet, iPhone 15, water bottle…"
            maxLength={120}
            required
          />
        </div>

        <div className="field-row">
          <div className="field">
            <label htmlFor="category">Category</label>
            <input
              id="category"
              name="category"
              value={form.category}
              onChange={handleChange}
              placeholder="Wallet"
              list="category-suggestions"
              maxLength={80}
              required
            />
            <datalist id="category-suggestions">
              {CATEGORY_SUGGESTIONS.map((category) => (
                <option key={category} value={category} />
              ))}
            </datalist>
          </div>

          <div className="field">
            <label htmlFor="color">Color</label>
            <input
              id="color"
              name="color"
              value={form.color}
              onChange={handleChange}
              placeholder="Black"
              maxLength={60}
            />
          </div>
        </div>

        <div className="field-row">
          <div className="field">
            <label htmlFor="brand">Brand</label>
            <input
              id="brand"
              name="brand"
              value={form.brand}
              onChange={handleChange}
              placeholder="Optional"
              maxLength={80}
            />
          </div>

          <div className="field">
            <label htmlFor="event_date">Date</label>
            <div className="input-with-icon">
              <CalendarDays size={16} aria-hidden="true" />
              <input
                id="event_date"
                type="date"
                name="event_date"
                value={form.event_date}
                onChange={handleChange}
                max={todayISO()}
                required
              />
            </div>
          </div>
        </div>

        <div className="field">
          <label htmlFor="location_text">Location</label>
          <input
            id="location_text"
            name="location_text"
            value={form.location_text}
            onChange={handleChange}
            placeholder="Library, cafeteria, hostel block…"
            maxLength={160}
            required
          />
        </div>

        <div className="field">
          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            name="description"
            value={form.description}
            onChange={handleChange}
            placeholder="Distinguishing marks, contents, where you last saw it…"
            maxLength={1000}
            required
          />
        </div>

        <div className="form-section">
          <div className="form-section__head">
            <h3>Contact details</h3>
            <span className="form-section__hint">
              <ShieldCheck size={12} aria-hidden="true" />
              Unlocks at 70%+
            </span>
          </div>

          <div className="field-row">
            <div className="field">
              <label htmlFor="contact_name">Your name</label>
              <input
                id="contact_name"
                name="contact_name"
                value={contact.contact_name}
                onChange={handleContactChange}
                placeholder="Name shared with a match"
                maxLength={120}
                autoComplete="name"
              />
            </div>

            <div className="field">
              <label htmlFor="contact_email">Contact email</label>
              <input
                id="contact_email"
                type="email"
                name="contact_email"
                value={contact.contact_email}
                onChange={handleContactChange}
                placeholder="you@gmail.com"
                maxLength={254}
                autoComplete="email"
              />
            </div>
          </div>

          <div className="field">
            <label htmlFor="contact_phone">Phone (optional)</label>
            <input
              id="contact_phone"
              type="tel"
              name="contact_phone"
              value={contact.contact_phone}
              onChange={handleContactChange}
              placeholder="+91 98765 43210"
              maxLength={30}
              autoComplete="tel"
            />
          </div>
        </div>

        <div className="field">
          <label htmlFor="image">Photo</label>

          {preview ? (
            <div className="upload upload--filled">
              <img src={preview} alt="Selected item preview" />
              <button
                type="button"
                className="upload__remove"
                onClick={clearImage}
                aria-label="Remove selected image"
              >
                <X size={16} aria-hidden="true" />
              </button>
            </div>
          ) : (
            <label className="upload upload--empty" htmlFor="image">
              <span className="upload__icon" aria-hidden="true">
                <Upload size={20} />
              </span>
              <span className="upload__text">
                <strong>Upload a photo</strong>
                <small>JPG, PNG or WEBP · up to 5 MB</small>
              </span>
              <input
                ref={fileRef}
                id="image"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={handleImage}
              />
            </label>
          )}
        </div>

        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}

        <button
          type="submit"
          className="btn btn--primary btn--full"
          disabled={submitting}
        >
          {submitting && <Loader2 size={17} className="spin" aria-hidden="true" />}
          {submitting ? "Publishing…" : "Publish report"}
        </button>

        <p className="credits-hint">
          <Coins size={14} aria-hidden="true" />
          Earn <strong>+{reward} credits</strong> for this{" "}
          {form.report_type} report
        </p>
      </form>
    </div>
  );
}
