import React, { useState, useCallback } from "react";
import styles from "./Input.module.css";

export interface BaseInputProps {
  variant?: "default" | "error" | "success";
  size?: "small" | "medium" | "large";
  fullWidth?: boolean;
  label?: string;
  helperText?: string;
  required?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  maxLength?: number;
  showCharacterCount?: boolean;
}

export interface InputProps
  extends BaseInputProps,
    Omit<React.InputHTMLAttributes<HTMLInputElement>, "size"> {
  ref?: React.Ref<HTMLInputElement>;
}

export interface TextareaProps
  extends BaseInputProps,
    Omit<React.TextareaHTMLAttributes<HTMLTextAreaElement>, "size"> {
  ref?: React.Ref<HTMLTextAreaElement>;
}

type InputComponent = typeof Input & {
  Textarea: typeof Textarea;
};

function Input({
  variant = "default",
  size = "medium",
  fullWidth = false,
  label,
  helperText,
  required = false,
  leftIcon,
  rightIcon,
  maxLength,
  showCharacterCount = false,
  className,
  disabled,
  value,
  onChange,
  ref,
  ...props
}: InputProps) {
  const [internalValue, setInternalValue] = useState<string>("");
  const currentValue = value !== undefined ? String(value) : internalValue;

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (value === undefined) {
        setInternalValue(e.target.value);
      }
      onChange?.(e);
    },
    [onChange, value],
  );

  const inputClasses = [
    styles.input,
    styles[size],
    variant !== "default" && styles[variant],
    leftIcon && styles.hasLeftIcon,
    rightIcon && styles.hasRightIcon,
    fullWidth && styles.fullWidth,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const labelClasses = [styles.label, required && styles.required]
    .filter(Boolean)
    .join(" ");

  const helperTextClasses = [
    styles.helperText,
    variant !== "default" && styles[variant],
  ]
    .filter(Boolean)
    .join(" ");

  const characterCount = currentValue.length;
  const isNearLimit = maxLength && characterCount >= maxLength * 0.8;
  const isOverLimit = maxLength && characterCount > maxLength;

  const characterCountClasses = [
    styles.characterCount,
    isOverLimit ? styles.overLimit : isNearLimit ? styles.nearLimit : undefined,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={styles.inputWrapper}>
      {label && (
        <label className={labelClasses} htmlFor={props.id}>
          {label}
        </label>
      )}
      <div style={{ position: "relative" }}>
        {leftIcon && <div className={styles.iconLeft}>{leftIcon}</div>}
        <input
          ref={ref}
          className={inputClasses}
          disabled={disabled}
          value={currentValue}
          onChange={handleChange}
          maxLength={maxLength}
          {...props}
        />
        {rightIcon && <div className={styles.iconRight}>{rightIcon}</div>}
      </div>
      {(helperText || (showCharacterCount && maxLength)) && (
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            gap: "0.5rem",
          }}
        >
          {helperText && <div className={helperTextClasses}>{helperText}</div>}
          {showCharacterCount && maxLength && (
            <div className={characterCountClasses}>
              {characterCount}/{maxLength}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Textarea({
  variant = "default",
  size = "medium",
  fullWidth = false,
  label,
  helperText,
  required = false,
  maxLength,
  showCharacterCount = false,
  className,
  disabled,
  value,
  onChange,
  rows = 4,
  ref,
  ...props
}: TextareaProps) {
  const [internalValue, setInternalValue] = useState<string>("");
  const currentValue = value !== undefined ? String(value) : internalValue;

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      if (value === undefined) {
        setInternalValue(e.target.value);
      }
      onChange?.(e);
    },
    [onChange, value],
  );

  const textareaClasses = [
    styles.input,
    styles.textarea,
    styles[size],
    variant !== "default" && styles[variant],
    fullWidth && styles.fullWidth,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const labelClasses = [styles.label, required && styles.required]
    .filter(Boolean)
    .join(" ");

  const helperTextClasses = [
    styles.helperText,
    variant !== "default" && styles[variant],
  ]
    .filter(Boolean)
    .join(" ");

  const characterCount = currentValue.length;
  const isNearLimit = maxLength && characterCount >= maxLength * 0.8;
  const isOverLimit = maxLength && characterCount > maxLength;

  const characterCountClasses = [
    styles.characterCount,
    isOverLimit ? styles.overLimit : isNearLimit ? styles.nearLimit : undefined,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={styles.inputWrapper}>
      {label && (
        <label className={labelClasses} htmlFor={props.id}>
          {label}
        </label>
      )}
      <textarea
        ref={ref}
        className={textareaClasses}
        disabled={disabled}
        value={currentValue}
        onChange={handleChange}
        maxLength={maxLength}
        rows={rows}
        {...props}
      />
      {(helperText || (showCharacterCount && maxLength)) && (
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            gap: "0.5rem",
          }}
        >
          {helperText && <div className={helperTextClasses}>{helperText}</div>}
          {showCharacterCount && maxLength && (
            <div className={characterCountClasses}>
              {characterCount}/{maxLength}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

Input.displayName = "Input";
Textarea.displayName = "Input.Textarea";

(Input as InputComponent).Textarea = Textarea;

export default Input as InputComponent;
