import React from "react";
import styles from "./Button.module.css";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "success" | "ghost";
  size?: "small" | "medium" | "large";
  loading?: boolean;
  fullWidth?: boolean;
  iconOnly?: boolean;
  children: React.ReactNode;
  ref?: React.Ref<HTMLButtonElement>;
}

export interface LinkButtonProps
  extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  variant?: "primary" | "secondary" | "danger" | "success" | "ghost";
  size?: "small" | "medium" | "large";
  loading?: boolean;
  fullWidth?: boolean;
  iconOnly?: boolean;
  href: string;
  children: React.ReactNode;
  ref?: React.Ref<HTMLAnchorElement>;
}

type ButtonComponent = typeof Button & {
  Link: typeof LinkButton;
};

function Button({
  variant = "primary",
  size = "medium",
  loading = false,
  fullWidth = false,
  iconOnly = false,
  disabled,
  className,
  children,
  ref,
  ...props
}: ButtonProps) {
  const buttonClasses = [
    styles.button,
    styles[variant],
    styles[size],
    loading && styles.loading,
    disabled && styles.disabled,
    fullWidth && styles.fullWidth,
    iconOnly && styles.iconOnly,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <button
      ref={ref}
      className={buttonClasses}
      disabled={disabled || loading}
      aria-disabled={disabled || loading}
      {...props}
    >
      {children}
    </button>
  );
}

function LinkButton({
  variant = "primary",
  size = "medium",
  loading = false,
  fullWidth = false,
  iconOnly = false,
  className,
  children,
  ref,
  ...props
}: LinkButtonProps) {
  const linkClasses = [
    styles.button,
    styles[variant],
    styles[size],
    loading && styles.loading,
    fullWidth && styles.fullWidth,
    iconOnly && styles.iconOnly,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <a ref={ref} className={linkClasses} aria-disabled={loading} {...props}>
      {children}
    </a>
  );
}

Button.displayName = "Button";
LinkButton.displayName = "Button.Link";

(Button as ButtonComponent).Link = LinkButton;

export default Button as ButtonComponent;
