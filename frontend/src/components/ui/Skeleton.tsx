import { HTMLAttributes } from "react";

type SkeletonProps = HTMLAttributes<HTMLDivElement>;

export function Skeleton({ className, ...props }: SkeletonProps) {
  const classes = [
    "animate-pulse rounded-lg bg-gradient-to-r from-white/6 via-white/14 to-white/6",
    className
  ]
    .filter(Boolean)
    .join(" ");

  return <div className={classes} {...props} />;
}
