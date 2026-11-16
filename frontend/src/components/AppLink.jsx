import { shouldHandleLink } from "../router";

export default function AppLink({
  to,
  onNavigate,
  className = "",
  children,
  onClick,
  ...rest
}) {
  function handleClick(event) {
    onClick?.(event);

    if (!shouldHandleLink(event)) return;

    event.preventDefault();
    onNavigate?.(to);
  }

  return (
    <a href={to} className={className} onClick={handleClick} {...rest}>
      {children}
    </a>
  );
}
