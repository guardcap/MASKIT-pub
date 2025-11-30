import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

/* ---------------------------------- FieldSet ---------------------------------- */
const FieldSet = React.forwardRef<
  HTMLFieldSetElement,
  React.FieldsetHTMLAttributes<HTMLFieldSetElement>
>(({ className, ...props }, ref) => (
  <fieldset
    ref={ref}
    className={cn("space-y-4", className)}
    {...props}
  />
))
FieldSet.displayName = "FieldSet"

/* ---------------------------------- FieldLegend ---------------------------------- */
const fieldLegendVariants = cva(
  "font-semibold tracking-tight",
  {
    variants: {
      variant: {
        legend: "text-lg",
        label: "text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70",
      },
    },
    defaultVariants: {
      variant: "legend",
    },
  }
)

export interface FieldLegendProps
  extends React.HTMLAttributes<HTMLLegendElement>,
    VariantProps<typeof fieldLegendVariants> {}

const FieldLegend = React.forwardRef<HTMLLegendElement, FieldLegendProps>(
  ({ className, variant, ...props }, ref) => (
    <legend
      ref={ref}
      className={cn(fieldLegendVariants({ variant }), className)}
      {...props}
    />
  )
)
FieldLegend.displayName = "FieldLegend"

/* ---------------------------------- FieldGroup ---------------------------------- */
const FieldGroup = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col gap-4", className)}
    {...props}
  />
))
FieldGroup.displayName = "FieldGroup"

/* ---------------------------------- Field ---------------------------------- */
const fieldVariants = cva(
  "group/field space-y-2",
  {
    variants: {
      orientation: {
        vertical: "flex flex-col",
        horizontal: "flex flex-row items-start gap-4",
        responsive: "flex flex-col @[600px]/field-group:flex-row @[600px]/field-group:items-start @[600px]/field-group:gap-4",
      },
    },
    defaultVariants: {
      orientation: "vertical",
    },
  }
)

export interface FieldProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof fieldVariants> {
  "data-invalid"?: boolean
}

const Field = React.forwardRef<HTMLDivElement, FieldProps>(
  ({ className, orientation, ...props }, ref) => (
    <div
      ref={ref}
      role="group"
      className={cn(fieldVariants({ orientation }), className)}
      {...props}
    />
  )
)
Field.displayName = "Field"

/* ---------------------------------- FieldContent ---------------------------------- */
const FieldContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col gap-2 flex-1", className)}
    {...props}
  />
))
FieldContent.displayName = "FieldContent"

/* ---------------------------------- FieldLabel ---------------------------------- */
export interface FieldLabelProps
  extends React.LabelHTMLAttributes<HTMLLabelElement> {
  asChild?: boolean
}

const FieldLabel = React.forwardRef<HTMLLabelElement, FieldLabelProps>(
  ({ className, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "label"
    return (
      <Comp
        ref={ref}
        className={cn(
          "text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 group-data-[invalid]/field:text-destructive",
          className
        )}
        {...props}
      />
    )
  }
)
FieldLabel.displayName = "FieldLabel"

/* ---------------------------------- FieldTitle ---------------------------------- */
const FieldTitle = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "text-sm font-medium leading-none group-data-[invalid]/field:text-destructive",
      className
    )}
    {...props}
  />
))
FieldTitle.displayName = "FieldTitle"

/* ---------------------------------- FieldDescription ---------------------------------- */
const FieldDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn(
      "text-sm text-muted-foreground",
      className
    )}
    {...props}
  />
))
FieldDescription.displayName = "FieldDescription"

/* ---------------------------------- FieldSeparator ---------------------------------- */
const FieldSeparator = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, children, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "relative my-4",
      className
    )}
    {...props}
  >
    <div className="absolute inset-0 flex items-center">
      <span className="w-full border-t" />
    </div>
    {children && (
      <div className="relative flex justify-center text-xs uppercase">
        <span className="bg-background px-2 text-muted-foreground">
          {children}
        </span>
      </div>
    )}
  </div>
))
FieldSeparator.displayName = "FieldSeparator"

/* ---------------------------------- FieldError ---------------------------------- */
export interface FieldErrorProps extends React.HTMLAttributes<HTMLDivElement> {
  errors?: Array<{ message?: string } | undefined>
}

const FieldError = React.forwardRef<HTMLDivElement, FieldErrorProps>(
  ({ className, errors, children, ...props }, ref) => {
    const errorMessages = errors
      ?.filter((error): error is { message: string } => !!error?.message)
      .map((error) => error.message) || []

    const hasErrors = errorMessages.length > 0 || children

    if (!hasErrors) return null

    return (
      <div
        ref={ref}
        className={cn(
          "text-sm font-medium text-destructive",
          className
        )}
        {...props}
      >
        {children}
        {errorMessages.length > 0 && (
          <>
            {errorMessages.length === 1 ? (
              <div>{errorMessages[0]}</div>
            ) : (
              <ul className="list-disc list-inside space-y-1">
                {errorMessages.map((message, index) => (
                  <li key={index}>{message}</li>
                ))}
              </ul>
            )}
          </>
        )}
      </div>
    )
  }
)
FieldError.displayName = "FieldError"

export {
  Field,
  FieldSet,
  FieldLegend,
  FieldGroup,
  FieldContent,
  FieldLabel,
  FieldTitle,
  FieldDescription,
  FieldSeparator,
  FieldError,
}
