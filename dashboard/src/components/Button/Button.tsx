import React, { forwardRef } from "react";
import styles from "./Button.module.css";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "success" | "ghost";
  size?: "small" | "medium" | "large";
  loading?: boolean;
  fullWidth?: boolean;
  iconOnly?: boolean;
  children: React.ReactNode;
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
}

type ButtonComponent = React.ForwardRefExoticComponent<
  ButtonProps & React.RefAttributes<HTMLButtonElement>
> & {
  Link: React.ForwardRefExoticComponent<
    LinkButtonProps & React.RefAttributes<HTMLAnchorElement>
  >;
};

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      size = "medium",
      loading = false,
      fullWidth = false,
      iconOnly = false,
      disabled,
      className,
      children,
      ...props
    },
    ref,
  ) => {
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
  },
);

const LinkButton = forwardRef<HTMLAnchorElement, LinkButtonProps>(
  (
    {
      variant = "primary",
      size = "medium",
      loading = false,
      fullWidth = false,
      iconOnly = false,
      className,
      children,
      ...props
    },
    ref,
  ) => {
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
  },
);

Button.displayName = "Button";
LinkButton.displayName = "Button.Link";

(Button as ButtonComponent).Link = LinkButton;

export default Button as ButtonComponent;
